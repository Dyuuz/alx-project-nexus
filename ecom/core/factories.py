import factory
from django.utils import timezone

from payments.models import Payment
from orders.models import Order


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    status = "paid"
    created_at = factory.LazyFunction(timezone.now)


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    order = factory.SubFactory(OrderFactory)
    status = "paid"
    payment_alert = False
    created_at = factory.LazyFunction(timezone.now)
