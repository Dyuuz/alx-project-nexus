from rest_framework.permissions import BasePermission

class IsCustomer(BasePermission):
    """
    Allows access only to authenticated users with a customer role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "customer")


class IsOrderOwnerOrAdmin(BasePermission):
    """
    Allows access to order owners or admin users.

    Admins have full access, while non-admin users can only
    access orders they own.
    """
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "is_staff", False):
            return True
        return obj.customer == request.user
