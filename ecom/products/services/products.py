from django.db import transaction
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()
