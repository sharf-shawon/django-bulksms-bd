"""
Django app configuration for BulkSMS BD package
"""

from django.apps import AppConfig


class DjangoBulksmsBdConfig(AppConfig):
    """Django app configuration for BulkSMS BD."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_bulksms'
    verbose_name = 'Django BulkSMS BD'

    def ready(self):
        """Perform initialization when Django starts."""
        # Import signals or perform other initialization tasks
        pass
