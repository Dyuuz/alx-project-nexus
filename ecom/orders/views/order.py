from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from django.shortcuts import get_object_or_404
from rest_framework.throttling import ScopedRateThrottle

from cart.services.cart import CartService
from orders.models import Order
from cart.models import Cart
from orders.serializers.order import (
    OrderReadSerializer, OrderCreateFromCheckoutSerializer,
    CreateOrderSerializer
)
from core.permissions import IsCustomer, IsOrderOwnerOrAdmin
from orders.services.order import OrderService


class OrderViewSet(ModelViewSet):
    """
    Handles order retrieval and creation for customers and admins.

    Allows customers to view their own orders and create new orders
    from a confirmed checkout, while admins can access all orders.
    """
    
    queryset = Order.objects.all()
    serializer_class = OrderReadSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post"]
    throttle_classes = [ScopedRateThrottle]
    
    list_message = "Order history retrieved successfully."

    def get_queryset(self):
        """
        Return orders visible to the requesting user.

        - Admin users can view all orders.
        - Customers can only view their own orders.

        Order items are prefetched for efficient reads.
        """
        user = self.request.user
        if getattr(user, "is_staff", False):
            return Order.objects.all().prefetch_related("items")
        return Order.objects.filter(customer=user).prefetch_related("items")

    def get_permissions(self):
        """
        Apply permissions based on the current action.

        - Listing and retrieval require ownership or admin access.
        - Order creation is restricted to authenticated customers.
        """
        if self.action in ["list"]:
            return [IsAuthenticated(), IsOrderOwnerOrAdmin()]
        if self.action in ["create_from_checkout"]:
            return [IsAuthenticated(), IsCustomer()]
        return [IsAuthenticated()]
    
    def get_throttles(self):
        """ 
        
        """
        if self.action in ["list", "retrieve"]:
            self.throttle_scope = "order_read"

        elif self.action == "create_from_checkout":
            self.throttle_scope = "order_create"

        return super().get_throttles()

    def get_serializer_class(self):
        """
        Select the appropriate serializer for the action.

        Uses a write serializer when creating an order from checkout
        and a read serializer for all other actions.
        """
        if self.action == "create_from_checkout":
            return OrderCreateFromCheckoutSerializer
        return OrderReadSerializer

    @action(detail=False, methods=["post"], url_path="create")
    def create_from_checkout(self, request):
        """
        POST /orders/create/
        
        Create an order from a confirmed checkout.

        Validates the provided cart ID, ensures the cart belongs to
        the authenticated user, and delegates order creation to
        the service layer.
        """
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pending_cart = get_object_or_404(
            Cart,
            pk=serializer.validated_data["cart_id"],
            customer=request.user,
        )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not pending_cart:
            return Response(
                {
                    "status": "error",
                    "code": "CART_NOT_FOUND",
                    "message": "No pending cart found for the provided cart_id."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            order = OrderService.create_order_with_cart_recovery(pending_cart)
            
        except ValidationError as exc:
            return Response(
                {
                    "status": "error",
                    "code": "ORDER_CREATION_FAILED",
                    "message": exc.detail[0].__str__(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        return Response(
            {
                "status": "success",
                "code": "ORDER_CREATED",
                "message": "Order created successfully.",
                "data": OrderReadSerializer(order).data,
            },
            status=status.HTTP_201_CREATED,
        )
