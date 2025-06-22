"""
BulkSMS BD API Client

Main client class for interacting with BulkSMSBD.net API
"""

import json
import logging
import time
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlencode, quote_plus

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from django.conf import settings

from .exceptions import (
    BulkSMSAPIError,
    BulkSMSConfigurationError,
    BulkSMSValidationError,
    BulkSMSNetworkError,
    BulkSMSTimeoutError,
    BulkSMSAuthenticationError,
    BulkSMSBalanceError,
    BulkSMSInvalidNumberError,
)
from .utils import (
    validate_phone_number,
    validate_sender_id,
    validate_message,
    format_phone_number,
    get_bulksms_setting,
)


logger = logging.getLogger(__name__)


class BulkSMSClient:
    """
    BulkSMS BD API Client

    A comprehensive client for interacting with BulkSMSBD.net API with support for:
    - One-to-many SMS sending
    - Many-to-many SMS sending
    - Balance checking
    - Retry mechanism with exponential backoff
    - Comprehensive error handling
    - Request/response logging
    """

    # API endpoints
    BASE_URL = "https://bulksmsbd.net/api"
    SMS_ENDPOINT = f"{BASE_URL}/smsapi"
    SMS_MANY_ENDPOINT = f"{BASE_URL}/smsapimany"
    BALANCE_ENDPOINT = f"{BASE_URL}/getBalanceApi"

    def __init__(
        self,
        base_url: Optional[str] = BASE_URL,
        api_key: Optional[str] = None,
        sender_id: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        verify_ssl: bool = False,
    ):
        """
        Initialize BulkSMS client.

        Args:
            api_key: BulkSMS API key (if not provided, reads from Django settings)
            sender_id: Default sender ID (if not provided, reads from Django settings)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
            verify_ssl: Whether to verify SSL certificates
        """
        # Get configuration from Django settings or parameters
        self.base_url = base_url or get_bulksms_setting('BASE_URL', self.BASE_URL)
        self.api_key = api_key or get_bulksms_setting('API_KEY')
        self.sender_id = sender_id or get_bulksms_setting('SENDER_ID')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.SMS_ENDPOINT = f"{self.base_url}/smsapi"
        self.SMS_MANY_ENDPOINT = f"{self.base_url}/smsapimany"
        self.BALANCE_ENDPOINT = f"{self.base_url}/getBalanceApi"

        # Validate required configuration
        if not self.api_key:
            raise BulkSMSConfigurationError(
                "API key is required. Set BULKSMS_API_KEY in Django settings or pass api_key parameter."
            )

        if not self.sender_id:
            raise BulkSMSConfigurationError(
                "Sender ID is required. Set BULKSMS_SENDER_ID in Django settings or pass sender_id parameter."
            )

        # Configure HTTP session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.info(f"BulkSMS client initialized with sender_id: {self.sender_id}")

    def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with error handling and logging.

        Args:
            method: HTTP method (GET, POST)
            url: Request URL
            data: Request data for POST requests
            params: URL parameters for GET requests

        Returns:
            Parsed response data

        Raises:
            Various BulkSMS exceptions based on error type
        """
        try:
            logger.debug(f"Making {method} request to {url}")

            # Make the request
            response = self.session.request(
                method=method,
                url=url,
                data=data,
                params=params,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )

            # Log response details
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response content: {response.text}")

            # Handle HTTP errors
            if response.status_code >= 400:
                raise BulkSMSNetworkError(
                    f"HTTP {response.status_code}: {response.text}",
                    error_code=response.status_code,
                    response=response.text,
                )

            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                # If response is not JSON, treat as plain text
                response_data = {"message": response.text, "code": None}

            # Check for API errors based on response code
            if isinstance(response_data, dict):
                error_code = response_data.get('code')

                # Handle success case
                if error_code == 202:
                    logger.info("SMS sent successfully")
                    return response_data

                # Handle error cases
                elif error_code and error_code != 202:
                    self._handle_api_error(error_code, response_data)

            return response_data

        except requests.exceptions.Timeout:
            raise BulkSMSTimeoutError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise BulkSMSNetworkError(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise BulkSMSNetworkError(f"Request error: {str(e)}")

    def _handle_api_error(self, error_code: int, response_data: Dict) -> None:
        """Handle specific API errors based on error codes."""
        # Authentication/Authorization errors
        if error_code in [1011, 1032]:
            raise BulkSMSAuthenticationError.from_response(response_data)

        # Balance related errors
        elif error_code in [1006, 1007]:
            raise BulkSMSBalanceError.from_response(response_data)

        # Invalid number errors
        elif error_code == 1001:
            raise BulkSMSInvalidNumberError.from_response(response_data)

        # Configuration/setup errors
        elif error_code in [1002, 1003, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020, 1021, 1031]:
            raise BulkSMSConfigurationError.from_response(response_data)

        # General API errors
        else:
            raise BulkSMSAPIError.from_response(response_data)

    def send_sms(
        self,
        phone_numbers: Union[str, List[str]],
        message: str,
        sender_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send SMS to one or multiple recipients (One-to-Many).

        Args:
            phone_numbers: Single phone number or list of phone numbers
            message: SMS message content
            sender_id: Sender ID (uses default if not provided)

        Returns:
            API response data

        Raises:
            BulkSMSValidationError: If validation fails
            BulkSMSAPIError: If API returns an error
        """
        # Validate inputs
        validate_message(message)

        # Use provided sender_id or default
        sender_id = sender_id or self.sender_id
        validate_sender_id(sender_id)

        # Process phone numbers
        if isinstance(phone_numbers, str):
            phone_numbers = [phone_numbers]

        # Validate and format phone numbers
        formatted_numbers = []
        for number in phone_numbers:
            validate_phone_number(number)
            formatted_numbers.append(format_phone_number(number))

        # Join phone numbers with comma
        numbers_str = ",".join(formatted_numbers)

        # Prepare request data
        data = {
            "api_key": self.api_key,
            "senderid": sender_id,
            "number": numbers_str,
            "message": message,
        }

        logger.info(f"Sending SMS to {len(formatted_numbers)} recipients")

        # Make API request
        return self._make_request("POST", self.SMS_ENDPOINT, data=data)

    def send_bulk_sms(
        self,
        messages: List[Dict[str, str]],
        sender_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send different SMS messages to different recipients (Many-to-Many).

        Args:
            messages: List of dictionaries with 'to' and 'message' keys
                     Example: [{'to': '8801712345678', 'message': 'Hello John'}, ...]
            sender_id: Sender ID (uses default if not provided)

        Returns:
            API response data

        Raises:
            BulkSMSValidationError: If validation fails
            BulkSMSAPIError: If API returns an error
        """
        if not messages:
            raise BulkSMSValidationError("Messages list cannot be empty")

        # Use provided sender_id or default
        sender_id = sender_id or self.sender_id
        validate_sender_id(sender_id)

        # Validate and format message data
        formatted_messages = []
        for msg_data in messages:
            if not isinstance(msg_data, dict) or 'to' not in msg_data or 'message' not in msg_data:
                raise BulkSMSValidationError(
                    "Each message must be a dictionary with 'to' and 'message' keys"
                )

            phone_number = msg_data['to']
            message = msg_data['message']

            validate_phone_number(phone_number)
            validate_message(message)

            formatted_messages.append({
                "to": format_phone_number(phone_number),
                "message": message,
            })

        # Prepare request data
        data = {
            "api_key": self.api_key,
            "senderid": sender_id,
            "messages": json.dumps(formatted_messages),
        }

        logger.info(f"Sending bulk SMS to {len(formatted_messages)} recipients")

        # Make API request
        return self._make_request("POST", self.SMS_MANY_ENDPOINT, data=data)

    def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance.

        Returns:
            API response with balance information

        Raises:
            BulkSMSAPIError: If API returns an error
        """
        params = {"api_key": self.api_key}

        logger.info("Checking account balance")

        return self._make_request("GET", self.BALANCE_ENDPOINT, params=params)

    def send_otp(
        self,
        phone_number: str,
        otp_code: str,
        brand_name: str = "Your Company",
        sender_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send OTP message with proper formatting.

        Args:
            phone_number: Recipient phone number
            otp_code: OTP code to send
            brand_name: Company/brand name
            sender_id: Sender ID (uses default if not provided)

        Returns:
            API response data
        """
        # Format OTP message as required by BulkSMSBD
        message = f"Your {brand_name} OTP is {otp_code}"

        return self.send_sms(phone_number, message, sender_id)

    def test_connection(self) -> bool:
        """
        Test API connection and credentials.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.get_balance()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
