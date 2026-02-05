from django.urls import path
from products.views.products import ProductViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")

urlpatterns = router.urls