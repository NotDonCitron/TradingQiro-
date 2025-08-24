# ⚙️ Configuration Reference

## 📋 Overview

This document provides a comprehensive reference for all configuration options available in the Trading Bot system, including environment variables, JSON configuration files, and runtime settings.

---

## 🏷️ Environment Variables

### Core Application Settings

#### `TELEGRAM_API_ID` (Required)
**Description**: Telegram API ID from my.telegram.org  
**Default**: None  
**Example**: `1234567`

#### `TELEGRAM_API_HASH` (Required)
**Description**: Telegram API Hash from my.telegram.org  
**Default**: None  
**Example**: `a1b2c3d4e5f6g7h8i9j0`

#### `TELEGRAM_BOT_TOKEN` (Required)
**Description**: Telegram Bot Token from @BotFather  
**Default**: None  
**Example**: `1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ`

#### `DATABASE_URL`
**Description**: PostgreSQL connection string  
**Default**: `postgresql+asyncpg://postgres:change-me-in-production@db:5432/trading_bot`  
**Example**: `postgresql+asyncpg://user:password@localhost:5432/trading_bot`

#### `LOG_LEVEL`
**Description**: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)  
**Default**: `INFO`  
**Example**: `DEBUG`

#### `PORT`
**Description**: HTTP server port  
**Default**: `8080`  
**Example**: `8000`

---

### Trading Configuration

#### `TRADING_ENABLED`
**Description**: Enable/disable actual trading  
**Default**: `false`  
**Example**: `true`

#### `BINGX_API_KEY` (Required for Trading)
**Description**: BingX exchange API key  
**Default**: None  
**Example**: `your_bingx_api_key`

#### `BINGX_SECRET_KEY` (Required for Trading)
**Description**: BingX exchange secret key  
**Default**: None  
**Example**: `your_bingx_secret_key`

#### `BINGX_TESTNET`
**Description**: Use BingX testnet environment  
**Default**: `true`  
**Example**: `false`

#### `MAX_SINGLE_TRADE_USD`
**Description**: Maximum USD amount per trade  
**Default**: `1000.0`  
**Example**: `500.0`

#### `MAX_DAILY_LOSS_USD`
**Description**: Maximum daily loss limit in USD  
**Default**: `5000.0`  
**Example**: `2000.0`

---

### Cryptet Automation Settings

#### `CRYPTET_ENABLED`
**Description**: Enable Cryptet automation system  
**Default**: `true`  
**Example**: `true`

#### `CRYPTET_COOKIES_FILE`
**Description**: Path to Cryptet cookies file  
**Default**: `cookies.txt`  
**Example**: `/app/cookies.txt`

#### `CRYPTET_HEADLESS`
**Description**: Run browser in headless mode  
**Default**: `true`  
**Example**: `false`

#### `CRYPTET_DEFAULT_LEVERAGE`
**Description**: Default leverage for Cryptet signals  
**Default**: `50`  
**Example**: `25`

#### `CRYPTET_MONITOR_INTERVAL`
**Description**: P&L monitoring interval in seconds  
**Default**: `300` (5 minutes)  
**Example**: `60`

#### `CRYPTET_MAX_MONITOR_HOURS`
**Description**: Maximum signal monitoring duration in hours  
**Default**: `6`  
**Example**: `4`

#### `CRYPTET_BROWSER_TIMEOUT`
**Description**: Browser operation timeout in seconds  
**Default**: `10`  
**Example**: `30`

---

### Signal Forwarding Settings

#### `OWN_GROUP_CHAT_ID`
**Description**: Target Telegram group for signal forwarding  
**Default**: None  
**Example**: `-1001234567890`

#### `MONITORED_CHAT_IDS`
**Description**: Comma-separated list of monitored Telegram chat IDs  
**Default**: `-2299206473,-1001804143400`  
**Example**: `-2299206473,-1001804143400,-1009876543210`

---

### Arbitrage Configuration

#### `ARBITRAGE_ENABLED`
**Description**: Enable arbitrage scanning  
**Default**: `true`  
**Example**: `true`

#### `MIN_PROFIT_THRESHOLD_PERCENT`
**Description**: Minimum profit percentage to consider arbitrage  
**Default**: `0.5`  
**Example**: `1.0`

#### `SCAN_INTERVAL_SECONDS`
**Description**: Arbitrage scan interval in seconds  
**Default**: `5`  
**Example**: `10`

#### `TRADING_SYMBOLS`
**Description**: Comma-separated list of symbols to monitor  
**Default**: `BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT,SOL/USDT`  
**Example**: `BTC/USDT,ETH/USDT,XRP/USDT`

