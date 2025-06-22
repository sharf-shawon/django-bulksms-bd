"""
Tests for bulksms.utils module
"""

import django
from django.test import TestCase
from django.core.exceptions import ValidationError
from bulksms.utils import (
    validate_phone_number,
    format_phone_number,
    validate_message,
    validate_sender_id,
    estimate_sms_cost,
    parse_phone_numbers,
    clean_message,
    is_valid_bangladesh_number
)
from bulksms.exceptions import (
    InvalidPhoneNumberError,
    InvalidMessageError,
    InvalidSenderIdError
)


class TestPhoneNumberValidation(TestCase):
    """Test phone number validation and formatting"""

    def setUp(self):
        """Set up test data"""
        self.valid_numbers = [
            '01712345678',
            '8801712345678', 
            '+8801712345678',
            '01612345678',
            '01512345678',
            '01812345678',
            '01912345678'
        ]

        self.invalid_numbers = [
            '0171234567',  # Too short
            '017123456789',  # Too long
            '01012345678',  # Invalid operator
            '8801012345678',  # Invalid with country code
            'abc01712345678',  # Contains letters
            '',  # Empty string
            None,  # None value
            '123456789'  # Wrong format
        ]

    def test_valid_phone_numbers(self):
        """Test validation of valid phone numbers"""
        for number in self.valid_numbers:
            with self.subTest(number=number):
                self.assertTrue(
                    validate_phone_number(number),
                    f"Should validate {number} as valid"
                )
                self.assertTrue(
                    is_valid_bangladesh_number(number),
                    f"Should recognize {number} as Bangladesh number"
                )

    def test_invalid_phone_numbers(self):
        """Test validation of invalid phone numbers"""
        for number in self.invalid_numbers:
            with self.subTest(number=number):
                with self.assertRaises(InvalidPhoneNumberError):
                    validate_phone_number(number)
                self.assertFalse(
                    is_valid_bangladesh_number(number),
                    f"Should recognize {number} as invalid Bangladesh number"
                )

    def test_phone_number_formatting(self):
        """Test phone number formatting"""
        test_cases = [
            ('01712345678', '8801712345678'),
            ('8801712345678', '8801712345678'),
            ('+8801712345678', '8801712345678'),
            ('01612345678', '8801612345678'),
        ]

        for input_number, expected in test_cases:
            with self.subTest(input_number=input_number):
                result = format_phone_number(input_number)
                self.assertEqual(result, expected)

    def test_parse_phone_numbers(self):
        """Test parsing multiple phone numbers"""
        # Test string input
        numbers_str = "01712345678,01812345678,01912345678"
        result = parse_phone_numbers(numbers_str)
        expected = ['8801712345678', '8801812345678', '8801912345678']
        self.assertEqual(result, expected)

        # Test list input
        numbers_list = ['01712345678', '01812345678']
        result = parse_phone_numbers(numbers_list)
        expected = ['8801712345678', '8801812345678']
        self.assertEqual(result, expected)

        # Test single number
        result = parse_phone_numbers('01712345678')
        expected = ['8801712345678']
        self.assertEqual(result, expected)

    def test_parse_phone_numbers_with_invalid(self):
        """Test parsing phone numbers with invalid numbers"""
        numbers_str = "01712345678,invalid,01812345678"
        with self.assertRaises(InvalidPhoneNumberError):
            parse_phone_numbers(numbers_str)


class TestMessageValidation(TestCase):
    """Test message validation and cleaning"""

    def test_valid_messages(self):
        """Test validation of valid messages"""
        valid_messages = [
            "Hello World!",
            "Test message with numbers 123",
            "Message with special chars: @#$%",
            "A" * 160,  # Max length
            "বাংলা মেসেজ",  # Bengali text
        ]

        for message in valid_messages:
            with self.subTest(message=message[:20]):
                self.assertTrue(validate_message(message))

    def test_invalid_messages(self):
        """Test validation of invalid messages"""
        invalid_messages = [
            "",  # Empty message
            None,  # None value
            "A" * 161,  # Too long
            "   ",  # Only whitespace
        ]

        for message in invalid_messages:
            with self.subTest(message=str(message)[:20]):
                with self.assertRaises(InvalidMessageError):
                    validate_message(message)

    def test_clean_message(self):
        """Test message cleaning functionality"""
        test_cases = [
            ("Hello & World", "Hello %26 World"),
            ("Price: $10", "Price: %2410"),
            ("Email@domain.com", "Email%40domain.com"),
            ("Test message", "Test message"),  # No special chars
            ("Multiple & symbols $ here", "Multiple %26 symbols %24 here"),
        ]

        for input_msg, expected in test_cases:
            with self.subTest(input_msg=input_msg):
                result = clean_message(input_msg)
                self.assertEqual(result, expected)


