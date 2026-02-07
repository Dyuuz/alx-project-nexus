from rest_framework.permissions import BasePermission

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "customer")


class IsOrderOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "is_staff", False):
            return True
        return obj.customer == request.user