---

### Monitoring & Alerting

#### `PROMETHEUS_ENABLED`
**Description**: Enable Prometheus metrics endpoint  
**Default**: `true`  
**Example**: `true`

#### `ALERTMANAGER_URL`
**Description**: Alertmanager webhook URL  
**Default**: None  
**Example**: `http://alertmanager:9093/api/v1/alerts`

#### `TELEGRAM_ALERTS_ENABLED`
**Description**: Enable Telegram alerts for critical events  
**Default**: `true`  
**Example**: `true`

---

## 📄 JSON Configuration Files

### `config/arbitrage_config.json`

**Location**: `config/arbitrage_config.json`  
**Description**: Arbitrage trading configuration

**Example Structure**:
```json
{
  "arbitrage": {
    "enabled": true,
    "min_profit_threshold": 0.5,
    "max_profit_threshold": 5.0,
    "min_volume_threshold": 1000.0,
    "scan_interval_seconds": 5,
    "max_opportunity_age_seconds": 30,
    "risk_limits": {
      "max_single_trade_usd": 1000.0,
      "max_daily_loss_usd": 5000.0,
      "max_open_positions": 5
    }
  },
  "exchanges": {
    "binance": {
      "enabled": true,
      "api_key_env": "BINANCE_API_KEY",
      "secret_key_env": "BINANCE_SECRET_KEY",
      "testnet": true,
      "rate_limit": 1000,
      "fee_structure": {
        "maker": 0.001,
        "taker": 0.001
      }
    },
    "coinbase": {
      "enabled": true,
      "api_key_env": "COINBASE_API_KEY",
      "secret_key_env": "COINBASE_SECRET_KEY",
      "sandbox": true,
      "rate_limit": 500
    }
  },
  "firecrawl": {
    "enabled": true,
    "api_key_env": "FIRECRAWL_API_KEY",
    "base_url": "https://api.firecrawl.com",
    "rate_limit": 100
  },
  "cache": {
    "redis_url": "redis://localhost:6379",
    "price_cache_ttl_seconds": 30,
    "arbitrage_cache_ttl_seconds": 60,
    "whale_cache_ttl_seconds": 300
  },
  "alerts": {
    "telegram_alerts": true,
    "min_profit_alert": 1.0
  }
}
```

---

### Exchange Configuration Reference

#### Binance Exchange
```json
{
  "binance": {
    "enabled": true,
    "api_key_env": "BINANCE_API_KEY",
    "secret_key_env": "BINANCE_SECRET_KEY",
    "testnet": true,
    "rate_limit": 1000,
    "fee_structure": {
      "maker": 0.001,
      "taker": 0.001
    }
  }
}
```

#### Coinbase Exchange
```json
{
  "coinbase": {
    "enabled": true,
    "api_key_env": "COINBASE_API_KEY",
    "secret_key_env": "COINBASE_SECRET_KEY",
    "sandbox": true,
    "rate_limit": 500
  }
}
```

#### Kraken Exchange
```json
{
  "kraken": {
    "enabled": true,
    "api_key_env": "KRAKEN_API_KEY",
    "secret_key_env": "KRAKEN_SECRET_KEY",
    "sandbox": true,
    "rate_limit": 300
  }
}
```

---

## 🎯 Signal Processing Configuration

### Signal Format Detection

The system automatically detects signals in multiple formats:

1. **Simple Format**: `BUY BTCUSDT 0.1`
2. **Advanced Format**: Cornix-compatible multi-line format
3. **Cryptet Format**: Automatically parsed from Cryptet URLs

### Signal Validation Rules

```python
# Minimum signal requirements
MIN_SIGNAL_CONFIDENCE = 0.8
MIN_VOLUME_THRESHOLD = 1000.0
MAX_LEVERAGE = 50
```

---

## 🔧 Runtime Configuration

### Docker Compose Environment

**File**: `docker-compose.yml`

```yaml
environment:
  - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
  - TRADING_ENABLED=false
  - BINGX_TESTNET=true
  - LOG_LEVEL=INFO
  - TELEGRAM_API_ID=${TELEGRAM_API_ID}
  - TELEGRAM_API_HASH=${TELEGRAM_API_HASH}
  - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
  - BINGX_API_KEY=${BINGX_API_KEY}
  - BINGX_SECRET_KEY=${BINGX_SECRET_KEY}
```

### Kubernetes Configuration

**File**: `helm/trading-bot/values.yaml`

```yaml
env:
  TRADING_ENABLED: "false"
  BINGX_TESTNET: "true"
  LOG_LEVEL: "INFO"

secrets:
  telegram_api_id: ""
  telegram_api_hash: ""
  telegram_bot_token: ""
  database_url: ""
  bingx_api_key: ""
  bingx_secret_key: ""
```

---

## 📊 Monitoring Configuration

### Prometheus Metrics

**Endpoint**: `/metrics`  
**Port**: `9090`

**Key Metrics**:
- `orders_total` - Total orders processed
- `orders_failed_total` - Failed orders count
- `signal_processing_duration_seconds` - Processing time histogram
- `position_size` - Current position values
- `reconciliation_cycles_total` - Reconciliation attempts

### Alerting Rules

**File**: `monitoring/alerts.yaml`

```yaml
groups:
- name: trading-bot
  rules:
  - alert: TradingBotDown
    expr: up{job="trading-bot"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Trading Bot is down"
      description: "Service has been unreachable for over 1 minute"
  
  - alert: HighOrderFailureRate
    expr: rate(orders_failed_total[2m]) / rate(orders_total[2m]) > 0.05
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High order failure rate"
      description: "More than 5% of orders are failing"
```

---

## 🔐 Security Configuration

### Environment Security

```bash
# Never commit these files
.env
cookies.txt
*.key
*.pem

# Database credentials should be secrets
POSTGRES_PASSWORD=strong-password-here
```

### API Key Security

```bash
# Use environment variables for API keys
export BINGX_API_KEY="your-api-key"
export BINGX_SECRET_KEY="your-secret-key"

# Never hardcode API keys in configuration files
```

---

## 🚀 Performance Tuning

### Database Optimization

```bash
# Connection pool settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_RECYCLE=3600
```

### Memory Settings

```bash
# Python memory management
PYTHONMALLOC=debug
PYTHONUNBUFFERED=1
```

### Browser Optimization

```bash
# Chrome headless settings
CRYPTET_HEADLESS=true
CHROME_MEMORY_LIMIT=512m
```

---

## 🧪 Testing Configuration

### Test Environment

```bash
# Test-specific settings
TEST_MODE=true
BINGX_TESTNET=true
TRADING_ENABLED=false
LOG_LEVEL=DEBUG
```

### Mock Services

```bash
# Enable mock services for testing
MOCK_BINGX=true
MOCK_TELEGRAM=true
MOCK_DATABASE=true
```

---

## 📝 Configuration Examples

### Development Environment

```bash
# .env.dev
TELEGRAM_API_ID=1234567
TELEGRAM_API_HASH=a1b2c3d4e5f6g7h8i9j0
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ
TRADING_ENABLED=false
BINGX_TESTNET=true
LOG_LEVEL=DEBUG
CRYPTET_HEADLESS=false
```

### Production Environment

```bash
# .env.production
TELEGRAM_API_ID=prod_api_id
TELEGRAM_API_HASH=prod_api_hash
TELEGRAM_BOT_TOKEN=prod_bot_token
TRADING_ENABLED=true
BINGX_TESTNET=false
LOG_LEVEL=INFO
CRYPTET_HEADLESS=true
OWN_GROUP_CHAT_ID=-1001234567890
```

### Docker Compose Example

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  bot:
    environment:
      - TRADING_ENABLED=false
      - LOG_LEVEL=DEBUG
      - CRYPTET_HEADLESS=false
```

---

## 🆘 Troubleshooting Configuration

### Common Issues

1. **Missing API Keys**: Ensure all required environment variables are set
2. **Invalid Chat ID**: OWN_GROUP_CHAT_ID must be negative for groups
3. **Cookie Issues**: Verify cookies.txt format and permissions
4. **Database Connection**: Check DATABASE_URL format and credentials

### Debug Mode

```bash
# Enable debug mode
LOG_LEVEL=DEBUG
CRYPTET_HEADLESS=false
ENABLE_STARTUP_DIAGNOSTICS=true
```

### Configuration Validation

```bash
# Run configuration validation
curl http://localhost:8080/diagnostics/run
```

---

## 📋 Configuration Checklist

- [ ] Set all required environment variables
- [ ] Verify database connection string
- [ ] Configure Telegram API credentials
- [ ] Set up exchange API keys
- [ ] Configure Cryptet cookies file
- [ ] Set target Telegram group ID
- [ ] Configure trading limits and risk management
- [ **Set up monitoring and alerting**
- [ ] Test configuration with diagnostics
- [ ] Verify production vs test settings

**Remember**: Always test configurations in a safe environment before deploying to production!