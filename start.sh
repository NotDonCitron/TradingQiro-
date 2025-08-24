#!/bin/bash

# Trading Bot Startup Script
set -e

echo "🚀 Trading Bot Startup Script"
echo "=============================="

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker ist nicht installiert. Bitte installieren Sie Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose ist nicht installiert. Bitte installieren Sie Docker Compose."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env Datei nicht gefunden. Kopiere .env.example zu .env..."
    cp .env.example .env
    echo "📝 Bitte bearbeiten Sie die .env Datei mit Ihren API-Credentials:"
    echo "   - TELEGRAM_API_ID"
    echo "   - TELEGRAM_API_HASH" 
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - BINGX_API_KEY"
    echo "   - BINGX_SECRET_KEY"
    echo ""
    echo "💡 Nach der Konfiguration führen Sie dieses Script erneut aus."
    exit 0
fi

echo "✅ Alle Voraussetzungen erfüllt!"
echo ""

# Start services
echo "🐳 Starte Docker Services..."
docker-compose up -d

# Wait for database
echo "⏳ Warte auf Datenbank..."
sleep 10

# Run migrations
echo "🗄️  Führe Datenbank-Migrationen aus..."
docker-compose exec -T bot alembic upgrade head

echo ""
echo "🎉 Trading Bot erfolgreich gestartet!"
echo ""
echo "📊 Verfügbare Services:"
echo "   • Trading Bot: http://localhost:8080"
echo "   • Health Check: http://localhost:8080/health"
echo "   • Metrics: http://localhost:8080/metrics"
echo "   • Status: http://localhost:8080/status"
echo ""
echo "📝 Logs anzeigen:"
echo "   docker-compose logs -f bot"
echo ""
echo "🧪 Test Signal senden:"
echo "   curl -X POST http://localhost:8080/signal \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": \"BUY BTCUSDT 0.001\", \"metadata\": {\"source\": \"test\"}}'"
echo ""
echo "🛑 Services stoppen:"
echo "   docker-compose down"