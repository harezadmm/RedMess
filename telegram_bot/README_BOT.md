# RedMess OSINT Bot

Telegram bot untuk OSINT toolkit dengan fitur lengkap.

## Features

- 🔍 **Email Lookup** - Holehe email enumeration
- 👤 **Username Tracker** - Sherlock username search across platforms
- 📱 **Phone Lookup** - PhoneInfoga phone number investigation
- 🌐 **IP Lookup** - IP geolocation and information
- 🔗 **Domain Lookup** - Domain WHOIS and DNS information

## Setup

### Requirements

```bash
pip install python-telegram-bot python-dotenv
```

### Installation

1. Clone repository:
```bash
git clone <your-repo-url>
cd RedMessBot
```

2. Set bot token:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

3. Run bot:
```bash
python3 redmess_bot.py
```

## Configuration

Edit token di line 26 atau set environment variable `TELEGRAM_BOT_TOKEN`.

```python
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN_HERE")
OWNER_ID = YOUR_TELEGRAM_USER_ID
```

## Usage

1. Start bot: `/start`
2. Pilih mode:
   - **Bypass Mode** - Eksekusi langsung tanpa konfirmasi
   - **Ask Mode** - Konfirmasi sebelum eksekusi

3. Commands:
   - `/email <email>` - Lookup email
   - `/username <username>` - Track username
   - `/phone <number>` - Lookup phone number
   - `/ip <ip_address>` - Lookup IP info
   - `/domain <domain>` - Lookup domain info

## Security

Bot ini untuk research dan educational purposes only. Owner ID wajib diset untuk keamanan.

## License

MIT License
