# checkout/admin.py

from django import forms
from django.core.exceptions import ValidationError
from cart.models import Checkout
from cart.services.checkout import CheckoutService
from rest_framework.exceptions import ValidationError as DRFValidationError


class CheckoutAdminForm(forms.ModelForm):
    class Meta:
        model = Checkout
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        cart = self.instance.cart

        try:
            # Call your service-level guard
            CheckoutService.confirm_checkout(cart)
        except DRFValidationError as e:
            # Convert DRF ValidationError to Django ValidationError
            raise ValidationError(e.detail)

        return cleaned_data
