from rest_framework.viewsets import ModelViewSet
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.renderers import JSONRenderer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError

from accounts.serializers.user import (
    UserCreateSerializer, UserUpdateSerializer, UserReadSerializer,
    PasswordConfirmSerializer, PasswordResetRequestSerializer, 
    PasswordChangeVerifySerializer, TokenRefreshSerializer,
    ResponseSerializer,
    ResponseDataSerializer, LoginSerializer
)
from accounts.services.user_service import (
    UserService,
    PasswordResetService
)
from core.permissions import IsAdmin, IsAdminOrSelf, IsEmailVerified
from accounts.services.email_verification import EmailVerificationService
import logging

logger = logging.getLogger(__name__)

signer = TimestampSigner()

User = get_user_model()

class UserViewSet(ModelViewSet):
    """
    Manage user account lifecycle including registration, profile retrieval,
    profile updates with optimistic locking, and administrative deletion.
    """
    
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post", "patch", "delete"]
    throttle_classes = [ScopedRateThrottle]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "register"
        elif self.action in ["update", "partial_update"]:
            self.throttle_scope = "user_update"
        elif self.action in ["list", "retrieve"]:
            self.throttle_scope = "user_read"
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserReadSerializer
    
    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]

        if self.action in ["list", "update", "partial_update"]:
            return [IsAuthenticated(), IsAdminOrSelf()]

        if self.action == "destroy":
            return [IsAuthenticated(), IsAdmin()]

        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        """
        Retrieve the authenticated user's profile information.

        Returns the current user's account details if available.
        If no user record exists, a successful response with null data is returned.
        """
        
        user = self.get_queryset().first()

        if not user:
            return Response(
                {
                    "status": "success",
                    "code": "NO_DATA_FETCHED",
                    "message": "No existing user found.",
                    "data": None
                },
                status=status.HTTP_200_OK
            )

        serializer = self.get_serializer(user)

        return Response(
            {
                "status": "success",
                "code": "FETCH_SUCCESSFUL",
                "message": "User retrieved successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
        
    def create(self, request, *args, **kwargs):
        """
        Register a new user account.

        Validates input data, creates the user via the service layer,
        and returns the newly created user representation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.create_user(serializer.validated_data)

        read_serializer = UserReadSerializer(user)

        return Response(
            {
                "status": "success",
                "code": "REGISTRATION_SUCCESSFUL",
                "message": "Registration successful.",
                "data": read_serializer.data 
            },
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """
        Update the authenticated user's account details.

        Applies partial updates using optimistic locking to prevent
        concurrent modification conflicts and returns the updated user data.
        """
        
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user = UserService.update_user(instance.pk, serializer.validated_data, instance.version)

        read_serializer = UserReadSerializer(user)

        return Response(
            {
                "status": "success",
                "code": "UPDATE_SUCCESSFUL",
                "message": "User updated successfully.",
                "data": read_serializer.data 
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        """
        Delete a user account.

        Allows administrators to permanently remove a user record
        from the system.
        """
        instance = self.get_object()
        UserService.delete_user(instance.pk)
        
        return Response(
            {
                "status": "success",
                "code": "DELETE_SUCCESSFUL",
                "message": "User deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT
        )
        

class PasswordResetViewSet(GenericViewSet):
    """
    Handle in-app password change and external password reset workflows.

    Supports secure code verification, token validation,
    and password update operations.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified]
    renderer_classes = [JSONRenderer]

    def get_serializer_class(self):
        if self.action == "password_change_verify":
            return PasswordChangeVerifySerializer
        
        if self.action == "password_change_confirm":
            return PasswordConfirmSerializer
        
        if self.action == "password_reset_request":
            return PasswordResetRequestSerializer
        
        if self.action == "password_reset_confirm":
            return PasswordConfirmSerializer
    
    def get_throttles(self):
        if self.action == "password_change_request":
            self.throttle_scope = "password_change_request"
            
        elif self.action == "password_change_verify":
            self.throttle_scope = "password_change_verify"
            
        elif self.action == "password_change_confirm":
            self.throttle_scope = "password_change_confirm"
            
        elif self.action == "password_reset_request":
            self.throttle_scope = "password_reset_request"

        elif self.action == "password_reset_confirm":
            self.throttle_scope = "password_reset_confirm"
            
        return super().get_throttles()

    @extend_schema(
        responses={
            200: ResponseSerializer,
            400: ResponseSerializer,
        },
        description="Initiate password reset by sending a reset code to the user's email."
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="password-change/request",
    )
    def password_change_request(self, request):
        """
        Initiate an in-app password change request.

        Sends a verification code to the authenticated user's email
        to confirm identity before allowing password update.
        """
        email = request.user.email
        reset_request = PasswordResetService.password_change_request(email)

        # Same response (no enumeration)
        return Response(
            {
                "status": "success",
                "code": "RESET_REQUEST_ACCEPTED",
                "message": "A password reset link has been sent to your email."
            },
            status=status.HTTP_200_OK,
        )
        
    @extend_schema(
        responses={
            200: ResponseSerializer,
            400: ResponseSerializer,
        },
        description="Verify the password reset code sent to the user's email and return a reset token."
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="password-change/verify",
    )
    def password_change_verify(self, request):
        """
        Verify the submitted password change code.

        Validates the provided verification code before
        allowing password update confirmation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.user.email
        user_id = request.user.pk

        try:
            PasswordResetService.verify_code_password_change(
                user_id, email, serializer.validated_data["code"],
            )

            return Response(
                {
                    "status": "success",
                    "code": "CODE_VERIFIED",
                    "message": "Reset code verified. You can now reset your password.",
                    "data": {}
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            
            return Response(
                {
                    "status": "error",
                    "code" : "VERIFICATION_FAILED",
                    "message": f"Something went wrong. Pls try again later.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
    @extend_schema(
        responses={
            200: ResponseSerializer,
            400: ResponseSerializer,
        },
        description="Confirms the user's password reset by validating the reset token and updating the password."
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="password-change/confirm",
    )
    def password_change_confirm(self, request):
        """
        Confirm and update the authenticated user's password.

        Validates input and securely updates the user's password
        after successful verification.
        """
        serializer = self.get_serializer(
            data=request.data,
            context={"require_token": False}
        )
        serializer.is_valid(raise_exception=True)

        try:
            PasswordResetService.confirm_password_change(
                request.user.pk,
                serializer.validated_data["new_password"],
            )

            return Response(
                {
                    "status": "success",
                    "code": "PASSWORD_RESET_SUCCESSFUL",
                    "message": "Password reset successful."
                },
                status=status.HTTP_200_OK,
            )
        
        except ValidationError as e:
            return Response(
                {
                    "status": "error",
                    "code": "VALIDATION_ERROR",
                    "message": e.detail,
            },
            status=400,
        )

        except Exception as e:        
            return Response(
                {
                    "status": "error",
                    "code" : "VALIDATION_ERROR",
                    "message": "Something went wrong. Pls try again later.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
          
    
    @extend_schema(
        responses={
            200: ResponseSerializer,
            400: ResponseSerializer,
        },
        description="Initiate password reset by sending a reset code to the user's email."
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        url_path="password-reset/request",
    )
    def password_reset_request(self, request):
        """
        Initiate an external password reset request.

        Accepts an email address and sends a reset link if the account exists,
        without exposing user enumeration details.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Service handle existence silently
        PasswordResetService.generate_reset_token_link_request(email)
 
        # Same response (no enumeration)
        return Response(
            {
                "status": "success",
                "code": "RESET_REQUEST_ACCEPTED",
                "message": "If the email exists, a password reset link has been sent."
            },
            status=status.HTTP_200_OK,
        )
            
    
    @extend_schema(
        description="Verify a user's email address using token",
        responses={
            200: ResponseSerializer,
            400: ResponseSerializer,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        url_path=r"password-reset/confirm",
    )
    def password_reset_confirm(self, request):
        """
        Confirm external password reset using a token.

        Validates the reset token and updates the user's password
        if the token is valid and not expired.
        """
        try:
            serializer = self.get_serializer(
                data=request.data,
                context={"require_token": True}
            )
            serializer.is_valid(raise_exception=True)
            reset_token = serializer.validated_data["reset_token"]
            new_password = serializer.validated_data["new_password"]

            PasswordResetService.confirm_password_reset_request(reset_token, new_password)

            return Response(
                {
                    "status": "success",
                    "code": "PASSWORD_RESET_SUCCESSFUL",
                    "message": "Password reset successful."
                },
                status=status.HTTP_200_OK,
            )
        
        except ValidationError as e:
            return Response(
                {
                    "status": "error",
                    "code": "VALIDATION_ERROR",
                    "message": e.detail,
            },
            status=400,
        )

        except SignatureExpired:
            return Response(
                {
                    "status": "error",
                    "code": "TOKEN_EXPIRED",
                    "message": "Password reset link has expired."
                },
                status=400
            )

        except BadSignature:
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_TOKEN",
                    "message": "Invalid verification link"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        except User.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_TOKEN",
                    "message": "User does not exist"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_TOKEN",
                    "message": f"Password reset change failed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
    
class LoginViewSet(GenericViewSet):
    """
    Authenticate user credentials and issue JWT tokens.

    Validates login data and returns access and refresh tokens
    for authenticated sessions.
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(
        responses={200: ResponseDataSerializer},
        description="Authenticate user and return JWT tokens."
    )
    def create(self, request):
        """
        Authenticate user credentials.

        Returns JWT access and refresh tokens along with
        basic user profile data upon successful login.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, email=email, password=password)

        if not user:
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response(
            {
                "status": "success",
                "code": "LOGIN_SUCCESSFUL",
                "message": "Login successful.",
                "data": {
                    "access": str(access),
                    "refresh": str(refresh),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "phone_number": str(user.phone_number) if user.phone_number else None,
                        "email_verified": user.email_verified,
                        "role": getattr(user, "role", ""),
                    }
                }
            },
            status=status.HTTP_200_OK
        )
        

