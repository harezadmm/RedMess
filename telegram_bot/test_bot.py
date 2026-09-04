#!/usr/bin/env python3
"""
Quick test script untuk verify bot commands
"""
import requests
import os
import sys

# Load token
with open('/root/RedMess/.env') as f:
    for line in f:
        if line.startswith('TELEGRAM_BOT_TOKEN='):
            TOKEN = line.split('=', 1)[1].strip()
            break

BOT_API = f"https://api.telegram.org/bot{TOKEN}"

# Get bot info
resp = requests.get(f"{BOT_API}/getMe")
data = resp.json()

if data.get('ok'):
    bot = data['result']
    print(f"✅ Bot Active!")
    print(f"   Username: @{bot['username']}")
    print(f"   Name: {bot['first_name']}")
    print(f"   ID: {bot['id']}")
    print()
    print("📱 Available Commands:")
    print("   /start - Welcome message")
    print("   /skills - List all skills")
    print("   /skill <name> - View skill details")
    print("   /memory - List memories")
    print("   /search <query> - Search memories")
    print("   /email <email> - Email OSINT")
    print("   /username <user> - Username OSINT")
    print("   /phone <number> - Phone OSINT")
    print("   /ip <address> - IP lookup")
    print("   /domain <domain> - WHOIS lookup")
    print()
    print("🔥 Test the bot: https://t.me/{}".format(bot['username']))
else:
    print("❌ Bot tidak bisa diakses!")
    print(data)
