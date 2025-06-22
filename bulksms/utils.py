"""
Utility functions for Django BulkSMS BD package
"""

import re
from typing import Any, Optional
from django.conf import settings
from .exceptions import BulkSMSValidationError, BulkSMSConfigurationError


def get_bulksms_setting(setting_name: str, default: Any = None) -> Any:
    """
    Get BulkSMS configuration from Django settings.

    Settings can be defined in multiple ways:
    1. BULKSMS_<SETTING_NAME>
    2. In BULKSMS dictionary

    Args:
        setting_name: Name of the setting
        default: Default value if setting is not found

    Returns:
        Setting value
    """
    # Try BULKSMS_<SETTING_NAME> format first
    full_setting_name = f"BULKSMS_{setting_name}"
    if hasattr(settings, full_setting_name):
        return getattr(settings, full_setting_name)

    # Try BULKSMS dictionary format
    if hasattr(settings, 'BULKSMS') and isinstance(settings.BULKSMS, dict):
        return settings.BULKSMS.get(setting_name, default)

    return default


def validate_phone_number(phone_number: str) -> None:
    """
    Validate Bangladesh phone number format.

    Accepts formats:
    - 8801712345678 (with country code)
    - 01712345678 (without country code)
    - +8801712345678 (with + prefix)

    Args:
        phone_number: Phone number to validate

    Raises:
        BulkSMSValidationError: If phone number is invalid
    """
    if not phone_number:
        raise BulkSMSValidationError("Phone number cannot be empty")

    # Remove spaces and hyphens
    cleaned_number = re.sub(r'[\s\-]', '', phone_number)

    # Remove + prefix if present
    if cleaned_number.startswith('+'):
        cleaned_number = cleaned_number[1:]

    # Bangladesh phone number patterns
    patterns = [
        r'^8801[3-9]\d{8}$',  # With country code 880
        r'^01[3-9]\d{8}$',    # Without country code
    ]

    for pattern in patterns:
        if re.match(pattern, cleaned_number):
            return

    raise BulkSMSValidationError(
        f"Invalid Bangladesh phone number format: {phone_number}. "
        "Expected formats: 8801712345678, 01712345678, or +8801712345678"
    )


def format_phone_number(phone_number: str) -> str:
    """
    Format phone number to the standard format required by BulkSMS API.

    Args:
        phone_number: Phone number to format

    Returns:
        Formatted phone number with country code (8801xxxxxxxxx)
    """
    # Remove spaces, hyphens, and + prefix
    cleaned_number = re.sub(r'[\s\-\+]', '', phone_number)

    # Add country code if not present
    if cleaned_number.startswith('01'):
        cleaned_number = '880' + cleaned_number

    return cleaned_number


def validate_sender_id(sender_id: str) -> None:
    """
    Validate sender ID format.

    Args:
        sender_id: Sender ID to validate

    Raises:
        BulkSMSValidationError: If sender ID is invalid
    """
    if not sender_id:
        raise BulkSMSValidationError("Sender ID cannot be empty")

    if len(sender_id) > 20:
        raise BulkSMSValidationError("Sender ID cannot be longer than 20 characters")

    # Check for valid characters (alphanumeric and some special chars)
    if not re.match(r'^[a-zA-Z0-9\s\-\.]+$', sender_id):
        raise BulkSMSValidationError(
            "Sender ID can only contain letters, numbers, spaces, hyphens, and dots"
        )


def validate_message(message: str) -> None:
    """
    Validate SMS message content.

    Args:
        message: SMS message to validate

    Raises:
        BulkSMSValidationError: If message is invalid
    """
    if not message:
        raise BulkSMSValidationError("Message cannot be empty")

    if not message.strip():
        raise BulkSMSValidationError("Message cannot be only whitespace")

    # Check message length (160 chars for single SMS, 1530 for concatenated)
    if len(message) > 1530:
        raise BulkSMSValidationError(
            "Message is too long. Maximum length is 1530 characters for concatenated SMS."
        )


def get_message_parts(message: str) -> int:
    """
    Calculate how many SMS parts the message will be split into.

    Args:
        message: SMS message

    Returns:
        Number of SMS parts
    """
    if len(message) <= 160:
        return 1
    elif len(message) <= 306:
        return 2
    elif len(message) <= 459:
        return 3
    elif len(message) <= 612:
        return 4
    elif len(message) <= 765:
        return 5
    elif len(message) <= 918:
        return 6
    elif len(message) <= 1071:
        return 7
    elif len(message) <= 1224:
        return 8
    elif len(message) <= 1377:
        return 9
    elif len(message) <= 1530:
        return 10
    else:
        return 11  # Max parts


def estimate_sms_cost(message: str, recipient_count: int = 1) -> dict:
    """
    Estimate SMS cost based on message length and recipient count.

    Args:
        message: SMS message
        recipient_count: Number of recipients

    Returns:
        Dictionary with cost estimation details
    """
    parts = get_message_parts(message)
    base_cost_per_sms = get_bulksms_setting('BASE_COST_PER_SMS', 0.50)  # Default cost in BDT

    total_sms_count = parts * recipient_count
    total_cost = total_sms_count * base_cost_per_sms

    return {
        'message_length': len(message),
        'sms_parts': parts,
        'recipient_count': recipient_count,
        'total_sms_count': total_sms_count,
        'cost_per_sms': base_cost_per_sms,
        'total_cost': total_cost,
        'currency': 'BDT'
    }


def sanitize_message(message: str) -> str:
    """
    Sanitize message content for SMS sending.

    Args:
        message: Original message

    Returns:
        Sanitized message
    """
    # Remove or replace problematic characters
    # Replace smart quotes with regular quotes
    message = message.replace('"', '"').replace('"', '"')
    message = message.replace("'", "'").replace("'", "'")

    # Remove null characters and other control characters
    message = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', message)

    # Normalize whitespace
    message = re.sub(r'\s+', ' ', message.strip())

    return message


def is_bengali_text(text: str) -> bool:
    """
    Check if text contains Bengali characters.

    Args:
        text: Text to check

    Returns:
        True if text contains Bengali characters
    """
    bengali_pattern = r'[\u0980-\u09FF]'
    return bool(re.search(bengali_pattern, text))


def validate_otp_format(otp: str, brand_name: str) -> None:
    """
    Validate OTP message format according to BulkSMS BD requirements.

    Args:
        otp: OTP code
        brand_name: Brand/company name

    Raises:
        BulkSMSValidationError: If format is invalid
    """
    if not otp:
        raise BulkSMSValidationError("OTP code cannot be empty")

    if not brand_name:
        raise BulkSMSValidationError("Brand name cannot be empty")

    # Check OTP format (should be numeric and reasonable length)
    if not re.match(r'^\d{4,8}$', otp):
        raise BulkSMSValidationError("OTP should be 4-8 digits")

    # Check brand name length
    if len(brand_name) > 50:
        raise BulkSMSValidationError("Brand name cannot be longer than 50 characters")


def get_default_settings() -> dict:
    """
    Get default settings for BulkSMS configuration.

    Returns:
        Dictionary with default settings
    """
    return {
        'API_KEY': '',
        'SENDER_ID': '',
        'TIMEOUT': 30,
        'MAX_RETRIES': 3,
        'BACKOFF_FACTOR': 0.5,
        'VERIFY_SSL': False,
        'BASE_COST_PER_SMS': 0.50,
        'LOG_REQUESTS': True,
        'LOG_RESPONSES': True,
        'SAVE_TO_DATABASE': True,
    }
