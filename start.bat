@echo off
setlocal enabledelayedexpansion

echo.
echo 🚀 Trading Bot Startup Script
echo ==============================

REM Check if docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker ist nicht installiert. Bitte installieren Sie Docker: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Check if docker-compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose ist nicht installiert. Bitte installieren Sie Docker Compose.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env Datei nicht gefunden. Kopiere .env.example zu .env...
    copy .env.example .env
    echo.
    echo 📝 Bitte bearbeiten Sie die .env Datei mit Ihren API-Credentials:
    echo    - TELEGRAM_API_ID
    echo    - TELEGRAM_API_HASH
    echo    - TELEGRAM_BOT_TOKEN
    echo    - BINGX_API_KEY
    echo    - BINGX_SECRET_KEY
    echo.
    echo 💡 Nach der Konfiguration führen Sie dieses Script erneut aus.
    pause
    exit /b 0
)

echo ✅ Alle Voraussetzungen erfüllt!
echo.

REM Start services
echo 🐳 Starte Docker Services...
docker-compose up -d

REM Wait for database
echo ⏳ Warte auf Datenbank...
timeout /t 10 /nobreak >nul

REM Run migrations
echo 🗄️  Führe Datenbank-Migrationen aus...
docker-compose exec -T bot alembic upgrade head

echo.
echo 🎉 Trading Bot erfolgreich gestartet!
echo.
echo 📊 Verfügbare Services:
echo    • Trading Bot: http://localhost:8080
echo    • Health Check: http://localhost:8080/health
echo    • Metrics: http://localhost:8080/metrics
echo    • Status: http://localhost:8080/status
echo.
echo 📝 Logs anzeigen:
echo    docker-compose logs -f bot
echo.
echo 🧪 Test Signal senden:
echo    curl -X POST http://localhost:8080/signal ^
echo      -H "Content-Type: application/json" ^
echo      -d "{\"message\": \"BUY BTCUSDT 0.001\", \"metadata\": {\"source\": \"test\"}}"
echo.
echo 🛑 Services stoppen:
echo    docker-compose down
echo.
pause