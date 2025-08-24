@echo off
REM =============================================================================
REM DOCKER 24/7 STARTUP SCRIPT - WINDOWS
REM Startet den Trading Bot in Docker für kontinuierlichen Betrieb
REM =============================================================================

echo 🐳 DOCKER TRADING BOT - 24/7 PRODUCTION MODE
echo ===============================================
echo ✅ Nur reine Trading-Signale werden weitergeleitet
echo ✅ Automatischer Restart bei Problemen
echo ✅ Health Monitoring aktiviert  
echo ✅ Resource Limits gesetzt
echo.

REM Prüfe ob Docker läuft
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker ist nicht gestartet oder nicht installiert!
    echo 💡 Bitte starte Docker Desktop und versuche es erneut.
    pause
    exit /b 1
)

echo 📊 Docker Status: ✅ Läuft
echo.

REM Stoppe eventuell laufende Container
echo 🛑 Stoppe alte Container...
docker-compose -f docker-compose.production.yml down

REM Erstelle notwendige Verzeichnisse
if not exist "logs" mkdir logs
if not exist "session_files" mkdir session_files

echo 📁 Verzeichnisse erstellt: logs/, session_files/
echo.

REM Überprüfe wichtige Dateien
if not exist ".env.production" (
    echo ⚠️  .env.production nicht gefunden! Kopiere von .env.production.example
    if exist ".env.production.example" (
        copy .env.production.example .env.production
    ) else (
        echo ❌ Bitte erstelle .env.production mit deiner Konfiguration!
        pause
        exit /b 1
    )
)

if not exist "cookies.txt" (
    echo ℹ️  cookies.txt nicht gefunden - wird automatisch erstellt
    echo. > cookies.txt
)

echo 🔧 Konfiguration: ✅ Bereit
echo.

REM Build und starte Container
echo 🏗️  Building Docker Image...
docker-compose -f docker-compose.production.yml build --no-cache

if %errorlevel% neq 0 (
    echo ❌ Docker Build fehlgeschlagen!
    pause
    exit /b 1
)

echo 🚀 Starte Trading Bot Container...
docker-compose -f docker-compose.production.yml up -d

if %errorlevel% neq 0 (
    echo ❌ Container Start fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo ✅ TRADING BOT LÄUFT JETZT 24/7!
echo ================================
echo 🌐 Health Check: http://localhost:8080/health
echo 📊 Status: http://localhost:8080/status  
echo 📈 Metrics: http://localhost:8080/metrics
echo.
echo 📋 NÜTZLICHE BEFEHLE:
echo   docker-compose -f docker-compose.production.yml logs -f    # Live Logs
echo   docker-compose -f docker-compose.production.yml ps         # Container Status  
echo   docker-compose -f docker-compose.production.yml restart    # Neustart
echo   docker-compose -f docker-compose.production.yml down       # Stoppen
echo.
echo 🎯 Der Bot läuft jetzt dauerhaft und startet automatisch neu bei Problemen!

REM Zeige Live-Logs für 10 Sekunden
echo 📜 Live-Logs (ersten 10 Sekunden):
timeout /t 3 >nul
docker-compose -f docker-compose.production.yml logs --tail=20

echo.
echo ✅ SETUP ABGESCHLOSSEN - Bot läuft im Hintergrund!
pause