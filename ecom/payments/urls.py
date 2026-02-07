from rest_framework.routers import DefaultRouter
from payments.views.payment import PaymentViewSet

router = DefaultRouter()
router.register("payments", PaymentViewSet, basename="payments")

urlpatterns = router.urls