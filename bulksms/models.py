"""
Django models for SMS tracking and logging
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class SMSMessage(models.Model):
    """Model to track SMS messages sent through the API."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
        ('expired', 'Expired'),
    ]

    MESSAGE_TYPE_CHOICES = [
        ('single', 'Single SMS'),
        ('bulk', 'Bulk SMS'),
        ('otp', 'OTP'),
    ]

    # Message details
    message_id = models.CharField(max_length=100, unique=True, db_index=True)
    sender_id = models.CharField(max_length=20)
    recipient = models.CharField(max_length=20)
    message_content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='single')

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    api_response_code = models.IntegerField(null=True, blank=True)
    api_response_message = models.TextField(blank=True)

    # Cost tracking
    sms_parts = models.IntegerField(default=1)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # User tracking (optional)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['recipient', 'created_at']),
            models.Index(fields=['message_type', 'created_at']),
        ]

    def __str__(self):
        return f"SMS to {self.recipient} - {self.status}"

    def mark_as_sent(self, api_response=None):
        """Mark message as sent."""
        self.status = 'sent'
        self.sent_at = timezone.now()
        if api_response:
            self.api_response_code = api_response.get('code')
            self.api_response_message = api_response.get('message', '')
        self.save()

    def mark_as_failed(self, error_message, error_code=None):
        """Mark message as failed."""
        self.status = 'failed'
        self.api_response_message = error_message
        if error_code:
            self.api_response_code = error_code
        self.save()

    @property
    def is_successful(self):
        """Check if message was sent successfully."""
        return self.status in ['sent', 'delivered']


class BulkSMSBatch(models.Model):
    """Model to track bulk SMS batches."""

    batch_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # Statistics
    total_recipients = models.IntegerField(default=0)
    successful_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)

    # Cost tracking
    total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # User tracking
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Batch {self.batch_id} - {self.total_recipients} recipients"

    def update_statistics(self):
        """Update batch statistics based on related messages."""
        messages = SMSMessage.objects.filter(
            message_id__startswith=f"{self.batch_id}_"
        )

        self.total_recipients = messages.count()
        self.successful_count = messages.filter(status__in=['sent', 'delivered']).count()
        self.failed_count = messages.filter(status='failed').count()

        # Calculate total cost
        total_cost = messages.aggregate(
            total=models.Sum('estimated_cost')
        )['total'] or 0
        self.total_estimated_cost = total_cost

        self.save()

    @property
    def success_rate(self):
        """Calculate success rate percentage."""
        if self.total_recipients == 0:
            return 0
        return (self.successful_count / self.total_recipients) * 100

    @property
    def is_completed(self):
        """Check if batch is completed."""
        return self.completed_at is not None


class SMSTemplate(models.Model):
    """Model to store reusable SMS templates."""

    TEMPLATE_TYPE_CHOICES = [
        ('otp', 'OTP Template'),
        ('marketing', 'Marketing'),
        ('notification', 'Notification'),
        ('reminder', 'Reminder'),
        ('alert', 'Alert'),
        ('welcome', 'Welcome Message'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    content = models.TextField(help_text="Use {variable_name} for dynamic content")

    # Metadata
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # User tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['name']
        unique_together = [['name', 'template_type']]

    def __str__(self):
        return f"{self.name} ({self.template_type})"

    def render(self, **kwargs):
        """Render template with provided variables."""
        content = self.content
        for key, value in kwargs.items():
            content = content.replace(f"{{{key}}}", str(value))
        return content

    def increment_usage(self):
        """Increment usage counter."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class APIUsageLog(models.Model):
    """Model to log API usage and monitor limits."""

    REQUEST_TYPE_CHOICES = [
        ('sms', 'Send SMS'),
        ('bulk_sms', 'Send Bulk SMS'),
        ('balance', 'Check Balance'),
        ('otp', 'Send OTP'),
    ]

    # Request details
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10, default='POST')

    # Request data (stored as JSON)
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)

    # Response details
    status_code = models.IntegerField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now)

    # User tracking
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['request_type', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.request_type} - {self.timestamp}"

    @classmethod
    def log_request(cls, request_type, endpoint, method='POST', **kwargs):
        """Create a new API usage log entry."""
        return cls.objects.create(
            request_type=request_type,
            endpoint=endpoint,
            method=method,
            **kwargs
        )


class SMSBlacklist(models.Model):
    """Model to store blacklisted phone numbers."""

    REASON_CHOICES = [
        ('user_request', 'User Requested'),
        ('spam_complaint', 'Spam Complaint'),
        ('invalid_number', 'Invalid Number'),
        ('carrier_block', 'Carrier Block'),
        ('admin_block', 'Admin Block'),
    ]

    phone_number = models.CharField(max_length=20, unique=True, db_index=True)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Leave blank for permanent block")

    # User tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Blacklisted: {self.phone_number}"

    @property
    def is_active(self):
        """Check if blacklist entry is currently active."""
        if not self.expires_at:
            return True
        return timezone.now() < self.expires_at

    @classmethod
    def is_blacklisted(cls, phone_number):
        """Check if a phone number is blacklisted."""
        from .utils import format_phone_number

        formatted_number = format_phone_number(phone_number)
        return cls.objects.filter(
            phone_number=formatted_number,
            expires_at__isnull=True
        ).exists() or cls.objects.filter(
            phone_number=formatted_number,
            expires_at__gt=timezone.now()
        ).exists()
