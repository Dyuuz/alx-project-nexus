from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from cart.serializers import cart
from cart.services.cart import CartService
from core.permissions import IsCustomer
from cart.models import Cart
from cart.serializers.cart import CartSerializer

from rest_framework.decorators import action

class CartViewSet(ModelViewSet):
    """
    ViewSet for managing the authenticated customer's cart.

    Ensures that each customer always has an active cart available
    and restricts access to customer-only users.
    """
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsCustomer]
    http_method_names = ["get"]
    
    # action-specific messages
    action_messages = {
        "history": "Cart history retrieved successfully.",
    }
    
    def list(self, request):
        """
        List the current user's active cart.

        Automatically creates an unpaid cart if one does not already exist,
        guaranteeing that the client always receives a valid cart response.
        """
        cart_instance = CartService.get_or_create_cart(request.user)
        serializer = cart.CartSerializer(cart_instance)
        
        return Response(
            {
                "status": "success",
                "code": "FETCH_SUCCESSFUL",
                "message": "Cart retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        """
        
        """
        carts = (
            Cart.objects
            .filter(
                customer=request.user,
            )
            .prefetch_related("items__product")
            .order_by("-updated_at")
        )
        
        page = self.paginate_queryset(carts)
        if page is not None:
            serializer = CartSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CartSerializer(carts, many=True)

        return Response(
            {
                "status": "success",
                "code": "FETCH_SUCCESSFUL",
                "message": "Cart history retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
