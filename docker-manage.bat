@echo off
REM =============================================================================
REM DOCKER MANAGEMENT SCRIPT - 24/7 TRADING BOT
REM Einfache Verwaltung des Docker Containers
REM =============================================================================

:menu
cls
echo 🐳 DOCKER TRADING BOT MANAGEMENT
echo ================================
echo.
echo 1) 📊 Status anzeigen
echo 2) 📜 Live Logs anzeigen
echo 3) 🔄 Bot neu starten
echo 4) 🛑 Bot stoppen
echo 5) 🚀 Bot starten
echo 6) 🏗️  Image neu builden
echo 7) 🧹 System aufräumen
echo 8) ❌ Beenden
echo.
set /p choice="Wähle eine Option (1-8): "

if "%choice%"=="1" goto status
if "%choice%"=="2" goto logs
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto stop
if "%choice%"=="5" goto start
if "%choice%"=="6" goto rebuild
if "%choice%"=="7" goto cleanup
if "%choice%"=="8" goto exit

echo ❌ Ungültige Auswahl!
timeout /t 2 >nul
goto menu

:status
echo 📊 CONTAINER STATUS:
echo ===================
docker-compose -f docker-compose.production.yml ps
echo.
echo 🌐 HEALTH CHECKS:
curl -s http://localhost:8080/health 2>nul || echo "❌ Bot nicht erreichbar"
curl -s http://localhost:8080/status 2>nul || echo "❌ Status nicht verfügbar"
echo.
pause
goto menu

:logs
echo 📜 LIVE LOGS (Ctrl+C zum Beenden):
echo ===================================
docker-compose -f docker-compose.production.yml logs -f
goto menu

:restart
echo 🔄 BOT NEUSTART...
docker-compose -f docker-compose.production.yml restart
echo ✅ Bot wurde neu gestartet!
timeout /t 3 >nul
goto menu

:stop
echo 🛑 BOT STOPPEN...
docker-compose -f docker-compose.production.yml down
echo ✅ Bot wurde gestoppt!
timeout /t 2 >nul
goto menu

:start
echo 🚀 BOT STARTEN...
docker-compose -f docker-compose.production.yml up -d
echo ✅ Bot wurde gestartet!
timeout /t 3 >nul
goto menu

:rebuild
echo 🏗️  IMAGE NEU BUILDEN...
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
echo ✅ Image wurde neu erstellt und Bot gestartet!
timeout /t 3 >nul
goto menu

:cleanup
echo 🧹 SYSTEM AUFRÄUMEN...
echo Lösche ungenutzte Docker Images und Container...
docker system prune -f
echo ✅ System wurde aufgeräumt!
timeout /t 2 >nul
goto menu

:exit
echo 👋 Auf Wiedersehen!
exit /b 0