from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from cart.serializers import cart
from cart.services.cart import CartService
from cart.permissions import IsCustomer


class CartViewSet(ViewSet):
    """
    ViewSet for managing the authenticated customer's cart.

    Ensures that each customer always has an active cart available
    and restricts access to customer-only users.
    """
    permission_classes = [IsAuthenticated, IsCustomer]
    http_method_names = ["get"]

    def retrieve(self, request, pk=None):
        """
        Retrieve the current user's active cart.

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