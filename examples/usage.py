from bulksms.client import BulkSMSClient

# Initialize client
client = BulkSMSClient()

# Send single SMS
response = client.send_sms('01712345678', 'Hello World!')

# Send to multiple recipients
response = client.send_sms(
    ['01712345678', '01812345678'], 
    'Hello everyone!'
)

# Send bulk with different messages
messages = [
    {'to': '01712345678', 'message': 'Hello John'},
    {'to': '01812345678', 'message': 'Hello Jane'},
]
response = client.send_bulk_sms(messages)

# Send OTP
response = client.send_otp('01712345678', '123456', 'MyApp')

# Check balance
balance = client.get_balance()
