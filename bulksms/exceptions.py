"""
Custom exceptions for Django BulkSMS BD package
"""


class BulkSMSError(Exception):
    """Base exception class for BulkSMS operations."""

    def __init__(self, message, error_code=None, response=None):
        self.message = message
        self.error_code = error_code
        self.response = response
        super().__init__(self.message)


class BulkSMSAPIError(BulkSMSError):
    """Exception raised for API-related errors."""

    # Error code mappings from BulkSMSBD.net API
    ERROR_CODES = {
        202: "SMS Submitted Successfully",
        1001: "Invalid Number",
        1002: "Sender ID not correct/sender ID is disabled",
        1003: "Please Required all fields/Contact Your System Administrator",
        1005: "Internal Error",
        1006: "Balance Validity Not Available",
        1007: "Balance Insufficient",
        1011: "User ID not found",
        1012: "Masking SMS must be sent in Bengali",
        1013: "Sender ID has not found Gateway by api key",
        1014: "Sender Type Name not found using this sender by api key",
        1015: "Sender ID has not found Any Valid Gateway by api key",
        1016: "Sender Type Name Active Price Info not found by this sender id",
        1017: "Sender Type Name Price Info not found by this sender id",
        1018: "The Owner of this (username) Account is disabled",
        1019: "The (sender type name) Price of this (username) Account is disabled",
        1020: "The parent of this account is not found",
        1021: "The parent active (sender type name) price of this account is not found",
        1031: "Your Account Not Verified, Please Contact Administrator",
        1032: "IP Not whitelisted",
    }

    def __init__(self, message=None, error_code=None, response=None):
        if error_code and error_code in self.ERROR_CODES:
            api_message = self.ERROR_CODES[error_code]
            message = f"{api_message} (Code: {error_code})"

        super().__init__(message, error_code, response)

    @classmethod
    def from_response(cls, response_data):
        """Create exception from API response."""
        error_code = response_data.get('code')
        message = response_data.get('message', 'Unknown API error')
        return cls(message=message, error_code=error_code, response=response_data)


class BulkSMSConfigurationError(BulkSMSError):
    """Exception raised for configuration-related errors."""
    pass


class BulkSMSValidationError(BulkSMSError):
    """Exception raised for validation errors."""
    pass


class BulkSMSNetworkError(BulkSMSError):
    """Exception raised for network-related errors."""
    pass


class BulkSMSTimeoutError(BulkSMSNetworkError):
    """Exception raised when API request times out."""
    pass


class BulkSMSAuthenticationError(BulkSMSAPIError):
    """Exception raised for authentication errors."""
    pass


class BulkSMSBalanceError(BulkSMSAPIError):
    """Exception raised when account has insufficient balance."""

    def __init__(self, message="Insufficient account balance", **kwargs):
        super().__init__(message, **kwargs)


class BulkSMSInvalidNumberError(BulkSMSAPIError):
    """Exception raised for invalid phone numbers."""

    def __init__(self, message="Invalid phone number format", **kwargs):
        super().__init__(message, **kwargs)
