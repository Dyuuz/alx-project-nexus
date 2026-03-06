from django.db import transaction
from accounts.models import BankAccount
from core.utils.mail_sender import send_mail_helper
from rest_framework.exceptions import ValidationError
from core.exceptions import ConflictException
from django.db.models import F
from django.conf import settings
import requests
import re
import logging

logger = logging.getLogger(__name__)
PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY

@transaction.atomic
def create_bank_account(vendor, data):
    """
    Create a new BankAccount instance for a given vendor.

    This function ensures that the creation is atomic—either it fully succeeds
    or rolls back in case of an error.

    Args:
        vendor (User): The vendor (user) who owns the bank account.
        data (dict): Dictionary of bank account fields, e.g.,
                     number, name, bank_name.

    Returns:
        BankAccount: The newly created BankAccount instance.
    """
    bank_account = BankAccount.objects.create(
        vendor=vendor,
        **data
    )
    
    transaction.on_commit(
        lambda: send_mail_helper.delay(
            "Bank Account Creation Successful",
            f"Hi {vendor.user.first_name}!\nYour bank account has been created successfully.",
            vendor.user.email,
        )
    )

    return bank_account


@transaction.atomic
def update_bank_account(bank_account_id,  data: dict, current_version: int):
    """
    Update an existing BankAccount instance with new data.

    The update is performed atomically to ensure data consistency.

    Args:
        bank_account (BankAccount): The BankAccount instance to update.
        data (dict): Dictionary of fields to update.

    Returns:
        BankAccount: The updated BankAccount instance.
    """
    updated = BankAccount.objects.filter(
        id=bank_account_id,
        version=current_version
    ).update(
        **data,
        version=F('version') + 1
    )

    if updated == 0:
        raise ConflictException()

    updated_instance = BankAccount.objects.get(id=bank_account_id)

    transaction.on_commit(
        lambda: send_mail_helper.delay(
            "Bank Account Update Successful",
            f"Hi {updated_instance.vendor.user.first_name}!\nYour bank account has been updated successfully.",
            updated_instance.vendor.user.email,
        )
    )

    return BankAccount.objects.get(id=bank_account_id)


@transaction.atomic
def delete_bank_account(bank_account_id):
    """
    Delete an existing BankAccount instance.

    This operation is atomic and ensures that deletion fully completes
    or rolls back in case of failure.

    Args:
        bank_account (BankAccount): The BankAccount instance to delete.

    Returns:
        None
    """
    bank_account = BankAccount.objects.get(pk=bank_account_id)
    first_name = bank_account.vendor.user.first_name
    email = bank_account.vendor.user.email
    bank_account.delete()
    
    transaction.on_commit(
        lambda: send_mail_helper.delay(
            "Bank Account Deletion Successful",
            f"Hi {first_name}!\nYour account is deleted successfully",
            email,
        )
    )


BANK_ALIASES = {
    # GTBank
    "gtbank": "Guaranty Trust Bank",
    "gt bank": "Guaranty Trust Bank",
    "gtb": "Guaranty Trust Bank",
    "guaranty trust": "Guaranty Trust Bank",

    # Access Bank
    "access": "Access Bank",
    "access bank": "Access Bank",
    "access diamond": "Access Bank",

    # Zenith Bank
    "zenith": "Zenith Bank",
    "zenith bank": "Zenith Bank",

    # First Bank
    "first bank": "First Bank of Nigeria",
    "firstbank": "First Bank of Nigeria",
    "fbn": "First Bank of Nigeria",

    # UBA
    "uba": "United Bank for Africa",
    "united bank": "United Bank for Africa",
    "united bank for africa": "United Bank for Africa",

    # Union Bank
    "union": "Union Bank of Nigeria",
    "union bank": "Union Bank of Nigeria",

    # FCMB
    "fcmb": "First City Monument Bank",
    "first city": "First City Monument Bank",
    "first city monument": "First City Monument Bank",

    # Stanbic IBTC
    "stanbic": "Stanbic IBTC Bank",
    "stanbic ibtc": "Stanbic IBTC Bank",
    "ibtc": "Stanbic IBTC Bank",

    # Sterling Bank
    "sterling": "Sterling Bank",
    "sterling bank": "Sterling Bank",

    # Wema Bank
    "wema": "Wema Bank",
    "wema bank": "Wema Bank",
    "alat": "Wema Bank",

    # Polaris Bank
    "polaris": "Polaris Bank",
    "polaris bank": "Polaris Bank",
    "skye bank": "Polaris Bank",

    # Fidelity Bank
    "fidelity": "Fidelity Bank",
    "fidelity bank": "Fidelity Bank",

    # Keystone Bank
    "keystone": "Keystone Bank",
    "keystone bank": "Keystone Bank",

    # Ecobank
    "ecobank": "Ecobank Nigeria",
    "eco bank": "Ecobank Nigeria",

    # Jaiz Bank
    "jaiz": "Jaiz Bank",
    "jaiz bank": "Jaiz Bank",

    # Heritage Bank
    "heritage": "Heritage Bank",
    "heritage bank": "Heritage Bank",

    # Unity Bank
    "unity": "Unity Bank",
    "unity bank": "Unity Bank",

    # Titan Trust Bank
    "titan": "Titan Trust Bank",
    "titan trust": "Titan Trust Bank",
    "titan trust bank": "Titan Trust Bank",

    # Providus Bank
    "providus": "Providus Bank",
    "providus bank": "Providus Bank",

    # Standard Chartered
    "standard chartered": "Standard Chartered Bank Nigeria",
    "stanchart": "Standard Chartered Bank Nigeria",

    # Citibank
    "citi": "Citibank Nigeria",
    "citibank": "Citibank Nigeria",

    # Globus Bank
    "globus": "Globus Bank",
    "globus bank": "Globus Bank",

    # SunTrust Bank
    "suntrust": "SunTrust Bank",
    "sun trust": "SunTrust Bank",

    # Coronation Bank
    "coronation": "Coronation Bank",
    "coronation merchant": "Coronation Bank",

    # Parallex Bank
    "parallex": "Parallex Bank",
    "parallex bank": "Parallex Bank",

    # Signature Bank
    "signature": "Signature Bank",
    "signature bank": "Signature Bank",

    # Lotus Bank
    "lotus": "Lotus Bank",
    "lotus bank": "Lotus Bank",

    # Premium Trust Bank
    "premium trust": "Premium Trust Bank",
    "premiumtrust": "Premium Trust Bank",

    # LAPO Microfinance
    "lapo": "LAPO Microfinance Bank",
    "lapo mfb": "LAPO Microfinance Bank",

    # Fintechs / Neobanks
    "kuda": "Kuda Bank",
    "kuda bank": "Kuda Bank",

    "opay": "OPay",
    "o pay": "OPay",

    "palmpay": "PalmPay",
    "palm pay": "PalmPay",

    "moniepoint": "Moniepoint MFB",
    "monie point": "Moniepoint MFB",
    "teamapt": "Moniepoint MFB",

    "fairmoney": "FairMoney Microfinance Bank",
    "fair money": "FairMoney Microfinance Bank",

    "carbon": "Carbon",
    "one finance": "Carbon",

    "rubies": "Rubies MFB",
    "rubies bank": "Rubies MFB",

    "sparkle": "Sparkle Microfinance Bank",
    "sparkle bank": "Sparkle Microfinance Bank",

    "vfd": "VFD Microfinance Bank",
    "vfd mfb": "VFD Microfinance Bank",

    "eyowo": "Eyowo",

    "paycom": "Opay",

    "paga": "Pagatech",

    "cowrywise": "Cowrywise",

    "piggyvest": "PiggyVest",

    "chipper": "Chipper Cash",
    "chipper cash": "Chipper Cash",
}


