#!/bin/bash
# =============================================================================
# DOCKER SERVICES STARTUP SCRIPT
# Startet Signal-Weiterleitung als separate Docker Services
# =============================================================================

echo "🐳 DOCKER SERVICES - SIGNAL FORWARDING"
echo "======================================"
echo "✅ Redis Message Queue"
echo "✅ Telegram Receiver Service"
echo "✅ Signal Parser Service"
echo "✅ Signal Forwarder Service"
echo "✅ API Gateway & Health Monitor"
echo ""

# Prüfe Voraussetzungen
if ! command -v docker &> /dev/null; then
    echo "❌ Docker ist nicht installiert!"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker Daemon läuft nicht!"
    exit 1
fi

# Prüfe .env Datei
if [ ! -f .env ]; then
    echo "❌ .env Datei nicht gefunden!"
    echo "💡 Erstelle .env mit:"
    echo "   TELEGRAM_API_ID=your_api_id"
    echo "   TELEGRAM_API_HASH=your_api_hash"  
    echo "   TELEGRAM_BOT_TOKEN=your_bot_token"
    echo "   OWN_GROUP_CHAT_ID=your_group_id"
    exit 1
fi

echo "📊 Docker Status: ✅ Läuft"
echo ""

# Stoppe alte Container
echo "🛑 Stoppe alte Services..."
docker-compose -f docker-compose.services.yml down

# Erstelle Verzeichnisse
mkdir -p services session_files logs
echo "📁 Verzeichnisse erstellt"
echo ""

# Baue und starte Services
echo "🔨 Baue Docker Images..."
docker-compose -f docker-compose.services.yml build --no-cache

if [ $? -ne 0 ]; then
    echo "❌ Docker Build fehlgeschlagen!"
    exit 1
fi

echo "🚀 Starte Services..."
docker-compose -f docker-compose.services.yml up -d

if [ $? -ne 0 ]; then
    echo "❌ Service Start fehlgeschlagen!"
    exit 1
fi

# Warte auf Services
echo "⏳ Warte auf Service-Start..."
sleep 15

echo ""
echo "✅ SERVICES GESTARTET!"
echo "====================="
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.services.yml ps
echo ""
echo "🌐 Verfügbare Endpoints:"
echo "   • API Gateway: http://localhost:8080"
echo "   • Health Check: http://localhost:8080/health"
echo "   • Service Status: http://localhost:8080/services"
echo "   • Redis: localhost:6379"
echo ""
echo "📝 Useful Commands:"
echo "   docker-compose -f docker-compose.services.yml logs -f                    # Live Logs"
echo "   docker-compose -f docker-compose.services.yml logs telegram-receiver     # Receiver Logs"
echo "   docker-compose -f docker-compose.services.yml logs signal-parser         # Parser Logs"
echo "   docker-compose -f docker-compose.services.yml logs signal-forwarder      # Forwarder Logs"
echo "   docker-compose -f docker-compose.services.yml restart                    # Neustart"
echo "   docker-compose -f docker-compose.services.yml down                       # Stoppen"
echo ""
echo "🎯 Signal-Weiterleitung läuft jetzt über Docker Services!"

# Zeige Live-Logs für 10 Sekunden
echo ""
echo "📜 Live-Logs (ersten 10 Sekunden):"
timeout 10 docker-compose -f docker-compose.services.yml logs -f