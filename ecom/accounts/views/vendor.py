from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status

from accounts.models import Vendor
from accounts.serializers.vendor import (
    VendorSerializer, VendorUpdateSerializer,
    VendorReadSerializer,
)
from accounts.services.vendor_service import (
    create_vendor,
    update_vendor,
    delete_vendor,
)
from accounts.permissions import IsOwner, IsAdminOrSelf, IsAdmin


class VendorViewSet(ModelViewSet):
    serializer_class = VendorSerializer
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Vendor.objects.all()
        return Vendor.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return VendorSerializer
        if self.action in ["update", "partial_update"]:
            return VendorUpdateSerializer
        return VendorReadSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]

        if self.action in ["retrieve", "update", "partial_update"]:
            return [IsAuthenticated(), IsAdminOrSelf()]

        if self.action == "list":
            return [IsAuthenticated()]

        if self.action == "destroy":
            return [IsAuthenticated(), IsAdmin()]

        return [IsAuthenticated()]
    
    def list(self, request, *args, **kwargs):
        bank_account = self.get_queryset().first()

        if not bank_account:
            return Response(
                {
                    "status": "success",
                    "code": "NO_DATA_FETCHED",
                    "message": "No existing bank account.",
                    "data": None
                },
                status=status.HTTP_200_OK
            )

        serializer = self.get_serializer(bank_account)

        return Response(
            {
                "status": "success",
                "code": "FETCH_SUCCESSFUL",
                "message": "Bank account retrieved successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            vendor_exists = Vendor.objects.filter(user=self.request.user).exists()
            if vendor_exists:
                raise ValidationError("You're not allowed to create multiple vendors.")

            vendor = create_vendor(self.request.user, serializer.validated_data)
            return Response(
                {
                    "status": "success",
                    "code": "CREATE_SUCCESSFUL",
                    "message": "Bank account created successfully.",
                    "data": VendorReadSerializer(vendor).data,
                },
                status=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            return Response(
                {
                    "status": "error",
                    "code": "VALIDATION_ERROR",
                    "message": e.detail[0] if isinstance(e.detail, list) else str(e.detail),
                },
                status=status.HTTP_400_BAD_REQUEST
            )


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        vendor = update_vendor(self.get_object(), serializer.validated_data)
        read_serializer = VendorReadSerializer(vendor)
        
        return Response(
            {
                "status": "success",
                "code": "UPDATE_SUCCESSFUL",
                "message": "Bank account updated successfully.",
                "data": read_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def perform_destroy(self, instance):
        delete_vendor(instance)
        
        return Response(
            {
                "status": "success",
                "code": "DELETE_SUCCESSFUL",
                "message": "Vendor deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )