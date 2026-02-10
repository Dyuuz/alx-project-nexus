from celery import shared_task
from cart.services.cart import CartService
from cart.services.checkout import CheckoutService
from payments.services.payment import PaymentService
from accounts.services import vendor_service
from orders.services.order import OrderService
from products.services.products import (
    send_critical_stock_alerts,
    reconcile_inventory_and_notify
)

@shared_task(bind=True, max_retries=3)
def cleanup_abandoned_carts_task(self):
    CartService.cleanup_abandoned_carts(self)
    
@shared_task(bind=True, max_retries=3)
def expire_pending_checkouts_task(self):
    CheckoutService.expire_pending_checkouts(self)
    
@shared_task(bind=True, max_retries=3)
def cancel_unpaid_orders_task(self):
    OrderService.cancel_unpaid_orders(self)
    
@shared_task(bind=True, max_retries=3)
def send_payment_alerts_task(self):
    PaymentService.send_payment_alerts(self)
    
@shared_task(bind=True, max_retries=3)
def send_payment_reminder_24h_task(self):
    PaymentService.send_payment_reminder_24h(self)
    
@shared_task(bind=True, max_retries=3)
def send_final_payment_reminder_task(self):
    PaymentService.send_final_payment_reminder(self)

@shared_task(bind=True, max_retries=3)
def send_vendor_low_stock_alerts_task(self, product_ids):
    vendor_service.send_vendor_low_stock_alerts()
    
@shared_task(bind=True, max_retries=3)
def send_critical_stock_alerts_task(self, product_ids):
    send_critical_stock_alerts()
    
@shared_task(bind=True, max_retries=3)
def reconcile_inventory_and_notify_task(self, product_ids):
    reconcile_inventory_and_notify()