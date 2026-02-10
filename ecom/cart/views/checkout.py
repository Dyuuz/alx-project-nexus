from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from django.shortcuts import get_object_or_404

from cart.services.cartItem import CartItemService
from cart.services.cart import CartService
from cart.models import Checkout, Cart
from cart.serializers.checkout import (
    CheckoutSerializer, ConfirmCheckoutSerializer,
    CheckoutHistorySerializer
)
from cart.services.checkout import CheckoutService
from core.permissions import IsCustomer


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
    
    # action-specific messages
    action_messages = {
        "history": "Checkout history retrieved successfully.",
    }

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
        try:
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
        
        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_CREDENTIALS",
                    
                    "detail": f"{e}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["get"], url_path="history", permission_classes=[IsCustomer])
    def history(self, request):
        """
        Returns the authenticated customer's checkout history.
        """
        checkouts = (
            Checkout.objects
            .filter(cart__customer=request.user)
            .select_related("cart")
            .prefetch_related("cart__items__product")
            .order_by("-created_at")
        )
        
        page = self.paginate_queryset(checkouts)
        if page is not None:
            serializer = CheckoutHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CheckoutHistorySerializer(checkouts, many=True)

        return Response(
            {
                "status": "success",
                "code": "FETCH_SUCCESSFUL",
                "message": "Checkout history retrieved successfully.",
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
        serializer = ConfirmCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = get_object_or_404(
            Cart,
            pk=serializer.validated_data["cart_id"],
            customer=request.user,
        )

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
                "message": "Checkout updated successfully.",
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
        serializer = ConfirmCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = get_object_or_404(
            Cart,
            pk=serializer.validated_data["cart_id"],
            customer=request.user,
        )   
        
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
