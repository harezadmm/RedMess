#!/bin/bash
# RedMess - One-Click Installation Script
# Usage: curl -sSL https://raw.githubusercontent.com/harezadmm/RedMess/main/install.sh | bash

set -e

echo "🔥 RedMess Hermes Agent - One-Click Installer"
echo "=============================================="
echo ""

# Check OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "✓ OS: Linux detected"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✓ OS: macOS detected"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install Python 3.8+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Python: $PYTHON_VERSION"

# Clone repo
echo ""
echo "📥 Cloning RedMess repository..."
git clone https://github.com/harezadmm/RedMess.git
cd RedMess

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Setup config
echo ""
echo "⚙️  Setting up configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your tokens:"
    echo "   - TELEGRAM_BOT_TOKEN=your_bot_token"
    echo "   - TELEGRAM_OWNER_ID=your_telegram_id"
    echo "   - AI_API_KEY=your_api_key"
fi

# Setup Hermes
echo ""
echo "🔧 Setting up Hermes Agent..."
hermes config set skills.external_dirs "['$(pwd)/skills']"

# Create launcher
cat > start_bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source .env
cd telegram_bot
python3 hermes_full_bot.py
EOF
chmod +x start_bot.sh

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file: nano .env"
echo "   2. Add your bot token and owner ID"
echo "   3. Start bot: ./start_bot.sh"
echo ""
echo "📚 Documentation: https://github.com/harezadmm/RedMess"
echo "🔥 GODMODE BRUTAL active for owner ID"
