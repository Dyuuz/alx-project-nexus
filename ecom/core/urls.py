from django.urls import path
from . import views

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(["GET"])
@permission_classes([AllowAny])
def sentry_test(request):
    1 / 0
    return Response({"ok": True})

urlpatterns = [
    path("sentry-test/", sentry_test),
]
