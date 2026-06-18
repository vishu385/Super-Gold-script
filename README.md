# Super.com Elite OTP Attacker

This repository contains an Elite OTP SMS sender for Super.com that bypasses basic Cloudflare protections using TLS fingerprint randomization.

It includes two ways to run the attack:
1. **Telegram Bot (`tg_bot.py`)**: A multi-user isolated bot for remote execution.
2. **Terminal Script (`terminal_bot.py`)**: A direct command-line execution script.

## Setup Instructions

1. Clone the repository.
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

### Running via Terminal (No Telegram Needed)
If you want to run the script directly from your terminal, you must first configure the `config.json` file.
1. Add your target numbers and proxy list to `config.json`.
2. Ensure you have a text file with your proxies (e.g., `.txt`) in the format `IP:Port:User:Pass` on each line.
3. Run the script:
```bash
python terminal_bot.py
```

### Running via Telegram Bot
If you want to control the bot via Telegram:
1. Open `tg_bot.py` and replace `BOT_TOKEN` with your bot's token.
2. Run the script:
```bash
python tg_bot.py
```
*Note: If Telegram API is blocked in your country, you must run this script with a system-level VPN.*
