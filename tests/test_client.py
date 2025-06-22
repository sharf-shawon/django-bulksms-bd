"""
Tests for BulkSMS client functionality
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from requests.exceptions import ConnectionError, Timeout

from bulksms.client import BulkSMSClient
from bulksms.exceptions import (
    BulkSMSAPIError,
    BulkSMSConfigurationError,
    BulkSMSValidationError,
    BulkSMSNetworkError,
    BulkSMSTimeoutError,
)


@override_settings(
    BULKSMS_API_KEY='test_api_key',
    BULKSMS_SENDER_ID='TestSender'
)
class BulkSMSClientTestCase(TestCase):
    """Test cases for BulkSMS client."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = BulkSMSClient()
        self.test_phone = '01712345678'
        self.test_message = 'Test message'

    def test_client_initialization_with_settings(self):
        """Test client initialization with Django settings."""
        self.assertEqual(self.client.api_key, 'test_api_key')
        self.assertEqual(self.client.sender_id, 'TestSender')

    def test_client_initialization_with_parameters(self):
        """Test client initialization with parameters."""
        client = BulkSMSClient(api_key='param_key', sender_id='ParamSender')
        self.assertEqual(client.api_key, 'param_key')
        self.assertEqual(client.sender_id, 'ParamSender')

    def test_client_initialization_missing_api_key(self):
        """Test client initialization fails without API key."""
        with override_settings(BULKSMS_API_KEY=None):
            with self.assertRaises(BulkSMSConfigurationError):
                BulkSMSClient()

    def test_client_initialization_missing_sender_id(self):
        """Test client initialization fails without sender ID."""
        with override_settings(BULKSMS_SENDER_ID=None):
            with self.assertRaises(BulkSMSConfigurationError):
                BulkSMSClient()

    @patch('bulksms.client.requests.Session.request')
    def test_send_sms_success(self, mock_request):
        """Test successful SMS sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 202, 'message': 'SMS Submitted Successfully'}
        mock_response.text = '{"code": 202, "message": "SMS Submitted Successfully"}'
        mock_request.return_value = mock_response

        response = self.client.send_sms(self.test_phone, self.test_message)

        self.assertEqual(response['code'], 202)
        self.assertEqual(response['message'], 'SMS Submitted Successfully')
        mock_request.assert_called_once()

    @patch('bulksms.client.requests.Session.request')
    def test_send_sms_api_error(self, mock_request):
        """Test SMS sending with API error."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 1007, 'message': 'Balance Insufficient'}
        mock_response.text = '{"code": 1007, "message": "Balance Insufficient"}'
        mock_request.return_value = mock_response

        with self.assertRaises(BulkSMSAPIError):
            self.client.send_sms(self.test_phone, self.test_message)

    @patch('bulksms.client.requests.Session.request')
    def test_send_sms_network_error(self, mock_request):
        """Test SMS sending with network error."""
        mock_request.side_effect = ConnectionError("Connection failed")

        with self.assertRaises(BulkSMSNetworkError):
            self.client.send_sms(self.test_phone, self.test_message)

    @patch('bulksms.client.requests.Session.request')
    def test_send_sms_timeout(self, mock_request):
        """Test SMS sending with timeout."""
        mock_request.side_effect = Timeout("Request timed out")

        with self.assertRaises(BulkSMSTimeoutError):
            self.client.send_sms(self.test_phone, self.test_message)

    def test_send_sms_invalid_phone(self):
        """Test SMS sending with invalid phone number."""
        with self.assertRaises(BulkSMSValidationError):
            self.client.send_sms('invalid_phone', self.test_message)

    def test_send_sms_empty_message(self):
        """Test SMS sending with empty message."""
        with self.assertRaises(BulkSMSValidationError):
            self.client.send_sms(self.test_phone, '')

    @patch('bulksms.client.requests.Session.request')
    def test_send_bulk_sms_success(self, mock_request):
        """Test successful bulk SMS sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 202, 'message': 'SMS Submitted Successfully'}
        mock_response.text = '{"code": 202, "message": "SMS Submitted Successfully"}'
        mock_request.return_value = mock_response

        messages = [
            {'to': '01712345678', 'message': 'Message 1'},
            {'to': '01712345679', 'message': 'Message 2'},
        ]

        response = self.client.send_bulk_sms(messages)

        self.assertEqual(response['code'], 202)
        mock_request.assert_called_once()

    def test_send_bulk_sms_empty_messages(self):
        """Test bulk SMS sending with empty messages list."""
        with self.assertRaises(BulkSMSValidationError):
            self.client.send_bulk_sms([])

    def test_send_bulk_sms_invalid_format(self):
        """Test bulk SMS sending with invalid message format."""
        messages = [
            {'to': '01712345678'},  # Missing 'message' key
        ]

        with self.assertRaises(BulkSMSValidationError):
            self.client.send_bulk_sms(messages)

    @patch('bulksms.client.requests.Session.request')
    def test_get_balance_success(self, mock_request):
        """Test successful balance check."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'balance': 100.50, 'currency': 'BDT'}
        mock_response.text = '{"balance": 100.50, "currency": "BDT"}'
        mock_request.return_value = mock_response

        response = self.client.get_balance()

        self.assertEqual(response['balance'], 100.50)
        self.assertEqual(response['currency'], 'BDT')

    @patch('bulksms.client.requests.Session.request')
    def test_send_otp_success(self, mock_request):
        """Test successful OTP sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 202, 'message': 'SMS Submitted Successfully'}
        mock_response.text = '{"code": 202, "message": "SMS Submitted Successfully"}'
        mock_request.return_value = mock_response

        response = self.client.send_otp(self.test_phone, '1234', 'TestCompany')

        self.assertEqual(response['code'], 202)

        # Verify the request was made with correct OTP format
        call_args = mock_request.call_args
        request_data = call_args[1]['data']
        self.assertIn('Your TestCompany OTP is 1234', request_data['message'])

    @patch('bulksms.client.BulkSMSClient.get_balance')
    def test_connection_test_success(self, mock_get_balance):
        """Test successful connection test."""
        mock_get_balance.return_value = {'balance': 100}

        result = self.client.test_connection()

        self.assertTrue(result)

    @patch('bulksms.client.BulkSMSClient.get_balance')
    def test_connection_test_failure(self, mock_get_balance):
        """Test failed connection test."""
        mock_get_balance.side_effect = BulkSMSAPIError("Connection failed")

        result = self.client.test_connection()

        self.assertFalse(result)

    def test_handle_api_error_authentication(self):
        """Test handling of authentication errors."""
        response_data = {'code': 1011, 'message': 'User ID not found'}

        with self.assertRaises(BulkSMSAPIError):
            self.client._handle_api_error(1011, response_data)

    def test_handle_api_error_balance(self):
        """Test handling of balance errors."""
        response_data = {'code': 1007, 'message': 'Balance Insufficient'}

        with self.assertRaises(BulkSMSAPIError):
            self.client._handle_api_error(1007, response_data)

    def test_handle_api_error_invalid_number(self):
        """Test handling of invalid number errors."""
        response_data = {'code': 1001, 'message': 'Invalid Number'}

        with self.assertRaises(BulkSMSAPIError):
            self.client._handle_api_error(1001, response_data)


class BulkSMSClientIntegrationTestCase(TestCase):
    """Integration tests for BulkSMS client."""

    @override_settings(
        BULKSMS_API_KEY='test_api_key',
        BULKSMS_SENDER_ID='TestSender'
    )
    def setUp(self):
        """Set up test fixtures."""
        self.client = BulkSMSClient()

    def test_phone_number_formatting(self):
        """Test phone number formatting in requests."""
        with patch('bulksms.client.requests.Session.request') as mock_request:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'code': 202, 'message': 'Success'}
            mock_response.text = '{"code": 202, "message": "Success"}'
            mock_request.return_value = mock_response

            # Test various phone number formats
            test_numbers = [
                '01712345678',
                '8801712345678',
                '+8801712345678',
                '880 1712345678',
                '017-1234-5678',
            ]

            for number in test_numbers:
                self.client.send_sms(number, 'Test message')

                # Verify the formatted number in the request
                call_args = mock_request.call_args
                request_data = call_args[1]['data']
                self.assertEqual(request_data['number'], '8801712345678')

    def test_message_validation(self):
        """Test message content validation."""
        test_phone = '01712345678'

        # Test empty message
        with self.assertRaises(BulkSMSValidationError):
            self.client.send_sms(test_phone, '')

        # Test whitespace-only message
        with self.assertRaises(BulkSMSValidationError):
            self.client.send_sms(test_phone, '   ')

        # Test very long message
        long_message = 'x' * 1600  # Longer than 1530 character limit
        with self.assertRaises(BulkSMSValidationError):
            self.client.send_sms(test_phone, long_message)
