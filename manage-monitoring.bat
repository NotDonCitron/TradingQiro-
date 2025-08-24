@echo off
setlocal enabledelayedexpansion

:menu
cls
echo ===============================================
echo    TRADING BOT - MONITORING MANAGEMENT
echo ===============================================
echo.
echo Verfügbare Aktionen:
echo.
echo 1. 🚀 Monitoring System starten
echo 2. ⏹️  Monitoring System stoppen
echo 3. 🔄 Monitoring System neustarten
echo 4. 📋 Live-Logs anzeigen
echo 5. 📊 Service-Status prüfen
echo 6. 🌐 Service-URLs anzeigen
echo 7. 🧹 System bereinigen (Container + Volumes)
echo 8. ❌ Beenden
echo.
set /p choice="Wähle eine Option (1-8): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto status
if "%choice%"=="6" goto urls
if "%choice%"=="7" goto cleanup
if "%choice%"=="8" goto exit

echo Ungültige Auswahl. Bitte versuche es erneut.
timeout /t 2 >nul
goto menu

:start
echo.
echo 🚀 Starte Monitoring System...
docker-compose -f docker-compose.monitoring.yml up -d
echo.
echo ✅ System gestartet!
timeout /t 3 >nul
goto menu

:stop
echo.
echo ⏹️  Stoppe Monitoring System...
docker-compose -f docker-compose.monitoring.yml down
echo.
echo ✅ System gestoppt!
timeout /t 3 >nul
goto menu

:restart
echo.
echo 🔄 Starte Monitoring System neu...
docker-compose -f docker-compose.monitoring.yml restart
echo.
echo ✅ System neugestartet!
timeout /t 3 >nul
goto menu

:logs
echo.
echo 📋 Live-Logs (Beenden mit Ctrl+C):
echo.
docker-compose -f docker-compose.monitoring.yml logs -f
echo.
pause
goto menu

:status
echo.
echo 📊 Service-Status:
echo ===============================================
docker-compose -f docker-compose.monitoring.yml ps
echo.
echo 🔍 Port-Status:
for %%p in (8080 3000 9090 9093 8081 3001) do (
    powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:%%p' -TimeoutSec 2 -UseBasicParsing; Write-Host '✅ Port %%p: Online (Status: ' $response.StatusCode ')' } catch { Write-Host '❌ Port %%p: Offline oder nicht erreichbar' }"
)
echo.
pause
goto menu

:urls
echo.
echo 🌐 SERVICE-URLS:
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
echo 🔧 Forwarder Status:      http://localhost:8080/forwarder/status
echo 🔍 Cryptet Status:        http://localhost:8080/cryptet/status
echo.
pause
goto menu

:cleanup
echo.
echo ⚠️  WARNUNG: Dies entfernt ALLE Container und Volumes!
echo ⚠️  Alle Monitoring-Daten gehen verloren!
echo.
set /p confirm="Bist du sicher? (j/N): "
if /i not "%confirm%"=="j" (
    echo Abgebrochen.
    timeout /t 2 >nul
    goto menu
)

echo.
echo 🧹 Bereinige Monitoring System...
docker-compose -f docker-compose.monitoring.yml down -v
docker system prune -f
echo.
echo ✅ System bereinigt!
timeout /t 3 >nul
goto menu

:exit
echo.
echo 👋 Auf Wiedersehen!
timeout /t 1 >nul
exit /b 0