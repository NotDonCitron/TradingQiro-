#!/bin/bash
# =============================================================================
# DOCKER 24/7 STARTUP SCRIPT - LINUX/MAC
# Startet den Trading Bot in Docker für kontinuierlichen Betrieb
# =============================================================================

echo "🐳 DOCKER TRADING BOT - 24/7 PRODUCTION MODE"
echo "==============================================="
echo "✅ Nur reine Trading-Signale werden weitergeleitet"
echo "✅ Automatischer Restart bei Problemen"
echo "✅ Health Monitoring aktiviert"
echo "✅ Resource Limits gesetzt"
echo ""

# Prüfe ob Docker läuft
if ! command -v docker &> /dev/null; then
    echo "❌ Docker ist nicht installiert!"
    echo "💡 Installiere Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker Daemon läuft nicht!"
    echo "💡 Starte Docker Service und versuche es erneut."
    exit 1
fi

echo "📊 Docker Status: ✅ Läuft"
echo ""

# Stoppe eventuell laufende Container
echo "🛑 Stoppe alte Container..."
docker-compose -f docker-compose.production.yml down

# Erstelle notwendige Verzeichnisse
mkdir -p logs session_files
echo "📁 Verzeichnisse erstellt: logs/, session_files/"
echo ""

# Überprüfe wichtige Dateien
if [ ! -f ".env.production" ]; then
    echo "⚠️  .env.production nicht gefunden!"
    if [ -f ".env.production.example" ]; then
        cp .env.production.example .env.production
        echo "✅ .env.production von Example kopiert"
    else
        echo "❌ Bitte erstelle .env.production mit deiner Konfiguration!"
        exit 1
    fi
fi

if [ ! -f "cookies.txt" ]; then
    echo "ℹ️  cookies.txt nicht gefunden - wird automatisch erstellt"
    touch cookies.txt
fi

echo "🔧 Konfiguration: ✅ Bereit"
echo ""

# Build und starte Container
echo "🏗️  Building Docker Image..."
docker-compose -f docker-compose.production.yml build --no-cache

if [ $? -ne 0 ]; then
    echo "❌ Docker Build fehlgeschlagen!"
    exit 1
fi

echo "🚀 Starte Trading Bot Container..."
docker-compose -f docker-compose.production.yml up -d

if [ $? -ne 0 ]; then
    echo "❌ Container Start fehlgeschlagen!"
    exit 1
fi

echo ""
echo "✅ TRADING BOT LÄUFT JETZT 24/7!"
echo "================================"
echo "🌐 Health Check: http://localhost:8080/health"
echo "📊 Status: http://localhost:8080/status"
echo "📈 Metrics: http://localhost:8080/metrics"
echo ""
echo "📋 NÜTZLICHE BEFEHLE:"
echo "  docker-compose -f docker-compose.production.yml logs -f    # Live Logs"
echo "  docker-compose -f docker-compose.production.yml ps         # Container Status"
echo "  docker-compose -f docker-compose.production.yml restart    # Neustart"
echo "  docker-compose -f docker-compose.production.yml down       # Stoppen"
echo ""
echo "🎯 Der Bot läuft jetzt dauerhaft und startet automatisch neu bei Problemen!"

# Zeige Live-Logs für 10 Sekunden
echo ""
echo "📜 Live-Logs (ersten 10 Sekunden):"
sleep 3
docker-compose -f docker-compose.production.yml logs --tail=20

echo ""
echo "✅ SETUP ABGESCHLOSSEN - Bot läuft im Hintergrund!"