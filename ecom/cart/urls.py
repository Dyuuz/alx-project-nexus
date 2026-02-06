from django.urls import path
from cart.views.cart import CartViewSet
from cart.views.cartItem import CartItemViewSet
from cart.views.checkout import CheckoutViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("cart", CartViewSet, basename="cart")
router.register("cart-items", CartItemViewSet, basename="cart-items")
router.register("checkout", CheckoutViewSet, basename="checkout")

urlpatterns = router.urls
