from rest_framework.permissions import BasePermission
from rest_framework import permissions

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff == True

class IsProductOwnerOrAdmin(BasePermission):
    """
    Access rules:
    - Admin users: full access
    - Vendor users: only their own products
    - Others: denied
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Staff: full access
        if request.user.is_staff:
            return True

        # Vendor: must own the product
        if user.role == "vendor":
            if not hasattr(user, "vendor_profile"):
                return False

            return obj.vendor_id == user.vendor_profile.id

        return False

class IsAdmin(BasePermission):
    """
    Allows access only to admin/staff users.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )
