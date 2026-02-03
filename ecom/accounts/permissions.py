from rest_framework.permissions import BasePermission
from rest_framework import permissions

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"
    
class IsAdminOrSelf(BasePermission):
    """
    Permission:
    - Staff can do anything
    - Users can edit their own user profile (obj is CustomUser)
    - Users can edit their own related objects (Vendor, Bank, etc.)
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True

        # User editing their own profile
        if isinstance(obj, request.user.__class__) and obj.pk == request.user.pk:
            return True

        # User editing their own related objects
        if hasattr(obj, "user") and obj.user == request.user:
            return True
        if hasattr(obj, "vendor") and obj.vendor == request.user:
            return True

        return False
    
class IsBankAccountOwner(permissions.BasePermission):
    """
    Only the vendor who owns the bank account can access it.
    Admins bypass this check.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        # Compare Vendor instance, not User
        try:
            return obj.vendor == request.user.vendor_profile
        except Vendor.DoesNotExist:
            return False


class IsAdminOrSelf_vendor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user

class IsBankAccountOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.vendor.user == request.user

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'user', None) == request.user or getattr(obj, 'vendor', None) == request.user
    
class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "vendor"