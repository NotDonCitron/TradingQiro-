# 🐳 DOCKER 24/7 SETUP - TRADING BOT

## 🎯 ÜBERSICHT

Dein Trading Bot läuft jetzt in Docker für **kontinuierlichen 24/7 Betrieb** mit:
- ✅ Automatischen Restarts bei Problemen
- ✅ Health Monitoring 
- ✅ Resource Limits (verhindert Überlastung)
- ✅ Persistente Daten (Sessions, Logs)
- ✅ **Nur reine Trading-Signale** (keine Debug-Nachrichten)

---

## 🚀 QUICK START

### Windows:
```batch
# 1. Docker starten und Bot deployen
.\docker-start.bat

# 2. Bot verwalten (optional)
.\docker-manage.bat
```

### Linux/Mac:
```bash
# 1. Script ausführbar machen
chmod +x docker-start.sh

# 2. Docker starten und Bot deployen  
./docker-start.sh

# 3. Health Monitor starten (optional)
python3 health-monitor.py
```

---

## 📋 VORAUSSETZUNGEN

### 1. Docker Installation:
- **Windows:** [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux:** `sudo apt install docker.io docker-compose`
- **Mac:** [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 2. Konfiguration:
- `.env.production` mit deinen Telegram API Keys
- `cookies.txt` für Cryptet (wird automatisch erstellt)

---

## 🏗️ DOCKER FILES ERKLÄRT

### `Dockerfile.production`
- Optimiertes Python 3.11 Image
- Chrome/Chromium für Cryptet Scraping
- Security: Non-root User
- Health Checks integriert

### `docker-compose.production.yml`  
- **restart: unless-stopped** → Automatischer Neustart
- **Resource Limits** → Max 1GB RAM, 0.5 CPU
- **Health Checks** → Alle 30 Sekunden
- **Volume Mounts** → Persistente Daten
- **Logging** → Begrenzte Log-Dateien

---

## 🎛️ MANAGEMENT BEFEHLE

### Container Status:
```bash
docker-compose -f docker-compose.production.yml ps
```

### Live Logs anzeigen:
```bash
docker-compose -f docker-compose.production.yml logs -f
```

### Bot neu starten:
```bash
docker-compose -f docker-compose.production.yml restart
```

### Bot stoppen:
```bash
docker-compose -f docker-compose.production.yml down
```

### Container Update (nach Code-Änderungen):
```bash
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

---

## 📊 MONITORING

### Health Check URLs:
- **Health:** http://localhost:8080/health
- **Status:** http://localhost:8080/status  
- **Metrics:** http://localhost:8080/metrics

### Automatisches Monitoring:
```bash
# Startet Health Monitor (überwacht und startet neu bei Problemen)
python3 health-monitor.py
```

---

## 📁 VERZEICHNISSTRUKTUR

```
trading-bot/
├── Dockerfile.production          # Docker Image Definition
├── docker-compose.production.yml  # Container Orchestration
├── docker-start.bat/.sh          # Startup Scripts  
├── docker-manage.bat              # Management Tool (Windows)
├── health-monitor.py              # 24/7 Health Monitor
├── .env.production               # Production Environment
├── logs/                         # Persistent Logs
├── session_files/               # Telegram Sessions
└── cookies.txt                  # Cryptet Cookies
```

---

## 🔧 TROUBLESHOOTING

### Container startet nicht:
```bash
# Logs prüfen
docker-compose -f docker-compose.production.yml logs

# Container Status
docker-compose -f docker-compose.production.yml ps

# System aufräumen
docker system prune -f
```

### Bot reagiert nicht:
```bash
# Health Check manuell
curl http://localhost:8080/health

# Container neu starten
docker-compose -f docker-compose.production.yml restart
```

### Memory-Probleme:
```bash
# Resource-Nutzung prüfen
docker stats

# Container mit mehr RAM starten (in docker-compose.yml ändern):
# memory: 2G  # statt 1G
```

---

## ⚙️ PRODUCTION KONFIGURATION

### Environment Variablen (.env.production):
```env
# CORE CONFIGURATION
API_ID=your_api_id
API_HASH=your_api_hash
OWN_GROUP_CHAT_ID=-1002773853382

# PRODUCTION SETTINGS (keine Debug-Messages)
LOG_LEVEL=ERROR
DEBUG=false
SIGNAL_DEBUG=false
ERROR_REPORTING=false
STATUS_MESSAGES=false

# CRYPTET SETTINGS
CRYPTET_ENABLED=true
CRYPTET_HEADLESS=true
```

### Resource Limits:
```yaml
# In docker-compose.production.yml
deploy:
  resources:
    limits:
      memory: 1G      # Maximaler RAM
      cpus: '0.5'     # Maximale CPU
    reservations:
      memory: 256M    # Reservierter RAM
      cpus: '0.1'     # Reservierte CPU
```

---

## 🛡️ SICHERHEIT

### Docker Security:
- ✅ Non-root Container User
- ✅ Resource Limits gesetzt
- ✅ Nur notwendige Ports exposed
- ✅ Read-only wo möglich

### Network Security:
- Container läuft in isoliertem Netzwerk
- Nur Port 8080 nach außen exposed
- Interne Kommunikation über Docker Network

---

## 🎯 PRODUCTION CHECKLIST

### Vor dem Go-Live:
- [ ] `.env.production` mit echten API Keys
- [ ] Telegram Session erstellt und getestet
- [ ] `cookies.txt` für Cryptet vorhanden
- [ ] Docker läuft stabil 
- [ ] Health Checks funktionieren
- [ ] Nur Trading-Signale werden gesendet (keine Debug-Messages)

### Nach dem Start:
- [ ] Container Status: `docker-compose -f docker-compose.production.yml ps`
- [ ] Health Check: `curl http://localhost:8080/health`
- [ ] Erste Signale getestet
- [ ] Logs monitored: `docker-compose -f docker-compose.production.yml logs -f`

---

## 🎉 FERTIG!

**Dein Trading Bot läuft jetzt 24/7 in Docker!**

- ✅ Automatische Restarts bei Problemen
- ✅ Health Monitoring aktiv
- ✅ Nur reine Trading-Signale (keine Debug)
- ✅ Bereit für öffentliche Gruppe
- ✅ Resource-effizient und stabil

### Support:
- Logs: `docker-compose -f docker-compose.production.yml logs -f`
- Management: `.\docker-manage.bat` (Windows)
- Health Monitor: `python3 health-monitor.py`