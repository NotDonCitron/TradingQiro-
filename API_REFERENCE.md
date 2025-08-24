# 📋 Trading Bot API Reference

## 🌐 Base URL
```
http://localhost:8080
```

## 📊 API Endpoints

### Health & Status Endpoints

#### GET `/health`
**Liveness Probe** - Check if the application is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/ready`
**Readiness Probe** - Check if the application is ready to serve requests.

**Response:**

```json
{
  "status": "ready",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/status`
**Detailed System Status** - Get comprehensive system health and component status.

**Response:**

```json
{
  "healthy": true,
  "ready": true,
  "components": {
    "state_manager": true,
    "task_executor": true,
    "reconciliation_job": true,
    "telethon_connector": true,
    "cryptet_automation": true,
    "signal_forwarder": true,
    "bingx_client": true,
    "audit_logger": true,
    "metrics": true
  },
  "config": {
    "trading_enabled": false,
    "cryptet_enabled": true,
    "bingx_testnet": true,
    "log_level": "INFO",
    "own_group_chat_id": true
  }
}
```

#### GET `/metrics`
**Prometheus Metrics** - Export metrics in Prometheus format.

**Response:**

```
# HELP orders_total Total number of orders
# TYPE orders_total counter
orders_total 42

# HELP orders_failed_total Total number of failed orders
# TYPE orders_failed_total counter
orders_failed_total 3

# HELP signal_processing_duration_seconds Signal processing duration
# TYPE signal_processing_duration_seconds histogram
signal_processing_duration_seconds_bucket{le="0.1"} 25
signal_processing_duration_seconds_bucket{le="0.5"} 40
signal_processing_duration_seconds_bucket{le="1.0"} 42
...
```

---

### Signal Processing Endpoints

#### POST `/signal`
**Manual Signal Submission** - Submit a trading signal manually for testing.

**Request:**

```json
{
  "message": "BUY BTCUSDT 0.1",
  "metadata": {
    "source": "manual",
    "chat_id": 123456789,
    "message_id": 987654321
  }
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Signal processed via normal flow"
}
```

**Error Response:**

```json
{
  "status": "failed",
  "reason": "Task executor not available"
}
```

---

### Signal Forwarder Endpoints

#### GET `/forwarder/status`
**Signal Forwarder Status** - Get status of the signal forwarding system.

**Response:**

```json
{
  "status": {
    "enabled": true,
    "target_group_id": "-1002773853382",
    "monitored_chat_id": -2299206473,
    "pattern_configured": true
  },
  "monitored_chat": -2299206473,
  "target_group": "-1002773853382"
}
```

---

### Cryptet Automation Endpoints

#### GET `/cryptet/status`
**Cryptet Automation Status** - Get status and active signals from Cryptet automation.

**Response:**

```json
{
  "status": {
    "initialized": true,
    "browser_ready": true,
    "cookies_loaded": true,
    "active_monitors": 2
  },
  "active_signals": [
    {
      "signal_id": "cryptet_12345",
      "symbol": "BTC/USDT",
      "direction": "LONG",
      "entry_price": "45000.00",
      "targets": ["46000.00", "47000.00"],
      "start_time": "2024-01-01T10:00:00Z",
      "status": "monitoring"
    }
  ],
  "active_count": 1
}
```

#### POST `/cryptet/test`
**Test Cryptet Link** - Test processing a Cryptet signal link for debugging.

**Request:**

```json
{
  "url": "https://cryptet.com/signal/1234567890"
}
```

**Response:**

```json
{
  "status": "success",
  "signal_data": {
    "symbol": "BTC/USDT",
    "direction": "LONG",
    "entry_price": "45000.00",
    "targets": ["46000.00", "47000.00"],
    "stop_loss": "44000.00",
    "leverage": 50,
    "source_url": "https://cryptet.com/signal/1234567890"
  }
}
```

**Error Response:**

```json
{
  "status": "failed",
  "reason": "Could not extract signal data"
}
```

#### POST `/cryptet/close/{signal_id}`
**Manually Close Signal** - Manually close a monitored Cryptet signal.

**Request:**

```json
{
  "reason": "manual intervention"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Signal cryptet_12345 closed"
}
```

**Error Response:**

```json
{
  "status": "failed",
  "reason": "Signal not found or already closed"
}
```

---

### Webhook Endpoints

#### POST `/webhook/alert`
**Generic Alert Webhook** - Receive alerts from Alertmanager.

**Request:**

```json
{
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "TradingBotDown",
        "severity": "critical"
      },
      "annotations": {
        "summary": "Trading Bot is down",
        "description": "Service has been unreachable for over 5 minutes"
      },
      "startsAt": "2024-01-01T12:00:00Z"
    }
  ]
}
```

**Response:**

```json
{
  "status": "received"
}
```

#### POST `/webhook/critical-alert`
**Critical Alert Webhook** - Receive critical alerts with Telegram notification.

**Response:**

```json
{
  "status": "critical_alert_processed"
}
```

#### POST `/webhook/warning-alert`
**Warning Alert Webhook** - Receive warning alerts (log only, no Telegram).

**Response:**

```json
{
  "status": "warning_alert_logged"
}
```

---

### Diagnostic Endpoints

#### GET `/diagnostics/run`
**Run Diagnostics** - Execute comprehensive system diagnostics.

**Response:**

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "overall_status": "healthy",
  "checks": [
    {
      "component": "telegram_connection",
      "status": "healthy",
      "message": "Telegram client connected successfully"
    },
    {
      "component": "database_connection",
      "status": "healthy",
      "message": "Database connection established"
    },
    {
      "component": "exchange_api",
      "status": "warning",
      "message": "BingX API connection slow"
    }
  ],
  "critical_issues": 0,
  "warnings": 1,
  "recommendations": ["Check BingX API connectivity"]
}
```

