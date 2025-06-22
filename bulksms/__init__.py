"""
Django BulkSMS BD Package

A Django package for integrating with BulkSMSBD.net API for sending SMS messages.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .client import BulkSMSClient
from .exceptions import (
    BulkSMSError,
    BulkSMSAPIError,
    BulkSMSConfigurationError,
    BulkSMSValidationError,
    BulkSMSNetworkError,
)

# Default Django app configuration
default_app_config = 'django_bulksms.apps.DjangoBulksmsBdConfig'

__all__ = [
    'BulkSMSClient',
    'BulkSMSError',
    'BulkSMSAPIError',
    'BulkSMSConfigurationError',
    'BulkSMSValidationError',
    'BulkSMSNetworkError',
]
