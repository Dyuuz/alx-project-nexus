from rest_framework.permissions import BasePermission

class IsPaymentOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "is_staff", False):
            return True
        return obj.order.customer == request.user
