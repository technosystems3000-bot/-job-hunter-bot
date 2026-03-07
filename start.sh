#!/bin/bash

# ============================================
# Global Job Hunter AI — Auto Setup & Launch
# ============================================

echo ""
echo "============================================"
echo "  Global Job Hunter AI — Setup & Launch"
echo "============================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    echo ""
    echo "To install Python 3 on MacBook:"
    echo "  1. Open this link: https://www.python.org/downloads/"
    echo "  2. Download and install the latest Python 3"
    echo "  3. After installation, run this script again"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "✅ Found $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment."
        echo "Try running: xcode-select --install"
        exit 1
    fi
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip -q 2>&1 | grep -v "already satisfied"
pip install -r requirements.txt -q 2>&1 | grep -v "already satisfied"

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    exit 1
fi
echo "✅ All dependencies installed"

# Check .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "❌ .env file not found!"
    echo "Creating .env from template..."
    cp .env.example .env
    echo "Please edit .env file and add your tokens."
    echo "Then run this script again."
    exit 1
fi

# Verify tokens are set
source <(grep -v '^#' .env | sed 's/^/export /')

if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
    echo ""
    echo "❌ BOT_TOKEN is not set in .env file!"
    echo "Please edit .env and add your Telegram bot token."
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo ""
    echo "❌ OPENAI_API_KEY is not set in .env file!"
    echo "Please edit .env and add your OpenAI API key."
    exit 1
fi

echo "✅ Tokens loaded from .env"

# Launch the bot
echo ""
echo "============================================"
echo "  🚀 Starting the bot..."
echo "============================================"
echo ""
echo "The bot is now running!"
echo "Open Telegram and send /start to your bot."
echo ""
echo "To stop the bot, press Ctrl+C"
echo ""

python3 bot.py
