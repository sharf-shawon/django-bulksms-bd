"""
Django BulkSMS BD Package

A Django package for integrating with BulkSMSBD.net API for sending SMS messages.
"""
from .__version__ import __version__

__version__ = __version__
__author__ = "Sharfuddin Shawon"
__email__ = "sharf@shawon.me"

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