class TestSenderIdValidation(TestCase):
    """Test sender ID validation"""

    def test_valid_sender_ids(self):
        """Test validation of valid sender IDs"""
        valid_senders = [
            "Random",
            "COMPANY",
            "MyApp123",
            "Test-ID",
            "A" * 11,  # Max length
        ]

        for sender in valid_senders:
            with self.subTest(sender=sender):
                self.assertTrue(validate_sender_id(sender))

    def test_invalid_sender_ids(self):
        """Test validation of invalid sender IDs"""
        invalid_senders = [
            "",  # Empty
            None,  # None
            "A" * 12,  # Too long
            "   ",  # Only whitespace
            "sender with spaces",  # Contains spaces
        ]

        for sender in invalid_senders:
            with self.subTest(sender=str(sender)):
                with self.assertRaises(InvalidSenderIdError):
                    validate_sender_id(sender)


class TestCostEstimation(TestCase):
    """Test SMS cost estimation"""

    def test_single_sms_cost(self):
        """Test cost estimation for single SMS"""
        # Standard message (≤160 chars)
        message = "Hello World!"
        cost = estimate_sms_cost(message, 1)
        self.assertEqual(cost, 1.0)

        # Long message (>160 chars)
        long_message = "A" * 320  # 2 SMS segments
        cost = estimate_sms_cost(long_message, 1)
        self.assertEqual(cost, 2.0)

    def test_multiple_recipients_cost(self):
        """Test cost estimation for multiple recipients"""
        message = "Hello World!"
        cost = estimate_sms_cost(message, 5)
        self.assertEqual(cost, 5.0)

    def test_unicode_message_cost(self):
        """Test cost estimation for Unicode messages"""
        # Bengali message (Unicode)
        bengali_message = "হ্যালো বিশ্ব!"
        cost = estimate_sms_cost(bengali_message, 1, unicode_rate=2.0)
        self.assertEqual(cost, 2.0)

    def test_long_unicode_message_cost(self):
        """Test cost estimation for long Unicode messages"""
        # Long Bengali message (>70 chars, Unicode limit)
        long_bengali = "হ্যালো " * 20  # Should exceed 70 chars
        cost = estimate_sms_cost(long_bengali, 1, unicode_rate=2.0)
        self.assertGreater(cost, 2.0)


class TestUtilityHelpers(TestCase):
    """Test utility helper functions"""

    def test_phone_number_edge_cases(self):
        """Test edge cases in phone number handling"""
        # Test with extra whitespace
        number_with_spaces = "  01712345678  "
        result = format_phone_number(number_with_spaces.strip())
        self.assertEqual(result, "8801712345678")

        # Test with dashes
        number_with_dashes = "0171-234-5678"
        cleaned = number_with_dashes.replace("-", "")
        result = format_phone_number(cleaned)
        self.assertEqual(result, "8801712345678")

    def test_message_length_calculation(self):
        """Test message length calculation for different character sets"""
        # ASCII message
        ascii_msg = "Hello World!"
        self.assertEqual(len(ascii_msg), 12)

        # Unicode message (Bengali)
        unicode_msg = "হ্যালো বিশ্ব!"
        # Unicode messages have different length limits (70 vs 160)
        self.assertGreater(len(unicode_msg.encode('utf-8')), len(unicode_msg))

    def test_bulk_validation(self):
        """Test bulk validation operations"""
        numbers = ['01712345678', '01812345678', '01912345678']
        messages = ['Hello 1', 'Hello 2', 'Hello 3']

        # Validate all numbers
        for number in numbers:
            self.assertTrue(validate_phone_number(number))

        # Validate all messages
        for message in messages:
            self.assertTrue(validate_message(message))


if __name__ == '__main__':
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')
    django.setup()

    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["__main__"])
