from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer

from cart.services.cart import CartService
from orders.models import Order
from orders.serializers.order import OrderReadSerializer, OrderCreateFromCheckoutSerializer
from orders.permissions import IsCustomer, IsOrderOwnerOrAdmin
from orders.services.order import OrderService


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderReadSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "is_staff", False):
            return Order.objects.all().prefetch_related("items")
        return Order.objects.filter(customer=user).prefetch_related("items")

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated(), IsOrderOwnerOrAdmin()]
        if self.action in ["create_from_checkout"]:
            return [IsAuthenticated(), IsCustomer()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create_from_checkout":
            return OrderCreateFromCheckoutSerializer
        return OrderReadSerializer

    @action(detail=False, methods=["post"], url_path="create")
    def create_from_checkout(self, request):
        """
        POST /orders/create/
        Creates an order from the user's confirmed checkout (cart must be pending).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        pending_cart = request.user.carts.filter(status="pending").order_by("-updated_at").first()
        if not pending_cart:
            return Response(
                {"detail": "No confirmed cart found. Confirm checkout first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        print("Pending cart found:", pending_cart)
        
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
