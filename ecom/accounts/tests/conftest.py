import pytest
from accounts.models import Vendor

@pytest.fixture
def vendor_user(normal_user):
    """
    Returns a Vendor instance linked to a CustomUser with role='vendor'.
    """
    normal_user.role = 'vendor'
    normal_user.save()
    vendor = Vendor.objects.create(
        user=normal_user,
        business_name="Test Shop",
        business_address="123 Street"
    )
    return vendor
