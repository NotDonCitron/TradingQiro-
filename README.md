# Asynchroner Signal-Trading-Bot (Telegram -> BingX)

## Übersicht

Ein asynchroner Trading-Bot, der Signale von Telegram empfängt, Trades auf BingX ausführt und seinen Zustand in einer PostgreSQL-Datenbank verwaltet. Das System ist für 24/7-Betrieb mit 99.9% Verfügbarkeit ausgelegt.

## Technologie-Stack

- **Backend**: Python 3.11+ mit asyncio
- **Telegram**: Telethon für Nachrichtenempfang
- **Exchange**: BingX REST API mit Retry-Logik
- **Datenbank**: PostgreSQL mit SQLAlchemy (async) & Alembic
- **HTTP**: FastAPI für Health-Checks und Metriken
- **Monitoring**: Prometheus Metriken & strukturierte Logs
- **Deployment**: Docker, Kubernetes mit Helm Charts
- **CI/CD**: GitHub Actions mit GHCR

## Architektur

### High-Level Komponenten

```mermaid
graph TB
    TG[Telegram] --> TC[Telethon Connector]
    TC --> SM[State Manager]
    SM --> TE[Task Executor]
    TE --> BX[BingX Client]
    SM --> DB[(PostgreSQL)]
    RJ[Reconciliation Job] --> SM
    RJ --> BX
    SM --> AL[Audit Logger]
    TE --> AL
    RJ --> AL
    MS[Metrics Server] --> PM[Prometheus]
```bash
### Datenfluss

1. **Empfang**: Telethon empfängt Telegram-Signale
2. **Verarbeitung**: Signal wird geparst und Order mit Status `PENDING` erstellt
3. **Ausführung**: Task Executor sendet Order an BingX (Status: `SUBMITTED`)
4. **Abgleich**: Reconciliation Job prüft finalen Status (`FILLED`, `CANCELLED`, etc.)
5. **Monitoring**: Alle Aktionen werden als Metriken und Logs erfasst

## Lokales Setup

### Voraussetzungen

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (optional, wird über Docker bereitgestellt)

### 1. Repository klonen

```bash
git clone <repository-url>
cd trading-bot
```bash
### 2. Umgebungsvariablen konfigurieren

Erstellen Sie eine `.env`-Datei:

```bash
# Telegram API Credentials
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token

# BingX API Credentials
BINGX_API_KEY=your_api_key
BINGX_SECRET_KEY=your_secret_key

# Configuration
TRADING_ENABLED=false
BINGX_TESTNET=true
LOG_LEVEL=INFO
```bash
### 3. Mit Docker Compose starten

```bash
# Services starten
docker-compose up --build

# In separatem Terminal: Datenbank migrieren
docker-compose exec bot alembic upgrade head
```bash
### 4. Tests ausführen

```bash
# Unit Tests
docker-compose exec bot pytest

# Mit Coverage
docker-compose exec bot pytest --cov=src --cov-report=html
```bash
### 5. Manuelles Signal testen

```bash
curl -X POST http://localhost:8080/signal \
  -H "Content-Type: application/json" \
  -d '{"message": "BUY BTCUSDT 0.001", "metadata": {"source": "test"}}'
```bash
## Endpoints

### Health Checks

- `GET /health` - Liveness Probe
- `GET /ready` - Readiness Probe
- `GET /status` - Detaillierter Status

### Monitoring

- `GET /metrics` - Prometheus Metriken
- Port 9090 - Dedizierter Metriken-Port

### Testing

- `POST /signal` - Manuelles Signal senden

## Signal Format

Der Bot versteht folgende Signal-Formate:

```bash
BUY BTCUSDT 0.1
SELL ETHUSDT 0.5
```bash
- **Action**: `BUY` oder `SELL`
- **Symbol**: Trading-Pair (z.B. `BTCUSDT`, `ETHUSDT`)
- **Quantity**: Menge als Dezimalzahl

## Deployment

### Kubernetes mit Helm

1. **Image bauen und pushen**:

```bash
docker build -t ghcr.io/myorg/trading-bot:latest .
docker push ghcr.io/myorg/trading-bot:latest
```bash
2. **Secrets erstellen**:

```bash
kubectl create secret generic trading-bot-secrets \
  --from-literal=telegram_api_id="$TELEGRAM_API_ID" \
  --from-literal=telegram_api_hash="$TELEGRAM_API_HASH" \
  --from-literal=telegram_bot_token="$TELEGRAM_BOT_TOKEN" \
  --from-literal=database_url="$DATABASE_URL" \
  --from-literal=bingx_api_key="$BINGX_API_KEY" \
  --from-literal=bingx_secret_key="$BINGX_SECRET_KEY"
```bash
3. **Mit Helm deployen**:

```bash
helm install trading-bot ./helm/trading-bot \
  --set image.tag=latest \
  --set env.TRADING_ENABLED=true
```bash
### CI/CD Pipeline

Die GitHub Actions Pipeline:

1. Führt Tests aus
2. Baut Docker Image
3. Pusht zu GitHub Container Registry
4. Verwendet Image-Tag: `${{ github.sha }}`

## Monitoring & Alerting

### Wichtige Metriken

- `orders_total` - Gesamtanzahl Orders
- `orders_failed_total` - Fehlgeschlagene Orders
- `signal_processing_duration_seconds` - Verarbeitungszeit
- `position_size` - Aktuelle Positionen
- `reconciliation_cycles_total` - Abgleich-Zyklen

### Alerting Rules

- **TradingBotDown**: Service nicht erreichbar (>1min)
- **HighOrderFailureRate**: >5% Order-Fehlerrate (>2min)

### Log-Format

Strukturierte JSON-Logs mit folgenden Feldern:

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "event_type": "order_created",
  "data": {...}
}
```bash
## Sicherheit

### Best Practices

- ✅ Keine Secrets im Code oder Docker Images
- ✅ Secrets über Kubernetes Secrets
- ✅ Non-root Container User
- ✅ TLS für alle Verbindungen
- ✅ Health Checks für Kubernetes

### Idempotenz & Zuverlässigkeit

- ✅ Signal-Deduplizierung
- ✅ Idempotente Order-Ausführung
- ✅ Circuit Breaker für API-Schutz
- ✅ Exponential Backoff bei Fehlern
- ✅ Reconciliation für Datenkonsistenz

## Performance

### Ziele

- Signal zu Order: <2s (p95)
- Durchsatz: 10 Orders/Sekunde
- Verfügbarkeit: 99.9%

### Optimierungen

- Async/await durchgängig
- Connection Pooling
- Bulk-Operationen wo möglich
- Effiziente Datenbankindizes

## Entwicklung

### Code-Struktur

```bash
src/
├── core/           # Kernlogik
├── connectors/     # Externe APIs
├── utils/          # Hilfsfunktionen
└── main.py         # FastAPI App

tests/              # Unit Tests
helm/               # Kubernetes Deployment
monitoring/         # Alerting Rules
```bash
### Neue Features

1. Branch erstellen
2. Tests schreiben
3. Implementierung
4. Tests aktualisieren
5. Pull Request

### Debugging

```bash
# Logs anzeigen
docker-compose logs -f bot

# In Container einsteigen
docker-compose exec bot bash

# Datenbank prüfen
docker-compose exec db psql -U postgres -d trading_bot
```bash
## FAQ

**Q: Wie aktiviere ich Live-Trading?**
A: Setzen Sie `TRADING_ENABLED=true` und `BINGX_TESTNET=false`

**Q: Wo finde ich die Logs?**
A: Strukturierte JSON-Logs werden auf stdout ausgegeben

**Q: Wie skaliere ich das System?**
A: Erhöhen Sie `replicaCount` im Helm Chart (horizontale Skalierung)

**Q: Was passiert bei Fehlern?**
A: Retry-Logik mit Exponential Backoff, Circuit Breaker bei anhaltenden Problemen

## Support

Bei Problemen:

1. Prüfen Sie die Logs: `docker-compose logs bot`
2. Status-Endpoint: `curl http://localhost:8080/status`
3. Metriken: `curl http://localhost:8080/metrics`

---

**⚠️ Warnung**: Dies ist ein Trading-Bot. Verwenden Sie ihn nur mit Testnet oder kleinen Beträgen. Trading ist riskant!
