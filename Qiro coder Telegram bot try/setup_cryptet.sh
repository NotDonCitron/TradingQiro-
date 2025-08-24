#!/bin/bash
# Setup script for Cryptet Signal Automation System

echo "🤖 Setting up Cryptet Signal Automation System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ Python and pip found"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Install Chrome WebDriver (for Selenium)
echo "🌐 Setting up Chrome WebDriver..."

# Check if Chrome is installed
if command -v google-chrome &> /dev/null || command -v chromium-browser &> /dev/null; then
    echo "✅ Chrome/Chromium found"
else
    echo "⚠️  Chrome/Chromium not found. Please install Chrome or Chromium browser."
    echo "   Download from: https://www.google.com/chrome/"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.cryptet.template .env
    echo "✅ .env file created. Please edit it with your configuration."
else
    echo "⚠️  .env file already exists. Please verify your configuration."
fi

# Check if cookies.txt exists
if [ ! -f cookies.txt ]; then
    echo "🍪 cookies.txt not found. Please export your Cryptet cookies:"
    echo "   1. Log in to https://cryptet.com in your browser"
    echo "   2. Export cookies using a browser extension (e.g., 'cookies.txt')"
    echo "   3. Save the file as 'cookies.txt' in this directory"
else
    echo "✅ cookies.txt found"
fi

# Create logs directory
mkdir -p logs
echo "✅ Logs directory created"

echo ""
echo "🎉 Setup completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file with your configuration:"
echo "      - Add your Telegram API credentials"
echo "      - Set your OWN_GROUP_CHAT_ID"
echo "      - Configure other settings as needed"
echo ""
echo "   2. Export Cryptet cookies:"
echo "      - Login to cryptet.com"
echo "      - Export cookies to cookies.txt"
echo ""
echo "   3. Test the system:"
echo "      python3 src/main.py"
echo ""
echo "   4. Use API endpoints:"
echo "      - GET /cryptet/status - Check system status"
echo "      - POST /cryptet/test - Test a Cryptet link"
echo "      - GET /health - Health check"
echo ""
echo "🚀 Your Cryptet automation system is ready!"