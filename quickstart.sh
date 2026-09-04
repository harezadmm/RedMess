#!/bin/bash
# RedMess Quick Start Script

echo "🔥 RedMess BRUTAL MOD - Quick Start"
echo ""

# Check if already installed
if command -v redmess &> /dev/null; then
    echo "✅ RedMess is already installed!"
    echo ""
    echo "Starting RedMess..."
    redmess
    exit 0
fi

# Check if we're in RedMess directory
if [ ! -f "install.sh" ]; then
    echo "📦 Downloading RedMess..."
    
    if ! command -v git &> /dev/null; then
        echo "❌ Git not found. Please install git first."
        exit 1
    fi
    
    git clone https://github.com/harezadmm/RedMess.git
    cd RedMess
fi

# Run installer
echo "🚀 Running installer..."
chmod +x install.sh
./install.sh

echo ""
echo "✅ Installation complete!"
echo ""
echo "Start RedMess with: redmess"
