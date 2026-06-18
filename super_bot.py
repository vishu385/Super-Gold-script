import uuid
import logging
from curl_cffi import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

def send_super_otp(phone_number):
    logger.info(f"Starting Super.com OTP flow for {phone_number}...")
    
    # Generate dynamic IDs so we don't use the same one every time
    device_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    
    # We use curl_cffi to bypass Cloudflare's basic TLS fingerprinting
    session = requests.Session(impersonate="chrome120")
    
    url = "https://www.super.com/snapcommerce/api/trpc/authentication.cognitoCreateUserOrLogIn"
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.super.com',
        'referer': 'https://www.super.com/',
        'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    }
    
    payload = {
        "body": {
            "request_id": request_id,
            "data": {
                "auth_contact_identifier": {
                    "brand": "ST",
                    "contact_type": "PHONE_NUMBER",
                    "contact_value": phone_number
                },
                "profile": {
                    "device_id": device_id,
                    "platform_data": {
                        "os": "Windows"
                    }
                }
            }
        },
        "queryParams": {}
    }
    
    try:
        # First do a GET request to the homepage to grab any initial cookies (like __cf_bm) if needed
        logger.info("Hitting homepage to get initial cookies...")
        session.get("https://www.super.com/", headers={'user-agent': headers['user-agent']})
        
        # Now send the actual POST request
        logger.info(f"Sending POST request to {url}...")
        response = session.post(url, headers=headers, json=payload)
        
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ SUCCESS: OTP request sent to Super.com!")
            logger.info(f"Response data: {response.json()}")
            return True
        else:
            logger.error(f"❌ Failed to send OTP. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        logger.error(f"Error during request: {e}")
        return False

if __name__ == "__main__":
    target_phone = "+917505702806"
    send_super_otp(target_phone)
