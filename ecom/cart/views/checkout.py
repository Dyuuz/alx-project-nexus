from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer

from cart.services.cartItem import CartItemService
from cart.services.cart import CartService
from cart.models import Checkout
from cart.serializers.checkout import CheckoutSerializer
from cart.services.checkout import CheckoutService
from cart.permissions import IsCustomer


class CheckoutViewSet(ModelViewSet):
    """
    Checkout ViewSet
    
    ViewSet responsible for managing the checkout lifecycle.

    Checkout is implicit and singular per customer and is always
    associated with the customer's active cart. This ViewSet exposes
    endpoints for retrieving a checkout draft, updating it, and
    confirming the checkout to lock the cart for order creation.

    - Checkout is implicit and singular per customer
    - list() returns the user's checkout draft
    - update()/partial_update() updates the checkout draft
    - confirm() locks the cart for order creation
    """

    queryset = Checkout.objects.all()
    serializer_class = CheckoutSerializer
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "patch", "post"]


    def get_queryset(self):
        """
        Return checkouts scoped to the requesting user.

        Staff users may access all checkouts, while customers are
        limited to the checkout associated with their active cart.
        """
        user = self.request.user

        if user.is_staff:
            return Checkout.objects.all()

        cart = CartService.get_or_create_cart(user)
        return Checkout.objects.filter(cart=cart)


    def get_permissions(self):
        """
        Apply customer-only permissions to checkout interactions.
        """
        if self.action in ["list", "update", "partial_update", "confirm"]:
            return [IsAuthenticated(), IsCustomer()]

        return [IsAuthenticated()]


    def list(self, request, *args, **kwargs):
        """
        Retrieve or create the current user's checkout draft.

        Guarantees that a checkout draft exists for the active cart.
        """
        cart = CartService.get_or_create_cart(request.user)
        checkout = CheckoutService.get_or_create_draft(cart)

        serializer = self.get_serializer(checkout)

        return Response(
            {
                "status": "success",
                "code": "FETCH_SUCCESSFUL",
                "message": "Checkout retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


    @action(detail=False, methods=["patch"], url_path="update")
    def update_draft(self, request):
        """
        Update the checkout draft for the active cart.

        Validates that the cart is eligible for checkout updates
        before applying any changes.
        """
        cart = CartService.get_or_create_cart(request.user)

        serializer = CheckoutSerializer(
            data=request.data,
            context={"cart": cart},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        checkout = CheckoutService.update_checkout(
            cart, serializer.validated_data
        )

        return Response(
            {
                "status": "success",
                "code": "UPDATE_SUCCESSFUL",
                "data": CheckoutSerializer(checkout).data,
            },
            status=status.HTTP_200_OK,
        )
        

    @action(detail=False, methods=["post"], url_path="confirm")
    def confirm(self, request):
        """
        Confirm the checkout and lock the associated cart.

        Once confirmed, the cart can no longer be modified and is
        ready for order creation.
        """
        cart = CartService.get_or_create_cart(request.user)
        checkout = CheckoutService.confirm_checkout(cart)

        return Response(
            {
                "status": "success",
                "code": "CHECKOUT_CONFIRMED",
                "message": "Checkout confirmed successfully.",
                "data": CheckoutSerializer(checkout).data,
            },
            status=status.HTTP_200_OK,
        )
