# Django BulkSMS BD

A comprehensive Django package for integrating with the BulkSMSBD.net API to send SMS messages easily and reliably.

## Features

- **Easy Integration**: Simple setup with Django settings
- **Multiple SMS Types**: Support for single SMS, bulk SMS, and OTP messages
- **Robust Error Handling**: Comprehensive exception handling with meaningful error messages
- **Retry Mechanism**: Built-in retry logic with exponential backoff
- **Request Logging**: Optional logging of all API requests and responses
- **Phone Number Validation**: Automatic validation and formatting of Bangladesh phone numbers
- **Cost Estimation**: Estimate SMS costs before sending
- **Database Tracking**: Optional database models to track SMS history
- **Management Commands**: Django management commands for testing
- **Comprehensive Testing**: Full test suite with mocking support

## Installation

### 1. Install the Package

```bash
pip install django-bulksms-bd
```

### 2. Add to Django Settings

Add the app to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... your other apps
    'bulksms',
]
```

### 3. Configure API Credentials

Add your BulkSMS BD credentials to your Django settings:

```python
# Method 1: Individual settings
BULKSMS_API_KEY = 'your_api_key_here'
BULKSMS_SENDER_ID = 'your_sender_id'

# Method 2: Dictionary configuration
BULKSMS = {
    'API_KEY': 'your_api_key_here',
    'SENDER_ID': 'your_sender_id',
    'TIMEOUT': 30,
    'MAX_RETRIES': 3,
    'VERIFY_SSL': False,
}
```

### 4. Run Migrations (Optional)

If you want to use the database tracking features:

```bash
python manage.py migrate
```

## Quick Start

### Basic SMS Sending

```python
from bulksms.client import BulkSMSClient

# Initialize client (uses settings from Django configuration)
client = BulkSMSClient()

# Send a single SMS
response = client.send_sms(
    phone_numbers='01712345678',
    message='Hello from Django BulkSMS BD!'
)

print(f"SMS sent successfully: {response}")
```

### Bulk SMS Sending

```python
# Send to multiple recipients with the same message
response = client.send_sms(
    phone_numbers=['01712345678', '01812345678', '01912345678'],
    message='Hello everyone!'
)

# Send different messages to different recipients
messages = [
    {'to': '01712345678', 'message': 'Hello John!'},
    {'to': '01812345678', 'message': 'Hello Jane!'},
    {'to': '01912345678', 'message': 'Hello Bob!'},
]

response = client.send_bulk_sms(messages)
```

### OTP Messages

```python
# Send OTP with proper formatting
response = client.send_otp(
    phone_number='01712345678',
    otp_code='123456',
    brand_name='Your Company'
)
# This sends: "Your Your Company OTP is 123456"
```

### Check Account Balance

```python
balance_info = client.get_balance()
print(f"Account balance: {balance_info}")
```

## Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `BULKSMS_API_KEY` | Your BulkSMS BD API key | Required |
| `BULKSMS_SENDER_ID` | Your approved sender ID | Required |
| `BULKSMS_BASE_URL` | BulkSMS Base URL | https://bulksmsbd.net/api |
| `BULKSMS_TIMEOUT` | Request timeout in seconds | 30 |
| `BULKSMS_MAX_RETRIES` | Maximum retry attempts | 3 |
| `BULKSMS_BACKOFF_FACTOR` | Retry backoff factor | 0.5 |
| `BULKSMS_VERIFY_SSL` | Verify SSL certificates | False |
| `BULKSMS_BASE_COST_PER_SMS` | Cost per SMS for estimation | 0.50 |
| `BULKSMS_LOG_REQUESTS` | Log API requests | True |
| `BULKSMS_SAVE_TO_DATABASE` | Save SMS to database | True |

## Error Handling

The package provides comprehensive error handling with specific exception types:

```python
from bulksms.exceptions import (
    BulkSMSAPIError,
    BulkSMSValidationError,
    BulkSMSNetworkError,
    BulkSMSConfigurationError,
)

