@echo off
echo ===============================================
echo    TRADING BOT - MONITORING STACK SETUP
echo ===============================================
echo.

:: Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker ist nicht verfügbar oder läuft nicht!
    echo 💡 Bitte starte Docker Desktop und versuche es erneut.
    pause
    exit /b 1
)

echo ✅ Docker ist verfügbar

:: Create necessary directories
echo 📁 Erstelle benötigte Verzeichnisse...
if not exist logs mkdir logs
if not exist monitoring\grafana\dashboards mkdir monitoring\grafana\dashboards
if not exist monitoring\grafana\datasources mkdir monitoring\grafana\datasources

:: Check if .env.production exists
if not exist .env.production (
    echo ⚠️  .env.production nicht gefunden!
    echo 📋 Kopiere .env.example zu .env.production...
    copy .env.example .env.production >nul
    echo ✅ .env.production erstellt
)

echo.
echo 🚀 Starte komplettes Monitoring-System...
echo.
echo 📊 Das System startet folgende Services:
echo    • Trading Bot (Port 8080)
echo    • Prometheus (Port 9090) 
echo    • Grafana (Port 3000)
echo    • Alertmanager (Port 9093)
echo    • cAdvisor (Port 8081)
echo    • Uptime Kuma (Port 3001)
echo.

:: Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up --build -d

if errorlevel 1 (
    echo ❌ Fehler beim Starten der Container!
    echo 📋 Prüfe die Logs mit: docker-compose -f docker-compose.monitoring.yml logs
    pause
    exit /b 1
)

echo.
echo ✅ Monitoring-System erfolgreich gestartet!
echo.
echo 🌐 ZUGRIFF AUF DIE SERVICES:
echo ===============================================
echo 📊 Grafana Dashboard:     http://localhost:3000
echo    └─ Login: admin / tradingbot123
echo.
echo 📈 Prometheus:            http://localhost:9090
echo 🚨 Alertmanager:          http://localhost:9093
echo 📊 cAdvisor (Container):  http://localhost:8081
echo 💚 Uptime Kuma:           http://localhost:3001
echo.
echo 🤖 TRADING BOT:
echo ===============================================
echo 🌐 Bot Status:            http://localhost:8080/status
echo 📊 Metrics:               http://localhost:8080/metrics
echo ❤️  Health Check:          http://localhost:8080/health
echo.

:: Wait a bit for services to start
echo ⏳ Warte auf vollständigen Start der Services...
timeout /t 15 /nobreak >nul

echo 🔍 Überprüfe Service-Status...

:: Check if services are responding
for %%s in (8080 3000 9090 9093) do (
    powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:%%s' -TimeoutSec 5 -UseBasicParsing | Out-Null; Write-Host '✅ Port %%s: Online' } catch { Write-Host '⚠️  Port %%s: Nicht erreichbar (noch startend...)' }"
)

echo.
echo 💡 NÜTZLICHE BEFEHLE:
echo ===============================================
echo 📋 Logs anzeigen:         docker-compose -f docker-compose.monitoring.yml logs -f
echo ⏹️  System stoppen:       docker-compose -f docker-compose.monitoring.yml down
echo 🔄 System neustarten:     docker-compose -f docker-compose.monitoring.yml restart
echo 🗑️  Alles entfernen:      docker-compose -f docker-compose.monitoring.yml down -v
echo.

echo 🎉 MONITORING-SETUP ABGESCHLOSSEN!
echo 📊 Öffne Grafana unter http://localhost:3000 für das Trading Dashboard
echo.
pause