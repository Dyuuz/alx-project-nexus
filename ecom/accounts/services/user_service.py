from django.db import transaction
from django.contrib.auth import get_user_model
from accounts.services.email_verification import EmailVerificationService
from core.utils.mail_sender import send_mail_helper
from asgiref.sync import async_to_sync
from django.db.models import F
from django.conf import settings
from django.core.cache import cache
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from rest_framework.exceptions import ValidationError
from django.utils.crypto import get_random_string
import hashlib
import time
from django.core.cache import cache

signer = TimestampSigner()
User = get_user_model()

class UserService:
    """
    Provide transactional user management operations.

    Encapsulates user creation, updates with optimistic locking,
    and deletion logic to keep business rules outside the view layer.
    """
    
    def create_user(data: dict) -> User:
        """
        Create a new user account within an atomic transaction.

        Ensures the password is securely hashed using the model's
        `create_user` method. On successful commit, dispatches
        asynchronous welcome and email verification messages.

        Rolls back the transaction automatically if any step fails.
        """
        
        with transaction.atomic():
            user = User.objects.create_user(**data)

            transaction.on_commit(
                lambda: send_mail_helper.delay(
                    "Welcome",
                    f"Hi {user.first_name}!\nYour registration was successful",
                    user.email,
                )
            )

            transaction.on_commit(
                lambda: send_mail_helper.delay(
                    "Email Verification Link",
                    EmailVerificationService.generate_email_token(user.pk),
                    user.email,
                )
            )

        return user


    @transaction.atomic
    def update_user(user_id, data: dict, current_version: int):
        """
        Update an existing user using optimistic locking.

        Performs a version-checked update to prevent concurrent
        modification conflicts. Increments the version field
        upon successful update.

        Raises an exception if a version mismatch is detected.
        """
        updated = User.objects.filter(
            id=user_id,
            version=current_version
        ).update(
            **data,
            version=F('version') + 1
        )

        if updated == 0:
            raise Exception("Conflict detected.")

        return User.objects.get(id=user_id)


    @transaction.atomic
    def delete_user(user_id) -> None:
        """
        Delete a user account within an atomic transaction.

        Ensures complete removal of the user record,
        guaranteeing rollback if any error occurs.
        """

        user = User.objects.get(pk=user_id)
        user.delete()

        transaction.on_commit(
            lambda: send_mail_helper.delay(
                "User Account Deletion Successful",
                f"Hi {user.first_name}!\nYour account is deleted successfully",
                user.email,
            )
        )


class PasswordResetService:
    """
    Handle secure password change and reset workflows.

    Implements OTP-based in-app password changes,
    signed token-based external resets, cache-backed
    one-time enforcement, and transactional password updates.
    """

    OTP_EXPIRY = 600  # 10 minutes
    RESET_TOKEN_EXPIRY = 900  # 15 minutes

    @staticmethod
    def password_change_request(email: str):
        """
        Initiate in-app password change verification.

        Generates a one-time numeric code and stores it in cache
        with expiration. Sends the OTP to the user's email.
        Fails silently to prevent user enumeration.
        """
        user = User.objects.filter(email=email).first()

        #  Return silently (no email leak)
        if not user:
            return False

        # Generate 6-digit OTP
        otp = get_random_string(length=6, allowed_chars="0123456789")

        # Store hashed OTP in cache
        cache_key = f"pwd-change:{email}"
        cache.set(cache_key, otp, timeout=PasswordResetService.OTP_EXPIRY)

        send_mail_helper.delay(
            "Password Reset Code",
            f"Your password reset code is {otp}",
            user.email,
        )
        return True

    @staticmethod
    def verify_code_password_change(user_id, email: str, code: str):
        """
        Validate submitted password change OTP.

        Compares the provided code with the cached value,
        enforces expiration, and grants temporary reset permission
        upon successful verification.
        """
        cache_key = f"pwd-change:{email}"
        stored_code = cache.get(cache_key)

        if not stored_code or stored_code != code:
            raise ValidationError("Invalid or expired code.")

        # Delete OTP after successful verification
        cache.delete(cache_key)
        
        cache.set(f"pwd-change-allowed:{user_id}", True, timeout=300)

        return True

    @staticmethod
    def confirm_password_change(user_id, new_password: str):
        """
        Finalize authenticated password change.

        Validates reset session permission, prevents password reuse,
        updates the password atomically, and invalidates the reset flag
        after successful completion.
        """
        
        cache_key = f"pwd-change-allowed:{user_id}"
        allowed = cache.get(cache_key)

        if not allowed:
            raise ValidationError({
                "code": "RESET_SESSION_EXPIRED",
                "message": "Reset session has expired."
            })
                    
        with transaction.atomic():
            user = User.objects.get(pk=user_id)
            
            if user.check_password(new_password):
                raise ValidationError({
                    "code": "PASSWORD_REUSE_NOT_ALLOWED",
                    "message": "You cannot reuse your current password."
                })
                
            user.set_password(new_password)
            user.save(update_fields=["password"])
            
            # Delete flag immediately (one-time use)
            cache.delete(cache_key)
            
            transaction.on_commit(
            lambda: send_mail_helper.delay(
                "Password Changed",
                "Your password has been successfully chnaged",
                user.email,
            )
        )

        return user
    
    @staticmethod
    def generate_reset_token_link_request(email: str):
        """
        Finalize authenticated password change.

        Validates reset session permission, prevents password reuse,
        updates the password atomically, and invalidates the reset flag
        after successful completion.
        """
        
        user = User.objects.filter(email=email).first()

        # Silent fail
        if not user:
            time.sleep(0.3)
            return

        reset_token = signer.sign(user.pk)

        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
        cache.set(
            f"pwd-reset-token:{token_hash}",
            user.pk,
            timeout=PasswordResetService.RESET_TOKEN_EXPIRY
        )

        password_reset_url = (
            f"{settings.DJANGO_API_URL}"
            f"/api/v1/auth/password-reset/confirm/?token={reset_token}"
        )

        send_mail_helper.delay(
            "Password Reset Link",
            f"Use the following link to reset your password: {password_reset_url}\nThis link expires in 15 minutes.",
            user.email,
        )

    @staticmethod
    def confirm_password_reset_request(reset_token: str, new_password: str):
        """
        Confirm external password reset using signed token.

        Validates token integrity and expiration, enforces one-time usage
        via cache-backed verification, prevents password reuse, and updates
        the password within an atomic transaction.
        """
        try:
            user_id = signer.unsign(reset_token, max_age=PasswordResetService.RESET_TOKEN_EXPIRY)

        except SignatureExpired:
            raise ValidationError("Reset session expired.")

        except BadSignature:
            raise ValidationError("Invalid reset token.")

        # One-time enforcement
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
        cache_key = f"pwd-reset-token:{token_hash}"

        stored_user_id = cache.get(cache_key)

        if not stored_user_id:
            raise ValidationError("Reset token already used or invalid.")

        if str(stored_user_id) != str(user_id):
            raise ValidationError("Invalid reset token.")

        with transaction.atomic():
            user = User.objects.get(pk=user_id)
            
            if user.check_password(new_password):
                raise ValidationError("You cannot reuse your current password.")
            
            user.set_password(new_password)
            user.save(update_fields=["password"])

            # Delete token immediately (one-time)
            cache.delete(cache_key)

            transaction.on_commit(
                lambda: send_mail_helper.delay(
                    "Password Changed",
                    "Your password has been successfully changed.",
                    user.email,
                )
            )

        return user