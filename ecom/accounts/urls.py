from rest_framework.routers import DefaultRouter
from accounts.views.user import UserViewSet, LoginViewSet, EmailVerificationViewSet
from accounts.views.vendor import VendorViewSet
from accounts.views.bank import BankAccountViewSet

router = DefaultRouter()
router.register("auth", EmailVerificationViewSet, basename="auth")
router.register("auth/users", UserViewSet, basename="user")
router.register("login", LoginViewSet, basename="login")
router.register("vendors", VendorViewSet, basename="vendor")
router.register("bank-accounts", BankAccountViewSet, basename="bank-account")

urlpatterns = router.urls
