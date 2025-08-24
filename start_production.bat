@echo off
REM Production Startup Script für Windows
REM Verwendet saubere Konfiguration ohne Debug-Nachrichten

echo 🚀 Starting Trading Bot in PRODUCTION MODE
echo ============================================
echo ✅ Only pure trading signals will be forwarded
echo ❌ No debug messages, no status updates  
echo ❌ No pipeline notifications
echo ✅ Clean Cornix-compatible signals only
echo.

REM Verwende Production Environment
set NODE_ENV=production
copy .env.production .env

REM Stelle sicher, dass nur relevante Signale durchkommen
set LOG_LEVEL=ERROR
set DEBUG=false
set SIGNAL_DEBUG=false
set ERROR_REPORTING=false
set STATUS_MESSAGES=false

echo 📊 Configuration loaded:
echo   - Signal Debug: DISABLED
echo   - Error Reporting: DISABLED
echo   - Status Messages: DISABLED
echo   - Log Level: ERROR only
echo.

echo 🌐 Starting server...
python src/main.py

echo.
echo ✅ Production Mode: Nur reine Trading-Signale werden weitergeleitet!
echo ✅ Keine Debug-Nachrichten mehr!
echo ✅ Bereit für öffentliche Gruppe!