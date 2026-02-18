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
from core.utils.mail_sender import send_mail_helper
from rest_framework.throttling import ScopedRateThrottle

from accounts.serializers.login import LoginSerializer, LoginResponseSerializer
from accounts.serializers.user import (
    UserCreateSerializer,
    UserUpdateSerializer,
    UserReadSerializer,
)
from accounts.services.user_service import (
    create_user,
    update_user,
    delete_user,
)
from core.permissions import IsAdmin, IsAdminOrSelf
from accounts.services.email_verification import EmailVerificationService
from accounts.serializers.email_verification import EmailVerif_ResponseSerializer
import logging

logger = logging.getLogger(__name__)

signer = TimestampSigner()

User = get_user_model()

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
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

        if self.action == "list":
            return [IsAuthenticated()]

        if self.action == "destroy":
            return [IsAuthenticated(), IsAdmin()]

        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = create_user(serializer.validated_data)
        
        token_message = EmailVerificationService.generate_email_token(user)
        subject = "Email Verification Link"
        send_mail_helper.delay(subject, token_message, user.email)

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
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = update_user(instance, serializer.validated_data)

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
        instance = self.get_object()
        delete_user(instance)
        return Response(
            {
                "status": "success",
                "code": "DELETE_SUCCESSFUL",
                "message": "User deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT
        )


class LoginViewSet(GenericViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(
        responses={200: LoginResponseSerializer},
        description="Authenticate user and return JWT tokens."
    )
    def create(self, request):
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
                        "role": getattr(user, "role", ""),
                    }
                }
            },
            status=status.HTTP_200_OK
        )


class EmailVerificationViewSet(GenericViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email_verify"

    @extend_schema(
        description="Verify a user's email address using token",
        responses={
            200: EmailVerif_ResponseSerializer,
            400: EmailVerif_ResponseSerializer,
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"verify-email/(?P<token>[^/]+)",
    )
    def verify_email(self, request, token=None):
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
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_TOKEN",
                    "message": "Verification link has expired."
                },
                status=status.HTTP_400_BAD_REQUEST,
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

        except Exception:
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_TOKEN",
                    "message": "Verification failed"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
