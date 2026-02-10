from rest_framework.permissions import BasePermission
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions
from accounts.models import Vendor


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
        

class IsCartOwner(BasePermission):
    """
    Object-level permission that allows access only to the cart owner.

    Ensures that users can interact only with carts they own.
    """

    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user


class IsCustomer(BasePermission):
    """
    Permission that restricts access to authenticated customers only.

    Prevents non-customer roles (e.g., vendors or admins) from
    accessing customer-specific cart and checkout endpoints.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "customer"
        )


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
    

class IsPaymentOwnerOrAdmin(BasePermission):
    """
    Allows access to payment owners or admin users.

    Admins have full access, while customers can only
    access payments linked to their own orders.
    """
    
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "is_staff", False):
            return True
        return obj.order.customer == request.user

    
class IsVendor(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        return (
            user.is_authenticated
            and hasattr(user, "vendor_profile")
        )
        

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