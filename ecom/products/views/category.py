from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status

from products.models import Category, Product
# from products.serializers.bank import (
    
# )
# from products.services.bank_service import (
    
# )
# from products.permissions import (

# )

