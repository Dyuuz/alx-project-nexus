from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from rest_framework.response import Response

from products.models import Category
from products.serializers.category import CategorySerializer
from products.services.category import (
    create_category,
    update_category,
    delete_category,
)
from core.permissions import IsAdmin


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post", "patch", "delete"]
    
    # default list message
    list_message = "Categories retrieved successfully."

    def get_queryset(self):
        # Publicly readable categories
        return Category.objects.all()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdmin()]

        return [AllowAny()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = create_category(serializer.validated_data)

        read_serializer = CategorySerializer(category)

        return Response(
            {
                "status": "success",
                "code": "CATEGORY_CREATED",
                "message": "Category created successfully.",
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

        category = update_category(instance, serializer.validated_data)

        read_serializer = CategorySerializer(category)

        return Response(
            {
                "status": "success",
                "code": "UPDATE_SUCCESSFUL",
                "message": "Category updated successfully.",
                "data": read_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_category(instance)

        return Response(
            {
                "status": "success",
                "code": "DELETE_SUCCESSFUL",
                "message": "Category deleted successfully.",
            },
            status=status.HTTP_204_NO_CONTENT,
        )
