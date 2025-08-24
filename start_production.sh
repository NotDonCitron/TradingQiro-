#!/bin/bash
# Production Startup Script
# Verwendet saubere Konfiguration ohne Debug-Nachrichten

echo "🚀 Starting Trading Bot in PRODUCTION MODE"
echo "============================================"
echo "✅ Only pure trading signals will be forwarded"
echo "❌ No debug messages, no status updates"
echo "❌ No pipeline notifications"
echo "✅ Clean Cornix-compatible signals only"
echo ""

# Verwende Production Environment
export NODE_ENV=production
cp .env.production .env

# Stelle sicher, dass nur relevante Signale durchkommen
export LOG_LEVEL=ERROR
export DEBUG=false
export SIGNAL_DEBUG=false
export ERROR_REPORTING=false
export STATUS_MESSAGES=false

echo "📊 Configuration loaded:"
echo "  - Signal Debug: DISABLED"
echo "  - Error Reporting: DISABLED" 
echo "  - Status Messages: DISABLED"
echo "  - Log Level: ERROR only"
echo ""

echo "🌐 Starting server..."
python src/main.py

echo ""
echo "✅ Production Mode: Nur reine Trading-Signale werden weitergeleitet!"
echo "✅ Keine Debug-Nachrichten mehr!"
echo "✅ Bereit für öffentliche Gruppe!"