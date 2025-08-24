@echo off
REM =============================================================================
REM DOCKER SERVICES STARTUP SCRIPT - WINDOWS
REM Startet Signal-Weiterleitung als separate Docker Services
REM =============================================================================

echo 🐳 DOCKER SERVICES - SIGNAL FORWARDING
echo ======================================
echo ✅ Redis Message Queue
echo ✅ Telegram Receiver Service
echo ✅ Signal Parser Service
echo ✅ Signal Forwarder Service
echo ✅ API Gateway ^& Health Monitor
echo.

REM Prüfe Docker
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker ist nicht installiert!
    pause
    exit /b 1
)

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Daemon läuft nicht!
    pause
    exit /b 1
)

REM Prüfe .env Datei
if not exist .env (
    echo ❌ .env Datei nicht gefunden!
    echo 💡 Erstelle .env mit:
    echo    TELEGRAM_API_ID=your_api_id
    echo    TELEGRAM_API_HASH=your_api_hash
    echo    TELEGRAM_BOT_TOKEN=your_bot_token
    echo    OWN_GROUP_CHAT_ID=your_group_id
    pause
    exit /b 1
)

echo 📊 Docker Status: ✅ Läuft
echo.

REM Stoppe alte Container
echo 🛑 Stoppe alte Services...
docker-compose -f docker-compose.services.yml down

REM Erstelle Verzeichnisse
if not exist services mkdir services
if not exist session_files mkdir session_files
if not exist logs mkdir logs
echo 📁 Verzeichnisse erstellt
echo.

REM Baue und starte Services
echo 🔨 Baue Docker Images...
docker-compose -f docker-compose.services.yml build --no-cache

if %errorlevel% neq 0 (
    echo ❌ Docker Build fehlgeschlagen!
    pause
    exit /b 1
)

echo 🚀 Starte Services...
docker-compose -f docker-compose.services.yml up -d

if %errorlevel% neq 0 (
    echo ❌ Service Start fehlgeschlagen!
    pause
    exit /b 1
)

REM Warte auf Services
echo ⏳ Warte auf Service-Start...
timeout /t 15 /nobreak >nul

echo.
echo ✅ SERVICES GESTARTET!
echo =====================
echo.
echo 📊 Service Status:
docker-compose -f docker-compose.services.yml ps
echo.
echo 🌐 Verfügbare Endpoints:
echo    • API Gateway: http://localhost:8080
echo    • Health Check: http://localhost:8080/health
echo    • Service Status: http://localhost:8080/services
echo    • Redis: localhost:6379
echo.
echo 📝 Nützliche Befehle:
echo    docker-compose -f docker-compose.services.yml logs -f                    # Live Logs
echo    docker-compose -f docker-compose.services.yml logs telegram-receiver     # Receiver Logs
echo    docker-compose -f docker-compose.services.yml logs signal-parser         # Parser Logs
echo    docker-compose -f docker-compose.services.yml logs signal-forwarder      # Forwarder Logs
echo    docker-compose -f docker-compose.services.yml restart                    # Neustart
echo    docker-compose -f docker-compose.services.yml down                       # Stoppen
echo.
echo 🎯 Signal-Weiterleitung läuft jetzt über Docker Services!

REM Zeige Live-Logs für 10 Sekunden
echo.
echo 📜 Live-Logs (ersten 10 Sekunden):
timeout /t 10 /nobreak >nul
docker-compose -f docker-compose.services.yml logs --tail=20

echo.
echo ✅ SETUP ABGESCHLOSSEN!
pause