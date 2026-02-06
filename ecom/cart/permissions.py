from rest_framework.permissions import BasePermission


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