try:
    response = client.send_sms('01712345678', 'Test message')
except BulkSMSValidationError as e:
    print(f"Validation error: {e}")
except BulkSMSAPIError as e:
    print(f"API error: {e} (Code: {e.error_code})")
except BulkSMSNetworkError as e:
    print(f"Network error: {e}")
except BulkSMSConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Management Commands

### Test SMS Functionality

```bash
# Test connection
python manage.py test_sms --test-connection

# Check balance
python manage.py test_sms --balance

# Send test SMS
python manage.py test_sms --phone 01712345678 --message "Test message"

# Send test OTP
python manage.py test_sms --phone 01712345678 --otp 123456
```

## Django Integration Examples

### In Django Views

```python
from django.shortcuts import render
from django.contrib import messages
from bulksms.client import BulkSMSClient
from bulksms.exceptions import BulkSMSError

def send_notification(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        
        try:
            client = BulkSMSClient()
            response = client.send_sms(phone, message)
            messages.success(request, 'SMS sent successfully!')
        except BulkSMSError as e:
            messages.error(request, f'Failed to send SMS: {e}')
    
    return render(request, 'send_sms.html')
```

### In Django Signals

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from bulksms.client import BulkSMSClient

@receiver(post_save, sender=User)
def send_welcome_sms(sender, instance, created, **kwargs):
    if created and instance.profile.phone_number:
        try:
            client = BulkSMSClient()
            client.send_sms(
                instance.profile.phone_number,
                f'Welcome to our platform, {instance.first_name}!'
            )
        except Exception as e:
            # Log error but don't fail user creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send welcome SMS: {e}")
```

### With Celery (Async)

```python
from celery import shared_task
from bulksms.client import BulkSMSClient

@shared_task
def send_sms_async(phone_numbers, message):
    """Send SMS asynchronously using Celery."""
    try:
        client = BulkSMSClient()
        response = client.send_sms(phone_numbers, message)
        return {'success': True, 'response': response}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Usage
send_sms_async.delay(['01712345678'], 'Your order has been confirmed!')
```

## Database Models

The package includes optional Django models for tracking SMS history:

- `SMSMessage`: Track individual SMS messages
- `BulkSMSBatch`: Track bulk SMS batches
- `SMSTemplate`: Store reusable SMS templates
- `APIUsageLog`: Log API usage for monitoring
- `SMSBlacklist`: Manage blacklisted phone numbers

### Using SMS Templates

```python
from bulksms.models import SMSTemplate

# Create a template
template = SMSTemplate.objects.create(
    name='welcome_message',
    template_type='welcome',
    content='Welcome {name}! Your account has been created successfully.'
)

# Use the template
message = template.render(name='John Doe')
client.send_sms('01712345678', message)
```

## Testing

The package includes comprehensive tests. Run them with:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=bulksms
```

## API Reference

### BulkSMSClient

#### Methods

- `send_sms(phone_numbers, message, sender_id=None)`: Send SMS to one or more recipients
- `send_bulk_sms(messages, sender_id=None)`: Send different messages to different recipients
- `send_otp(phone_number, otp_code, brand_name, sender_id=None)`: Send OTP message
- `get_balance()`: Check account balance
- `test_connection()`: Test API connectivity

#### Error Codes

The API returns various error codes. The package handles these automatically:

| Code | Meaning |
|------|---------|
| 202 | SMS Submitted Successfully |
| 1001 | Invalid Number |
| 1002 | Sender ID not correct/disabled |
| 1007 | Balance Insufficient |
| 1011 | User ID not found |
| 1032 | IP Not whitelisted |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Check the documentation
- Review the examples in the `examples/` directory

## Changelog

### Version 1.0.0
- Initial release
- Basic SMS sending functionality
- Bulk SMS support
- OTP message support
- Error handling and retry logic
- Django integration
- Database models for tracking
- Management commands
- Comprehensive test suite
