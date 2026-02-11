from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
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
from core.permissions import IsAdminOrSelf, IsAdmin


class VendorViewSet(ModelViewSet):
    """
    Handles vendor account management for the platform.

    This ViewSet allows authenticated users to create and manage a single
    vendor account linked to their profile, while granting administrators
    full access to all vendor records.

    Core responsibilities:
    - Enforce a one-vendor-per-user constraint
    - Apply role-based access control for vendor operations
    - Expose safe CRUD endpoints using action-specific serializers
    - Delegate business logic to the service layer for consistency

    Regular users can only view and update their own vendor account,
    while destructive actions are restricted to administrators.
    """
    serializer_class = VendorSerializer
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post", "patch", "delete"]
    throttle_classes = [ScopedRateThrottle]

    def get_queryset(self):
        """
        Return the appropriate vendor queryset based on the requesting user.

        - Staff users can access all vendor records.
        - Non-staff users are limited to their own vendor account.

        This prevents unauthorized access to other vendors' data.
        """
        if self.request.user.is_staff:
            return Vendor.objects.all()
        return Vendor.objects.filter(user=self.request.user)
    
    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "vendor_create"

        elif self.action in ["update", "partial_update"]:
            self.throttle_scope = "vendor_update"

        elif self.action == "destroy":
            self.throttle_scope = "vendor_delete"

        elif self.action in ["list", "retrieve"]:
            self.throttle_scope = "vendor_read"

        return super().get_throttles()

    def get_serializer_class(self):
        """
        Select the serializer class based on the current action.

        Uses write serializers for creation and updates, and a read-only
        serializer for retrieval operations to ensure data integrity.
        """
        if self.action == "create":
            return VendorSerializer
        if self.action in ["update", "partial_update"]:
            return VendorUpdateSerializer
        return VendorReadSerializer

    def get_permissions(self):
        """
        Assign permissions dynamically according to the action.

        Ensures only authenticated users can create vendors, owners or
        admins can update or retrieve vendor data, and only admins can
        delete vendor records.
        """
        if self.action == "create":
            return [IsAuthenticated()]

        if self.action in ["list", "update", "partial_update"]:
            return [IsAuthenticated(), IsAdminOrSelf()]

        if self.action == "list":
            return [IsAuthenticated()]

        if self.action == "destroy":
            return [IsAuthenticated(), IsAdmin()]

        return [IsAuthenticated()]
    
    def list(self, request, *args, **kwargs):
        """
        Retrieve the vendor account associated with the requesting user.

        Returns a success response with null data if no vendor account
        exists, ensuring a consistent response shape for clients.
        """
        bank_account = self.get_queryset().first()

        if not bank_account:
            return Response(
                {
                    "status": "success",
                    "code": "NO_DATA_FETCHED",
                    "message": "No existing vendor account.",
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
        """
        Create a new vendor account for the authenticated user.

        - Validates incoming data.
        - Prevents users from creating multiple vendor accounts.
        - Delegates creation logic to the service layer.

        Ensures one-to-one relationship between user and vendor.
        """
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
        """
        Update an existing vendor account.

        - Allows partial updates.
        - Restricts access to admins or the vendor owner.
        - Delegates update logic to the service layer.

        Guarantees controlled and atomic updates.
        """
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

    def destroy(self, request, *args, **kwargs):
        """
        Delete a vendor account.

        - Restricted to admin users.
        - Delegates deletion logic to the service layer.

        Allows future extensions such as soft deletes or audit logging.
        """
        instance = self.get_object()
        delete_vendor(instance)
        
        return Response(
            {
                "status": "success",
                "code": "DELETE_SUCCESSFUL",
                "message": "Vendor deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )