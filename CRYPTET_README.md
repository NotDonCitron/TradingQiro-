# 🤖 Cryptet Signal Automation System

Ein automatisiertes System zur Verarbeitung von Cryptet-Signalen mit Browser-Automation, Cookie-basierter Authentifizierung und automatischer Weiterleitung an Ihre eigene Telegram-Gruppe.

## 🎯 Funktionen

### Hauptfeatures

- **Automatische Cryptet-Link Erkennung** in Telegram-Nachrichten
- **Browser-Automation** mit Selenium für Cryptet-Website Zugriff
- **Cookie-basierte Authentifizierung** mit Ihren gespeicherten Cryptet-Cookies
- **Signal-Parsing** und automatisches Hinzufügen von 50x Leverage
- **Automatische Weiterleitung** an Ihre eigene Telegram-Gruppe
- **P&L Monitoring** mit automatischem Signal-Schließen nach ~4h
- **Web-Dashboard** für Monitoring und Kontrolle

### Workflow

1. 📱 Cryptet-Link wird in Telegram gepostet
2. 🌐 Browser öffnet automatisch mit Ihren gespeicherten Cookies
3. 📊 Signal wird ausgelesen und mit 50x Leverage modifiziert
4. 📤 Modifiziertes Signal wird in Ihre eigene Telegram-Gruppe weitergeleitet
5. ⏰ Automatisches Schließen wenn Cryptet Gewinn/Verlust anzeigt

## 🚀 Installation

### Voraussetzungen

- Python 3.11+
- Chrome/Chromium Browser
- Telegram API Credentials
- Cryptet.com Account mit Cookies

### Schnelle Installation

#### Windows

```bash
# Setup ausführen
setup_cryptet.bat
```bash
#### Linux/Mac

```bash
# Setup ausführen
chmod +x setup_cryptet.sh
./setup_cryptet.sh
```bash
#### Manuelle Installation

```bash
# Dependencies installieren
pip install -r requirements.txt

# Konfiguration erstellen
cp .env.cryptet.template .env

# .env Datei bearbeiten
# cookies.txt von Cryptet exportieren
```bash
## ⚙️ Konfiguration

### 1. Environment Variables (.env)

```bash
# Telegram API Credentials
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Ihre eigene Telegram-Gruppe ID (wichtig!)
OWN_GROUP_CHAT_ID=-1001234567890

# Cryptet Einstellungen
CRYPTET_ENABLED=true
CRYPTET_COOKIES_FILE=cookies.txt
CRYPTET_HEADLESS=true
CRYPTET_DEFAULT_LEVERAGE=50
```bash
### 2. Cryptet Cookies exportieren

#### Option A: Browser Extension (Empfohlen)

1. Installieren Sie eine "cookies.txt" Browser-Extension
2. Loggen Sie sich bei <https://cryptet.com> ein
3. Exportieren Sie die Cookies als `cookies.txt`
4. Speichern Sie die Datei im Projektverzeichnis

#### Option B: Manuell aus Developer Tools

1. Öffnen Sie <https://cryptet.com> und loggen Sie sich ein
2. Drücken Sie F12 → Application → Cookies
3. Kopieren Sie alle cryptet.com Cookies
4. Erstellen Sie `cookies.txt` im Netscape-Format

### 3. Telegram Gruppe Chat ID finden

```bash
# Bot zu Ihrer Gruppe hinzufügen
# Nachricht in der Gruppe senden
# Logs prüfen für chat_id oder API verwenden:
curl "https://api.telegram.org/bot<BOT_TOKEN>/getUpdates"
```bash
## 🎮 Verwendung

### System starten

```bash
python src/main.py
```bash
### Web Dashboard

- **Status:** <http://localhost:8000/status>
- **Cryptet Status:** <http://localhost:8000/cryptet/status>
- **Health Check:** <http://localhost:8000/health>

### API Endpoints

#### Cryptet Status prüfen

```bash
GET /cryptet/status
```bash
#### Cryptet Link testen

```bash
POST /cryptet/test
{
    "url": "https://cryptet.com/signal/123456"
}
```bash
#### Signal manuell schließen

```bash
POST /cryptet/close/{signal_id}
{
    "reason": "manual close"
}
```bash
## 📊 Monitoring

### Aktive Signale überwachen

```bash
curl http://localhost:8000/cryptet/status
```bash
### Logs prüfen