def get_bank_codes() -> dict:
    """Fetch current bank list from Paystack dynamically."""
    # logger.info("Fetching bank list from Paystack...")
    url = "https://api.paystack.co/bank?country=nigeria&perPage=100"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}

    response = requests.get(url, headers=headers)
    data = response.json()

    if not data.get("status"):
        raise ValidationError("Failed to fetch bank list from Paystack")

    # logger.info(f"Successfully fetched {len(data['data'])} banks.")
    return {bank["name"]: bank["code"] for bank in data["data"]}


def fetch_account_name(account_number: str, bank_name: str) -> str:
    """
    Fetches the account name for a given account number and bank name using Paystack API.
    Args:
        account_number (str): Bank account number
        bank_name (str): Bank name input by user (case-insensitive, partial match supported)
    Returns:
        str: Verified account name
    Raises:
        ValidationError: If bank not found, verification fails, or API error occurs
    """
    bank_codes = get_bank_codes()

    normalized_input = re.sub(r'\bbank\b', '', bank_name, flags=re.IGNORECASE).strip().lower()
    # logger.info(f"Normalized bank input: '{normalized_input}'")

    # Check aliases - substring match (input exists in any alias key or vice versa)
    resolved_name = None
    for alias, official_name in BANK_ALIASES.items():
        if normalized_input in alias or alias in normalized_input:
            resolved_name = official_name
            break

    matched_bank = None
    if resolved_name:
        matched_bank = next((name for name in bank_codes if name.lower() == resolved_name.lower()), None)
        # logger.info(f"Alias resolved to: '{matched_bank}'")

    # Fall back to fuzzy match against Paystack bank list directly
    if not matched_bank:
        for name in bank_codes:
            normalized_name = re.sub(r'\bbank\b', '', name, flags=re.IGNORECASE).strip().lower()
            if normalized_input in normalized_name or normalized_name in normalized_input:
                matched_bank = name
                break

    if not matched_bank:
        raise ValidationError(f"Bank name '{bank_name}' not recognized or not supported.")

    # logger.info(f"Matched bank: '{matched_bank}' | Code: {bank_codes[matched_bank]}")
    bank_code = bank_codes[matched_bank]

    # logger.info(f"Resolving account '{account_number}' with bank code '{bank_code}'...")
    url = f"https://api.paystack.co/bank/resolve?account_number={account_number}&bank_code={bank_code}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}

    response = requests.get(url, headers=headers)
    # logger.info(f"Status Code: {response.status_code}")
    # logger.info(f"Response Text: {response.text}")

    try:
        data = response.json()
    except ValidationError:
        raise ValidationError(f"API returned non-JSON response: {response.text}")

    if not data.get("status") or "account_name" not in data.get("data", {}):
        raise ValidationError(data.get("message", "Account verification failed"))

    account_name = data["data"]["account_name"]
    logger.info(f"Account successfully resolved: {account_name}")
    return account_name
