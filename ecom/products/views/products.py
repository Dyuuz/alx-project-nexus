from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from rest_framework.response import Response

from products.models import Product
from rest_framework.exceptions import PermissionDenied
from products.serializers.products import ProductSerializer
from products.services.products import (
    create_product,
    update_product,
    delete_product,
)
from products.permissions import IsProductOwnerOrAdmin, IsAdmin

class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post", "patch", "delete"]
    
    def get_queryset(self):
        user = self.request.user

        if user.role == "admin":
            return Product.objects.all()

        if user.role == "vendor" and hasattr(user, "vendor_profile"):
            return Product.objects.filter(vendor=user.vendor_profile)
        
        raise PermissionDenied("You do not have permission to view products.")
        # return Product.objects.none()

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]

        if self.action in ["update", "partial_update"]:
            return [IsAuthenticated(), IsProductOwnerOrAdmin()]

        if self.action == "destroy":
            return [IsAuthenticated(), IsAdmin()]

        return [AllowAny()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if request.user.role == "vendor":
            data["vendor"] = request.user.vendor_profile
        else:
            return Response(
                {
                    "status": "error",
                    "code": "PERMISSION_DENIED",
                    "message": "Only vendors can create products.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        product = create_product(**data)

        read_serializer = ProductSerializer(product)

        return Response(
            {
                "status": "success",
                "code": "PRODUCT_CREATED",
                "message": "Product created successfully.",
                "data": read_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
        
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data

        product = update_product(
            instance.id, **data
        )

        read_serializer = ProductSerializer(product)

        return Response(
            {
                "status": "success",
                "code": "UPDATE_SUCCESSFUL",
                "message": "Product updated successfully.",
                "data": read_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_product(instance)

        return Response(
            {
                "status": "success",
                "code": "DELETE_SUCCESSFUL",
                "message": "Product deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )

