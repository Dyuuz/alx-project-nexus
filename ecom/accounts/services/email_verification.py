from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()
signer = TimestampSigner()

class EmailVerificationService:
    
    @staticmethod
    def generate_email_token(user, *, max_age_hours=24):
        """
        Create an email verification token and send a verification email.

        This function enforces the verification flow but does not handle
        HTTP or persistence beyond sending the email.
        """
        token = signer.sign(user.pk)

        verify_url = (
            f"{settings.DJANGO_API_URL}"
            f"/api/v1/auth/verify-email/{token}/"
        )

        message = (
            "Welcome!\n\n"
            "Please verify your email address with the link below:\n\n"
            f"{verify_url}\n\n"
            f"This link expires in {max_age_hours} hours."
        )

        return message
    
    @staticmethod
    def verify_email_token(token: str, max_age: int = 60 * 60 * 24):
        """
        Verify a signed email verification token and mark the user as verified.

        Returns:
            user (User): The verified user instance

        Raises:
            SignatureExpired: if token is expired
            BadSignature: if token is invalid
            User.DoesNotExist: if user does not exist
        """
        user_id = signer.unsign(token, max_age=max_age)
        user = User.objects.get(pk=user_id)

        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])

        return user
