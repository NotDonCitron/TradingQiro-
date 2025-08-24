#!/bin/bash

echo "==============================================="
echo "    TRADING BOT - MONITORING STACK SETUP"
echo "==============================================="
echo

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker ist nicht verfügbar oder läuft nicht!"
    echo "💡 Bitte starte Docker und versuche es erneut."
    exit 1
fi

echo "✅ Docker ist verfügbar"

# Create necessary directories
echo "📁 Erstelle benötigte Verzeichnisse..."
mkdir -p logs
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "⚠️  .env.production nicht gefunden!"
    echo "📋 Kopiere .env.example zu .env.production..."
    cp .env.example .env.production
    echo "✅ .env.production erstellt"
fi

echo
echo "🚀 Starte komplettes Monitoring-System..."
echo
echo "📊 Das System startet folgende Services:"
echo "   • Trading Bot (Port 8080)"
echo "   • Prometheus (Port 9090)" 
echo "   • Grafana (Port 3000)"
echo "   • Alertmanager (Port 9093)"
echo "   • cAdvisor (Port 8081)"
echo "   • Uptime Kuma (Port 3001)"
echo

# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up --build -d

if [ $? -ne 0 ]; then
    echo "❌ Fehler beim Starten der Container!"
    echo "📋 Prüfe die Logs mit: docker-compose -f docker-compose.monitoring.yml logs"
    exit 1
fi

echo
echo "✅ Monitoring-System erfolgreich gestartet!"
echo
echo "🌐 ZUGRIFF AUF DIE SERVICES:"
echo "==============================================="
echo "📊 Grafana Dashboard:     http://localhost:3000"
echo "   └─ Login: admin / tradingbot123"
echo
echo "📈 Prometheus:            http://localhost:9090"
echo "🚨 Alertmanager:          http://localhost:9093"
echo "📊 cAdvisor (Container):  http://localhost:8081"
echo "💚 Uptime Kuma:           http://localhost:3001"
echo
echo "🤖 TRADING BOT:"
echo "==============================================="
echo "🌐 Bot Status:            http://localhost:8080/status"
echo "📊 Metrics:               http://localhost:8080/metrics"
echo "❤️  Health Check:          http://localhost:8080/health"
echo

# Wait a bit for services to start
echo "⏳ Warte auf vollständigen Start der Services..."
sleep 15

echo "🔍 Überprüfe Service-Status..."

# Check if services are responding
for port in 8080 3000 9090 9093; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port" | grep -q "200\|302\|401"; then
        echo "✅ Port $port: Online"
    else
        echo "⚠️  Port $port: Nicht erreichbar (noch startend...)"
    fi
done

echo
echo "💡 NÜTZLICHE BEFEHLE:"
echo "==============================================="
echo "📋 Logs anzeigen:         docker-compose -f docker-compose.monitoring.yml logs -f"
echo "⏹️  System stoppen:       docker-compose -f docker-compose.monitoring.yml down"
echo "🔄 System neustarten:     docker-compose -f docker-compose.monitoring.yml restart"
echo "🗑️  Alles entfernen:      docker-compose -f docker-compose.monitoring.yml down -v"
echo

echo "🎉 MONITORING-SETUP ABGESCHLOSSEN!"
echo "📊 Öffne Grafana unter http://localhost:3000 für das Trading Dashboard"
echo