class AuthTokenViewSet(GenericViewSet):
    """
    Handle JWT access token refresh operations.

    Provides endpoint for generating a new access token
    using a valid refresh token.
    """
    
    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer
    renderer_classes = [JSONRenderer]
    throttle_classes = [ScopedRateThrottle]
    
    def get_throttles(self):
        if self.action == "refresh_token":
            self.throttle_scope = "token_refresh"
        return super().get_throttles()

    @extend_schema(
        description="Refresh access token using a valid refresh token.",
        responses={
            200: ResponseDataSerializer,
            400: ResponseSerializer,
            401: ResponseSerializer,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="token/refresh",
    )
    def refresh_token(self, request):
        """
        Refresh an access token.

        Validates the provided refresh token and returns
        a newly generated access token.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]

        if not refresh_token:
            return Response(
                {
                    "status": "error",
                    "code": "REFRESH_TOKEN_REQUIRED",
                    "message": "Refresh token is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return Response(
                {
                    "status": "success",
                    "code": "ACCESS_TOKEN_REFRESHED",
                    "message": "Access token refreshed successfully.",
                    "data": {
                        "access": access_token
                    }
                },
                status=status.HTTP_200_OK,
            )

        except TokenError:
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Invalid or expired refresh token."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


class EmailVerificationViewSet(GenericViewSet):
    """
    Manage email verification workflow.

    Handles verification of signed email tokens
    and resending verification links when required.
    """
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]
    throttle_classes = [ScopedRateThrottle]

    def get_throttles(self):
        if self.action == "verify_email":
            self.throttle_scope = "email_verify"

        elif self.action == "resend_verification":
            self.throttle_scope = "resend_verification"

        return super().get_throttles()

    @extend_schema(
        description="Verify a user's email address using token",
        responses={
            200: ResponseSerializer,
            400: ResponseSerializer,
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"verify-email/(?P<token>[^/]+)",
    )
    def verify_email(self, request, token=None):
        """
        Verify a user's email address.

        Validates the signed verification token and marks
        the user's email as verified if successful.
        """
        try:
            EmailVerificationService.verify_email_token(token)

            return Response(
                {
                    "status": "success",
                    "code": "EMAIL_VERIFIED",
                    "message": "Email verified successfully."
                },
                status=status.HTTP_200_OK,
            )

        except SignatureExpired:
            try:
                # Extract user safely
                user_pk = signer.unsign(token)
                user = User.objects.get(pk=user_pk)

                return Response(
                    {
                        "status": "error",
                        "code": "TOKEN_EXPIRED",
                        "email": user.email,
                        "message": "Verification link expired."
                    },
                    status=400
                )

            except Exception:
                return Response(
                    {
                        "status": "error",
                        "code": "INVALID_TOKEN",
                        "message": "Invalid verification link"
                    },
                    status=400
                )

        except BadSignature:
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_TOKEN",
                    "message": "Invalid verification link"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        except User.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_TOKEN",
                    "message": "User does not exist"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_TOKEN",
                    "message": "Verification failed"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    
    @extend_schema(
        description="Resend email verification link",
        responses={
            200: ResponseSerializer,
            400: ResponseSerializer,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="resend-verification",
    )
    def resend_verification(self, request):
        """
        Resend email verification link.

        Triggers generation and delivery of a new
        verification link to the authenticated user.
        """
        email = request.user.email

        if not email:
            return Response(
                {
                    "status": "error",
                    "code": "MISSING_EMAIL",
                    "message": "Email address is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = EmailVerificationService.resend_verification(email)
        
        if token is True:
            return Response(
                {
                    "status": "success",
                    "code": "VERIFICATION_EMAIL_SENT",
                    "message": "Verification email has been resent."
                },
                status=status.HTTP_200_OK,
            )
            
        if token == "already_verified":
            return Response(
                {
                    "status": "error",
                    "code": "ALREADY_VERIFIED",
                    "message": "Email is already verified."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "status": "error",
                "code": "VERIFICATION_EMAIL_NOT_SENT",
                "message": "Failed to resend verification email."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )