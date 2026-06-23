import telebot
from telebot import types
import threading
import logging
from database import init_db, init_user, get_db, update_user
from super_attacker import attack_thread
from telebot import apihelper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fallback: Instead of applying it to telebot directly which causes SSL issues with api.telegram.org via HTTP proxies, 
# we rely on the system environment variables if the user has a VPN, or just direct if Telegram is actually accessible.

BOT_TOKEN = "8918306883:AAFBzMKxBTL119ig-Pha9qmSrBZHnXt1rbA"
bot = telebot.TeleBot(BOT_TOKEN)

# Clear any conflicting webhooks before starting polling
try:
    bot.remove_webhook()
except Exception:
    pass

# Initialize Database
init_db()

# Define Commands
commands = [
    types.BotCommand("start", "Start the bot & Initialize Profile"),
    types.BotCommand("add_number", "Add single/bulk numbers (+CC)"),
    types.BotCommand("add_proxy", "Add single/bulk proxies (IP:Port:User:Pass)"),
    types.BotCommand("clean_all_number", "Delete all your numbers"),
    types.BotCommand("clean_proxy", "Delete all your proxies"),
    types.BotCommand("set_limit", "Set OTP limit per number"),
    types.BotCommand("set_wait", "Set wait time between OTPs"),
    types.BotCommand("proxy_on_off", "Toggle proxy usage"),
    types.BotCommand("status", "Check your current setup"),
    types.BotCommand("start_attack", "Start the Elite Attack"),
    types.BotCommand("stop_attack", "Stop the current attack")
]

@bot.message_handler(commands=['start'])
def handle_start(message):
    init_user(message.chat.id)
    text = (
        "🤖 **Welcome to Elite Super.com OTP Bot** 🤖\n\n"
        "Your isolated profile has been created.\n"
        "Use the `/` menu to configure your settings and start the attack.\n\n"
        "To add numbers, use: `/add_number +911234567890 +1234567890`"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['add_number'])
def handle_add_number(message):
    user = init_user(message.chat.id)
    text = message.text.replace('/add_number', '').strip()
    
    if not text:
        bot.reply_to(message, "⚠️ Send numbers separated by space or newline.\nExample: `/add_number +917505702806 +1234567890`", parse_mode="Markdown")
        return
        
    new_numbers = text.split()
    added = 0
    for num in new_numbers:
        if num not in user["numbers"]:
            user["numbers"][num] = {"sent": 0}
            added += 1
            
    update_user(message.chat.id, user)
    bot.reply_to(message, f"✅ Successfully added {added} new number(s).\nTotal numbers in your list: {len(user['numbers'])}")

@bot.message_handler(commands=['add_proxy'])
def handle_add_proxy(message):
    user = init_user(message.chat.id)
    text = message.text.replace('/add_proxy', '').strip()
    
    if not text:
        bot.reply_to(message, "⚠️ Send proxies separated by space or newline.\nExample: `/add_proxy 12.34.56.78:8080:user:pass`", parse_mode="Markdown")
        return
        
    # Split by whitespace which handles both spaces and newlines
    new_proxies = text.split()
    added = 0
    for proxy in new_proxies:
        proxy = proxy.strip()
        if proxy and proxy not in user["proxies"]:
            user["proxies"].append(proxy)
            added += 1
            
    update_user(message.chat.id, user)
    bot.reply_to(message, f"✅ Successfully added {added} new proxy(s).\nTotal proxies in your list: {len(user['proxies'])}")

@bot.message_handler(commands=['clean_all_number'])
def handle_clean_numbers(message):
    user = init_user(message.chat.id)
    user["numbers"] = {}
    update_user(message.chat.id, user)
    bot.reply_to(message, "🗑️ All numbers have been deleted from your list.")

@bot.message_handler(commands=['clean_proxy'])
def handle_clean_proxies(message):
    user = init_user(message.chat.id)
    user["proxies"] = []
    update_user(message.chat.id, user)
    bot.reply_to(message, "🗑️ All proxies have been deleted from your list.")

@bot.message_handler(commands=['set_limit'])
def handle_set_limit(message):
    user = init_user(message.chat.id)
    try:
        limit = int(message.text.split()[1])
        if limit <= 0: raise ValueError
        user["config"]["limit"] = limit
        update_user(message.chat.id, user)
        bot.reply_to(message, f"⚙️ Limit set to {limit} OTPs per number.\nOnce a number hits this limit, it will be automatically removed from the queue.")
    except:
        bot.reply_to(message, "⚠️ Invalid format. Use: `/set_limit 10`", parse_mode="Markdown")

@bot.message_handler(commands=['set_wait'])
def handle_set_wait(message):
    user = init_user(message.chat.id)
    try:
        wait = int(message.text.split()[1])
        user["config"]["wait_time"] = wait
        update_user(message.chat.id, user)
        bot.reply_to(message, f"⏱️ Wait time set to {wait} seconds between OTPs.")
    except:
        bot.reply_to(message, "⚠️ Invalid format. Use: `/set_wait 5`", parse_mode="Markdown")

@bot.message_handler(commands=['proxy_on_off'])
def handle_proxy_toggle(message):
    user = init_user(message.chat.id)
    current = user["config"]["use_proxy"]
    user["config"]["use_proxy"] = not current
    update_user(message.chat.id, user)
    status = "ON 🟢" if user["config"]["use_proxy"] else "OFF 🔴"
    bot.reply_to(message, f"🔄 Proxy Usage is now {status}")

@bot.message_handler(commands=['status'])
def handle_status(message):
    user = init_user(message.chat.id)
    numbers_count = len(user["numbers"])
    proxy_count = len(user["proxies"])
    limit = user["config"]["limit"]
    wait = user["config"]["wait_time"]
    proxy_status = "ON 🟢" if user["config"]["use_proxy"] else "OFF 🔴"
    
    active_nums = sum(1 for data in user["numbers"].values() if data["sent"] < limit)
    
    text = (
        f"📊 **YOUR CURRENT SETUP** 📊\n\n"
        f"📱 Total Numbers: `{numbers_count}`\n"
        f"🎯 Active Targets (under limit): `{active_nums}`\n"
        f"🛡️ Total Proxies: `{proxy_count}`\n"
        f"⚙️ Limit Per Number: `{limit}`\n"
        f"⏱️ Wait Time: `{wait}s`\n"
        f"🌐 Proxy Usage: {proxy_status}\n\n"
        f"Use `/start_attack` to begin."
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['start_attack'])
def handle_start_attack(message):
    chat_id = message.chat.id
    user = init_user(chat_id)
    
    if user["config"]["is_attacking"]:
        bot.reply_to(message, "⚠️ Attack is already running! Use `/stop_attack` first.")
        return
        
    active_nums = sum(1 for data in user["numbers"].values() if data["sent"] < user["config"]["limit"])
    if active_nums == 0:
        bot.reply_to(message, "❌ You have no active numbers under the limit. Add numbers using `/add_number`.")
        return
        
    if user["config"]["use_proxy"] and len(user["proxies"]) == 0:
        bot.reply_to(message, "⚠️ Proxy usage is ON but your proxy list is empty!\nAdd proxies with `/add_proxy` or turn them off with `/proxy_on_off`.")
        return

    # Set status to attacking
    user["config"]["is_attacking"] = True
    update_user(chat_id, user)
    
    bot.reply_to(message, "🚀 **ELITE ATTACK STARTED** 🚀\nMulti-threading enabled. Monitoring limits...", parse_mode="Markdown")
    
    # Start attack in background thread so bot doesn't hang
    t = threading.Thread(target=attack_thread, args=(chat_id, bot))
    t.daemon = True
    t.start()

@bot.message_handler(commands=['stop_attack'])
def handle_stop_attack(message):
    user = init_user(message.chat.id)
    user["config"]["is_attacking"] = False
    update_user(message.chat.id, user)
    bot.reply_to(message, "🛑 Stopping attack... Please wait a moment for current requests to finish.")

# Run bot
try:
    logger.info("Trying to set bot commands...")
    bot.set_my_commands(commands)
    logger.info("Commands successfully set.")
except Exception as e:
    logger.warning(f"Failed to set bot commands: {e}")

import asyncio
from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is running!")

async def init_app():
    app = web.Application()
    app.router.add_get('/', handle)
    return app

def run_server():
    import os
    port = int(os.environ.get("PORT", 8080))
    app = asyncio.run(init_app())
    web.run_app(app, port=port)

# Run bot in a thread
def run_bot():
    try:
        logger.info("Starting Telegram Bot Polling...")
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Polling failed. Error: {e}")

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

# Start the web server in the main thread
logger.info("Starting Web Server...")
run_server()