```bash
tail -f logs/trading_bot.log
```bash
### Metrics (Prometheus)

```bash
curl http://localhost:8000/metrics
```bash
## 🔧 Fehlerbehebung

### Häufige Probleme

#### 1. Browser startet nicht

```bash
# Chrome/Chromium installieren
# WebDriver-Manager wird automatisch installiert
pip install webdriver-manager
```bash
#### 2. Cookies funktionieren nicht

```bash
# Cookies neu exportieren
# Prüfen ob cookies.txt im korrekten Netscape-Format ist
# Format: domain flag path secure expiry name value
```bash
#### 3. Telegram sendet nicht

```bash
# OWN_GROUP_CHAT_ID prüfen (muss negativ sein für Gruppen)
# Bot-Token prüfen
# Bot zu Gruppe hinzufügen und Admin-Rechte geben
```bash
#### 4. Signal wird nicht erkannt

```bash
# Cryptet URL prüfen
# Logs für Parsing-Fehler prüfen
# Test-Endpoint verwenden: POST /cryptet/test
```bash
### Debug-Modus

```bash
# Headless deaktivieren (Browser sichtbar)
CRYPTET_HEADLESS=false

# Log-Level erhöhen
LOG_LEVEL=DEBUG

# Einzelnen Link testen
curl -X POST http://localhost:8000/cryptet/test \
  -H "Content-Type: application/json" \
  -d '{"url": "https://cryptet.com/your-signal-link"}'
```bash
## 📁 Projektstruktur

```bash
src/
├── connectors/
│   ├── cryptet_scraper.py      # Web-Scraping mit Selenium
│   ├── telethon_connector.py   # Telegram Integration
│   └── bingx_client.py         # BingX API Client
├── core/
│   ├── cryptet_automation.py   # Hauptsteuerung
│   ├── cryptet_link_handler.py # Link-Verarbeitung
│   ├── cryptet_signal_parser.py# Signal-Formatierung
│   ├── cryptet_pnl_monitor.py  # P&L Überwachung
│   └── state_manager.py        # Datenbankmanagement
├── utils/
│   ├── cookie_parser.py        # Cookie-Konvertierung
│   ├── audit_logger.py         # Logging
│   └── metrics.py              # Prometheus Metrics
└── main.py                     # FastAPI Anwendung
```bash
## 🔐 Sicherheit

### Wichtige Sicherheitshinweise

- **Cookies:** Niemals `cookies.txt` in Git committen
- **API Keys:** Verwenden Sie `.env` für sensible Daten
- **Permissions:** Bot benötigt nur Lese-/Schreibrechte in Ihrer Gruppe
- **Network:** System läuft lokal, keine externen Services

### .gitignore erweitern

```bash
cookies.txt
.env
*.log
logs/
```bash
## 📈 Performance

### Optimierungen

- **Headless Browser:** Reduziert Ressourcenverbrauch
- **Connection Pooling:** Wiederverwendung von Browser-Sessions
- **Async Processing:** Parallele Signal-Verarbeitung
- **Smart Monitoring:** Nur aktive Signale überwachen

### Systemanforderungen

- **RAM:** 1GB (mit Headless Browser)
- **CPU:** Beliebig (auch Raspberry Pi)
- **Network:** Stabile Internetverbindung
- **Storage:** 100MB für Logs/Cache

## 🤝 Support

### Bei Problemen

1. Logs prüfen (`logs/trading_bot.log`)
2. Status-Endpoint aufrufen (`/cryptet/status`)
3. Test-Endpoint verwenden (`/cryptet/test`)
4. Debug-Modus aktivieren (`CRYPTET_HEADLESS=false`)

### Erweiterte Konfiguration

```bash
# Monitoring-Intervall anpassen (Sekunden)
CRYPTET_MONITOR_INTERVAL=300

# Maximale Überwachungszeit (Stunden)
CRYPTET_MAX_MONITOR_HOURS=6

# Browser-Timeout (Sekunden)
CRYPTET_BROWSER_TIMEOUT=10
```bash
## 🎉 Das wars

Ihr Cryptet Signal Automation System ist einsatzbereit!

**Workflow Zusammenfassung:**

1. 📱 Cryptet-Link in Telegram →
2. 🤖 Automatische Verarbeitung →
3. 📤 Signal an Ihre Gruppe →
4. ⏰ Automatisches Schließen

**Viel Erfolg beim Trading! 🚀📈**
