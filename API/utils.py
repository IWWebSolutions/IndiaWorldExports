
import requests
import random

def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_otp(mobile, otp):
    """Send OTP via SMS using Fast2SMS API."""
    api_key = "kNDx9q6LjGcJz02TMmKoVuYfSrCQZByiOH4nAP7t1X8v5REeWIoQF9cdXYrgRs1VIt5phCKBTkU67ezy"  # Replace with your API key
    url = "https://www.fast2sms.com/dev/bulkV2"

    payload = {
        "route": "otp",
        "message": f"Your OTP code is {otp} , please use this code login proccess. do not share this code to anyone, IndiaWorldExports",
        "language": "english",
        "flash": 0,
        "numbers": mobile
    }

    headers = {
        "authorization": api_key,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()
