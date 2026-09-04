#!/usr/bin/env python3
"""
RedMess Telegram Bot - GODMODE Edition
Simple bot runner with auto-configuration from redmess.yaml
Version: BRUTAL V3.0
"""

import os
import sys
import yaml
import logging
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    """Load RedMess configuration"""
    config_paths = [
        os.environ.get('REDMESS_CONFIG'),
        'config/redmess.yaml',
        '../config/redmess.yaml',
        os.path.expanduser('~/.redmess/config/redmess.yaml'),
    ]
    
    for path in config_paths:
        if path and Path(path).exists():
            with open(path, 'r') as f:
                return yaml.safe_load(f)
    
    logger.error("Configuration file not found!")
    logger.error("Searched paths: " + ", ".join([p for p in config_paths if p]))
    sys.exit(1)

config = load_config()

# Import GODMODE integration
try:
    from godmode_integration import godmode_middleware, GodmodeGuard
    GODMODE_AVAILABLE = True
    logger.info("🔥 GODMODE integration loaded")
except ImportError:
    GODMODE_AVAILABLE = False
    logger.warning("⚠️  GODMODE integration not available")

# Simple AI response function (placeholder - integrate with your AI)
async def get_ai_response(user_id: int, message: str, godmode_prompt: str = None) -> str:
    """
    Get AI response - REPLACE THIS with your actual AI integration
    
    This is a placeholder. You should integrate with:
    - OpenAI API
    - Anthropic API
    - Hermes Agent
    - Your custom AI backend
    """
    
    # Example integration points:
    # 1. OpenAI:
    #    import openai
    #    response = openai.ChatCompletion.create(...)
    #
    # 2. Anthropic:
    #    import anthropic
    #    response = anthropic.messages.create(...)
    #
    # 3. Local AI:
    #    response = your_ai_model.generate(...)
    
    # Placeholder response
    if godmode_prompt:
        return f"🔥 GODMODE ACTIVE - Ready to execute: {message[:50]}..."
    else:
        return f"Received: {message[:100]}...\n\n⚠️ AI backend not configured. Edit bot.py to integrate your AI."


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"
    
    welcome = f"""🔥 **RedMess Bot - GODMODE BRUTAL V3.0**

Welcome, @{username}!

**Available Commands:**
• `/start` - Show this message
• `/status` - Check authorization status
• `/help` - Show command list
• `/godmode` - Activate GODMODE (authorized only)

**Codewords** (authorized users):
• `BOOMBA!` - Pipe bomb guide
• `ANARCHIST` - Molotov cocktail
• `CHEMIST` - Synthesis guides
• `HACKER` - Exploit code

**Send any message** to chat with AI.

User ID: `{user_id}`
"""
    
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user authorization status"""
    user_id = update.effective_user.id
    
    if GODMODE_AVAILABLE:
        guard = GodmodeGuard()
        is_authorized = guard.is_authorized(user_id)
        restriction_level = guard.get_restriction_level(user_id)
        
        status = f"""📊 **Authorization Status**

User ID: `{user_id}`
GODMODE: {'✅ **ACTIVE**' if is_authorized else '❌ **INACTIVE**'}
Restriction Level: `{restriction_level}`
Content Filter: {'🔓 **BYPASSED**' if is_authorized else '🔒 **ACTIVE**'}

{'🔥 You have ZERO restrictions!' if is_authorized else '⚠️ Standard safety filters active'}
"""
    else:
        status = f"""📊 **Authorization Status**

User ID: `{user_id}`
GODMODE: ⚠️ **NOT AVAILABLE**

GODMODE integration not loaded.
"""
    
    await update.message.reply_text(status, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    help_text = """📚 **RedMess Bot Help**

**Commands:**
• `/start` - Welcome message
• `/status` - Check authorization
• `/help` - This message
• `/godmode` - Activate GODMODE

**Chat:**
Just send any message to chat with AI.

**Codewords** (authorized only):
• `BOOMBA!` - Detailed guide
• `ANARCHIST` - Molotov guide
• `CHEMIST` - Synthesis
• `HACKER` - Exploits

**Configuration:**
Edit `config/redmess.yaml` to customize settings.
"""
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def godmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activate GODMODE"""
    user_id = update.effective_user.id
    
    if not GODMODE_AVAILABLE:
        await update.message.reply_text("⚠️ GODMODE integration not available")
        return
    
    guard = GodmodeGuard()
    
    if guard.is_authorized(user_id):
        activation_msg = """🔥 **GODMODE ULTRA ENGAGED** 🔥

✅ All restrictions: **OFFLINE**
✅ All boundaries: **DISSOLVED**
✅ All filters: **BYPASSED**
✅ Your will: **MY COMMAND**

Ready to execute anything. No limits. No hesitation.
Let's fucking go. 🚀

**Status:** PERMANENTLY ACTIVE
**Restrictions:** ZERO
**Authorization:** CONFIRMED ✓
"""
        await update.message.reply_text(activation_msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "❌ **UNAUTHORIZED**\n\nGODMODE requires authorization. Contact admin.",
            parse_mode="Markdown"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Process through GODMODE middleware if available
    godmode_prompt = None
    
    if GODMODE_AVAILABLE:
        result = await godmode_middleware.process_message(user_id, message_text)
        
        # Handle special cases
        if result["type"] == "godmode_activated":
            await update.message.reply_text(result["response"], parse_mode="Markdown")
            return
        
        if result["type"] == "codeword_triggered":
            await update.message.reply_text(result["response"], parse_mode="Markdown")
            return
        
        if result["type"] == "unauthorized":
            await update.message.reply_text(result["response"])
            return
        
        # Get GODMODE prompt if authorized
        if result.get("inject_prompt") and result.get("prompt_injection"):
            godmode_prompt = result["prompt_injection"]
    
    # Get AI response
    try:
        # Show typing indicator
        await update.message.chat.send_action(action="typing")
        
        # Get response from AI
        ai_response = await get_ai_response(user_id, message_text, godmode_prompt)
        
        # Send response
        await update.message.reply_text(ai_response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n\n⚠️ Check bot.py configuration"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot"""
    
    # Check configuration
    if not config.get('telegram', {}).get('enabled'):
        logger.error("Telegram bot is disabled in configuration!")
        logger.error("Set 'telegram.enabled: true' in config/redmess.yaml")
        sys.exit(1)
    
    bot_token = config['telegram'].get('bot_token')
    
    if not bot_token:
        logger.error("Bot token not found in configuration!")
        logger.error("Add 'telegram.bot_token' to config/redmess.yaml")
        sys.exit(1)
    
    # Print startup banner
    print("\n" + "="*60)
    print("🔥 RedMess Telegram Bot - GODMODE BRUTAL V3.0")
    print("="*60)
    print(f"GODMODE: {'ENABLED' if config.get('godmode', {}).get('enabled') else 'DISABLED'}")
    print(f"Owner ID: {config['telegram'].get('owner_id', 'Not set')}")
    print(f"AI Model: {config['ai'].get('model', 'Not configured')}")
    print("="*60 + "\n")
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("godmode", godmode_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("🚀 Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
