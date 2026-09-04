#!/bin/bash
# RedMess x Hermes Full Bot Launcher
# Auto-load .env and start bot

cd /root/RedMess

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Verify token
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not found in .env"
    exit 1
fi

echo "🔥 Starting RedMess x Hermes Full Bot..."
echo "Token: ${TELEGRAM_BOT_TOKEN:0:20}..."
echo "Owner: $TELEGRAM_OWNER_ID"

cd telegram_bot
exec python3 hermes_full_bot.py
