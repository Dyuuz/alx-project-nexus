from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status

from cart.models import CartItem
from cart.serializers import cart, cartItem
from cart.services.cartItem import CartItemService
from cart.services.cart import CartService
from core.permissions import IsCustomer


class CartItemViewSet(ModelViewSet):
    """
    ViewSet for managing items within a customer's cart.

    Delegates all business rules to the CartService layer and exposes
    only controlled operations for adding, updating, and removing
    cart items.
    
    - create(): add product to cart
    - partial_update(): update quantity
    - destroy(): remove item from cart
    """

    queryset = CartItem.objects.all()
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticated, IsCustomer]
    http_method_names = ["get", "post", "patch", "delete"]


    def get_serializer_class(self):
        """
        Return the appropriate serializer based on the current action.
        """
        if self.action == "create":
            return cartItem.CartItemSerializer
        if self.action in ["update", "partial_update"]:
            return cartItem.CartItemUpdateSerializer
        return cartItem.CartItemSerializer


    def get_queryset(self):
        """
        Restrict cart items to the authenticated user's active cart.
        """
        cart = CartService.get_or_create_cart(self.request.user)
        return CartItem.objects.filter(cart=cart)
    
    
    def list(self, request, *args, **kwargs):
        """
        Return all items in the authenticated user's active cart.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "status": "success",
                "code": "FETCH_SUCCESSFUL",
                "message": "Active Cart items retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
        

    def create(self, request, *args, **kwargs):
        """
        Add a product to the authenticated user's cart.
        """
        cart = CartService.get_or_create_cart(request.user)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart_item, append = CartItemService.add_item(
            cart=cart,
            product_id=serializer.validated_data["product_id"],
            quantity=serializer.validated_data["item_quantity"],
        )

        if append:
            return Response(
                {
                    "status": "success",
                    "code": "UPDATED_SUCCESSFUL",
                    "message": "Cart Item quantity updated successfully.",
                    "data" : cartItem.CartItemSerializer(cart_item).data
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "status": "success",
                "code": "CREATE_SUCCESSFUL",
                "message": "Cart Item created successfully.",
                "data" : cartItem.CartItemSerializer(cart_item).data
            },
            status=status.HTTP_201_CREATED,
        )
        

    def partial_update(self, request, *args, **kwargs):
        """
        Update the quantity of a cart item.

        If the quantity is zero or less, the item is removed.
        """
        cart = CartService.get_or_create_cart(request.user)
        cart_item_id = kwargs.get("pk")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data["item_quantity"]

        cart_item = CartItemService.update_item(cart, cart_item_id, quantity)

        if cart_item is None:
            return Response(
                {
                    "status": "success",
                    "code": "DELETE_SUCCESSFUL",
                    "message": "Cart Item deleted successfully due to zero or negative quantity.",
                },
                status=status.HTTP_204_NO_CONTENT,
            )
        
        return Response(
            {
                "status": "success",
                "code": "UPDATE_SUCCESSFUL",
                "message": "Cart Item updated successfully.",
                "data" : cartItem.CartItemSerializer(cart_item).data
            },
            status=status.HTTP_200_OK,
        )


    def destroy(self, request, *args, **kwargs):
        """
        Remove a cart item from the authenticated user's cart.
        """
        cart = CartService.get_or_create_cart(request.user)
        cart_item_id = kwargs.get("pk")

        CartItemService.remove_item(cart, cart_item_id)
        
        return Response(
            {
                "status": "success",
                "code": "DELETE_SUCCESSFUL",
                "message": "Cart Item deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )

