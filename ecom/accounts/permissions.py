from rest_framework.permissions import BasePermission
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions
from accounts.models import Vendor

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff == True
    
class IsAdminOrSelf(BasePermission):
    """
    Permission:
    - Staff can do anything
    - Users can edit their own user profile
    - Users can edit objects that belong to them
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin override
        if request.user.is_staff:
            return True

        # User editing their own user object
        if obj == request.user:
            return True

        # Object directly linked to user
        if hasattr(obj, "user") and obj.user == request.user:
            return True

        # Object linked through vendor
        if hasattr(obj, "vendor") and obj.vendor.user == request.user:
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

        try:
            return obj.vendor == request.user.vendor_profile
        
        except ObjectDoesNotExist:
            return False