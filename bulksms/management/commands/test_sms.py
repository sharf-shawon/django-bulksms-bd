"""
Django management command to test SMS functionality
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from bulksms.client import BulkSMSClient
from bulksms.exceptions import BulkSMSError


class Command(BaseCommand):
    help = 'Test BulkSMS BD API functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            help='Phone number to send test SMS (e.g., 01712345678)',
        )
        parser.add_argument(
            '--message',
            type=str,
            default='This is a test message from Django BulkSMS BD package.',
            help='Test message content',
        )
        parser.add_argument(
            '--otp',
            type=str,
            help='Send OTP instead of regular message (provide OTP code)',
        )
        parser.add_argument(
            '--balance',
            action='store_true',
            help='Check account balance only',
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test API connection and credentials',
        )
        parser.add_argument(
            '--sender-id',
            type=str,
            help='Override default sender ID',
        )

    def handle(self, *args, **options):
        """Handle the command execution."""
        self.stdout.write("Django BulkSMS BD - Test Command")
        self.stdout.write("=" * 40)

        try:
            # Initialize client
            client = BulkSMSClient(sender_id=options.get('sender_id'))
            self.stdout.write(
                self.style.SUCCESS("✓ SMS client initialized successfully")
            )

            # Test connection if requested
            if options['test_connection']:
                self.test_connection(client)
                return

            # Check balance if requested
            if options['balance']:
                self.check_balance(client)
                return

            # Send SMS if phone number provided
            phone = options['phone']
            if phone:
                if options['otp']:
                    self.send_otp(client, phone, options['otp'])
                else:
                    self.send_sms(client, phone, options['message'])
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "No phone number provided. Use --phone argument to send test SMS."
                    )
                )
                self.check_balance(client)

        except BulkSMSError as e:
            raise CommandError(f"BulkSMS Error: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error: {e}")

    def test_connection(self, client):
        """Test API connection."""
        self.stdout.write("Testing API connection...")

        if client.test_connection():
            self.stdout.write(
                self.style.SUCCESS("✓ API connection successful")
            )
        else:
            self.stdout.write(
                self.style.ERROR("✗ API connection failed")
            )

    def check_balance(self, client):
        """Check account balance."""
        self.stdout.write("Checking account balance...")

        try:
            response = client.get_balance()
            self.stdout.write(
                self.style.SUCCESS("✓ Balance check successful")
            )
            self.stdout.write(f"Response: {response}")
        except BulkSMSError as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Balance check failed: {e}")
            )

    def send_sms(self, client, phone, message):
        """Send test SMS."""
        self.stdout.write(f"Sending SMS to {phone}...")
        self.stdout.write(f"Message: {message}")

        try:
            response = client.send_sms(phone, message)
            self.stdout.write(
                self.style.SUCCESS("✓ SMS sent successfully")
            )
            self.stdout.write(f"Response: {response}")
        except BulkSMSError as e:
            self.stdout.write(
                self.style.ERROR(f"✗ SMS sending failed: {e}")
            )

    def send_otp(self, client, phone, otp_code):
        """Send test OTP."""
        self.stdout.write(f"Sending OTP to {phone}...")
        self.stdout.write(f"OTP Code: {otp_code}")

        try:
            response = client.send_otp(phone, otp_code, "Test Company")
            self.stdout.write(
                self.style.SUCCESS("✓ OTP sent successfully")
            )
            self.stdout.write(f"Response: {response}")
        except BulkSMSError as e:
            self.stdout.write(
                self.style.ERROR(f"✗ OTP sending failed: {e}")
            )
