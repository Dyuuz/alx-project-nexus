from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status

from accounts.models import BankAccount
from accounts.models import Vendor
from accounts.serializers.bank import (
    BankAccountCreateSerializer, BankAccountUpdateSerializer,
    BankAccountReadSerializer,
)
from accounts.services.bank_service import (
    create_bank_account,
    update_bank_account,
    delete_bank_account,
)
from accounts.permissions import (
    IsBankAccountOwner, IsAdmin
)

class BankAccountViewSet(ModelViewSet):
    """
    Bank account CRUD operations.

    Rules:
    - Each vendor can have only one bank account
    - Vendors can only access their own bank account
    - Admins can access and delete any bank account
    """
    queryset = BankAccount.objects.all()
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        """
        Restrict bank account access:
        - Admins see all bank accounts
        - Vendors see only their own
        """
        user = self.request.user

        if user.is_staff:
            return BankAccount.objects.all()

        try:
            vendor = user.vendor_profile
        except Vendor.DoesNotExist:
            return BankAccount.objects.none()

        return BankAccount.objects.filter(vendor=vendor)


    def get_serializer_class(self):
        """
        Return serializer based on action.
        """
        if self.action == "create":
            return BankAccountCreateSerializer
        if self.action in ["update", "partial_update"]:
            return BankAccountUpdateSerializer
        return BankAccountReadSerializer

    def get_permissions(self):
        """
        Assign permissions per action.
        """
        if self.action == "create":
            return [IsAuthenticated()]

        if self.action in ["retrieve", "update", "partial_update"]:
            return [IsAuthenticated(), IsBankAccountOwner()]

        if self.action == "list":
            return [IsAuthenticated()]

        if self.action == "destroy":
            return [IsAuthenticated(), IsAdmin()]

        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        """
        Retrieve the vendor's bank account.

        NOTE:
        This endpoint intentionally returns a single bank account
        instead of a list because each vendor can only have one.
        """
        bank_account = self.get_queryset().first()

        if not bank_account:
            return Response(
                {
                    "status": "success",
                    "code": "NO_DATA_FETCHED",
                    "message": "No existing bank account.",
                    "data": None,
                },
                status=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(bank_account)

        return Response(
            {
                "status": "success",
                "code": "FETCH_SUCCESSFUL",
                "message": "Bank account retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        """
        Create a bank account for the authenticated vendor.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vendor = request.user.vendor_profile
        bank_account = create_bank_account(
            vendor=vendor,
            data=serializer.validated_data
        )

        read_serializer = BankAccountReadSerializer(bank_account)

        return Response(
            {
                "status": "success",
                "code": "CREATE_SUCCESSFUL",
                "message": "Bank account created successfully.",
                "data": read_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """
        Update the authenticated vendor's bank account.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        bank_account = update_bank_account(
            bank_account=instance,
            data=serializer.validated_data,
        )

        read_serializer = BankAccountReadSerializer(bank_account)

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
        Delete a bank account.

        Only admins are allowed to perform this action.
        """
        instance = self.get_object()
        delete_bank_account(instance)

        return Response(
            {
                "status": "success",
                "code": "DELETE_SUCCESSFUL",
                "message": "Bank account deleted successfully.",
            },
            status=status.HTTP_204_NO_CONTENT,
        )