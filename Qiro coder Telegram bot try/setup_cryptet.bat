@echo off
REM Setup script for Cryptet Signal Automation System (Windows)

echo 🤖 Setting up Cryptet Signal Automation System...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.11+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed. Please install pip first.
    pause
    exit /b 1
)

echo ✅ Python and pip found

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo ✅ Dependencies installed successfully
) else (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Check if Chrome is installed
echo 🌐 Checking for Chrome browser...
where chrome >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Chrome found
) else (
    echo ⚠️  Chrome not found. Please install Chrome browser.
    echo Download from: https://www.google.com/chrome/
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.cryptet.template .env
    echo ✅ .env file created. Please edit it with your configuration.
) else (
    echo ⚠️  .env file already exists. Please verify your configuration.
)

REM Check if cookies.txt exists
if not exist cookies.txt (
    echo 🍪 cookies.txt not found. Please export your Cryptet cookies:
    echo    1. Log in to https://cryptet.com in your browser
    echo    2. Export cookies using a browser extension ^(e.g., 'cookies.txt'^)
    echo    3. Save the file as 'cookies.txt' in this directory
) else (
    echo ✅ cookies.txt found
)

REM Create logs directory
if not exist logs mkdir logs
echo ✅ Logs directory created

echo.
echo 🎉 Setup completed!
echo.
echo 📋 Next steps:
echo    1. Edit .env file with your configuration:
echo       - Add your Telegram API credentials
echo       - Set your OWN_GROUP_CHAT_ID
echo       - Configure other settings as needed
echo.
echo    2. Export Cryptet cookies:
echo       - Login to cryptet.com
echo       - Export cookies to cookies.txt
echo.
echo    3. Test the system:
echo       python src/main.py
echo.
echo    4. Use API endpoints:
echo       - GET /cryptet/status - Check system status
echo       - POST /cryptet/test - Test a Cryptet link
echo       - GET /health - Health check
echo.
echo 🚀 Your Cryptet automation system is ready!
pause