#### POST `/diagnostics/resolve`
**Resolve Issues** - Attempt to automatically resolve detected issues.

**Response:**

```json
{
  "diagnostics": {
    "timestamp": "2024-01-01T12:00:00Z",
    "overall_status": "healthy",
    "checks": [...],
    "critical_issues": 0,
    "warnings": 1
  },
  "resolutions": {
    "attempted": ["Reconnect to BingX API"],
    "succeeded": ["Reconnect to BingX API"],
    "failed": [],
    "recommendations": []
  }
}
```

#### GET `/diagnostics/health`
**Diagnostic System Health** - Check if diagnostic system is available.

**Response:**

```json
{
  "diagnostic_system": true,
  "error_resolver": true,
  "status": "healthy"
}
```

---

## 🚀 Signal Formats

### Standard Trading Signals
```
BUY BTCUSDT 0.1
SELL ETHUSDT 0.5
```

### Advanced Signal Format (Cornix-compatible)
```
🟢 Long
Name: BTC/USDT
Margin mode: Cross (50X)

↪️ Entry price(USDT):
45000.00

Targets(USDT):
1) 46000.00
2) 47000.00
```

### Take-Profit Updates
```
Binance, BingX Spot, Bitget Spot, KuCoin, OKX
#BTC/USDT Take-Profit target 1 ✅
Profit: 2.22% 📈
Period: 1h 30m ⏰
```

---

## 🔧 Error Handling

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid input)
- `503` - Service Unavailable (component not ready)
- `500` - Internal Server Error

### Error Response Format

```json
{
  "status": "error",
  "error": "Component not available",
  "details": "Telegram connector not initialized"
}
```

---

## 📋 Rate Limiting

- **Health/Status endpoints**: No rate limiting
- **Signal endpoints**: 10 requests per minute
- **Cryptet endpoints**: 5 requests per minute
- **Webhook endpoints**: 20 requests per minute

---

## 🔐 Authentication

All endpoints require valid API keys configured via environment variables:

```bash
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
BINGX_API_KEY=your_api_key
BINGX_SECRET_KEY=your_secret_key
```

---

## 📊 Monitoring

### Key Metrics
- `orders_total` - Total orders processed
- `orders_failed_total` - Failed orders
- `signal_processing_duration_seconds` - Processing time
- `reconciliation_cycles_total` - Reconciliation cycles
- `position_size` - Current positions

### Alert Rules
- `TradingBotDown` - Service unreachable >1 minute
- `HighOrderFailureRate` - >5% order failure rate >2 minutes

---

## 📝 Examples

### Test Signal Processing
```bash
curl -X POST http://localhost:8080/signal \
  -H "Content-Type: application/json" \
  -d '{"message": "BUY BTCUSDT 0.1", "metadata": {"source": "test"}}'
```

### Check System Status
```bash
curl http://localhost:8080/status
```

### Test Cryptet Automation
```bash
curl -X POST http://localhost:8080/cryptet/test \
  -H "Content-Type: application/json" \
  -d '{"url": "https://cryptet.com/signal/1234567890"}'
```

### Run Diagnostics
```bash
curl http://localhost:8080/diagnostics/run
```

---

## ⚠️ Important Notes

1. **Production Mode**: Set `TRADING_ENABLED=true` and `BINGX_TESTNET=false` for live trading
2. **Cryptet Automation**: Requires valid `cookies.txt` file with Cryptet session
3. **Telegram Integration**: Bot must be added to monitored groups with appropriate permissions
4. **Rate Limiting**: Respect exchange API rate limits to avoid bans
5. **Monitoring**: Regularly check metrics and logs for system health

---

## 🆘 Support

For issues:
1. Check logs: `docker-compose logs bot`
2. Run diagnostics: `curl http://localhost:8080/diagnostics/run`
3. Verify configuration: Check environment variables
4. Test individual components using the provided endpoints

**Warning**: This is a trading bot. Use only with testnet or small amounts. Trading is risky!