# 🚀 Usage Examples & Testing Guide

## 📋 Overview

This document provides practical usage examples, testing procedures, and sample workflows to help users understand and effectively utilize the trading bot system.

---

## 🧪 Testing Framework

### Test Environment Setup

#### Local Test Setup
```bash
# Clone and setup test environment
git clone <repository>
cd trading-bot

# Create test environment
python -m venv test-env
source test-env/bin/activate

# Install test dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Setup test database
createdb trading_bot_test

# Run test migrations
alembic -c alembic_test.ini upgrade head
```

#### Docker Test Setup
```bash
# Use test docker-compose
docker-compose -f docker-compose.test.yml up --build

# Or deploy test environment
docker-compose -f docker-compose.yml -f docker-compose.test.yml up
```

### Test Configuration

**test.env**
```bash
# Test environment configuration
TRADING_ENABLED=false
BINGX_TESTNET=true
LOG_LEVEL=DEBUG
TELEGRAM_BOT_TOKEN=test-bot-token
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/trading_bot_test
CRYPTET_ENABLED=false
```

---

## 🎯 API Usage Examples

### Basic Health Checks

#### Check System Health
```bash
# Using curl
curl -X GET http://localhost:8080/health

# Using httpie
http GET http://localhost:8080/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

#### Get System Status
```bash
curl -X GET http://localhost:8080/status

# Expected response includes:
{
  "trading_enabled": false,
  "exchange_connected": true,
  "telegram_connected": true,
  "database_connected": true,
  "uptime_seconds": 3600,
  "metrics": {
    "orders_processed": 150,
    "signals_received": 200
  }
}
```

### Signal Processing Examples

#### Submit a Trading Signal
```bash
# Basic BUY signal
curl -X POST http://localhost:8080/signal \
  -H "Content-Type: application/json" \
  -d '{
    "message": "BUY BTCUSDT 0.1",
    "source": "telegram",
    "channel": "trading-signals",
    "timestamp": "2024-01-15T10:30:00Z"
  }'

# SELL signal with price target
curl -X POST http://localhost:8080/signal \
  -H "Content-Type: application/json" \
  -d '{
    "message": "SELL ETHUSDT 2.5 at 2500",
    "source": "cryptet",
    "metadata": {
      "signal_id": "12345",
      "confidence": 0.85
    }
  }'

# Complex signal with stop loss
curl -X POST http://localhost:8080/signal \
  -H "Content-Type: application/json" \
  -d '{
    "message": "BUY SOLUSDT 10 SL 90 TP 120",
    "source": "manual",
    "user": "trader-john"
  }'
```

#### Signal Response Examples
```json
{
  "success": true,
  "signal_id": "signal_abc123",
  "parsed_data": {
    "action": "BUY",
    "symbol": "BTCUSDT",
    "quantity": 0.1,
    "price": null,
    "stop_loss": null,
    "take_profit": null
  },
  "order_placed": false,
  "message": "Signal processed successfully"
}
```

### Order Management Examples

#### Place a Test Order
```bash
# Place a test order (BingX testnet)
curl -X POST http://localhost:8080/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC-USDT",
    "side": "BUY",
    "quantity": 0.01,
    "price": 50000,
    "order_type": "LIMIT",
    "test": true
  }'

# Market order example
curl -X POST http://localhost:8080/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "ETH-USDT",
    "side": "SELL",
    "quantity": 1.5,
    "order_type": "MARKET",
    "test": false
  }'
```

#### Check Order Status
```bash
# Get order by ID
curl -X GET "http://localhost:8080/order/order_12345"

# Get recent orders
curl -X GET "http://localhost:8080/orders?limit=10&offset=0"

# Get orders by status
curl -X GET "http://localhost:8080/orders?status=filled"
```

#### Cancel an Order
```bash
# Cancel specific order
curl -X DELETE "http://localhost:8080/order/order_12345"

# Cancel all open orders
curl -X DELETE "http://localhost:8080/orders"
```

### Cryptet Automation Examples

#### Process Cryptet Signal
```bash
# Process Cryptet signal URL
curl -X POST http://localhost:8080/cryptet/process \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://cryptet.com/signal/1234567890",
    "force": false
  }'

# Test Cryptet parsing
curl -X POST http://localhost:8080/cryptet/test \
  -H "Content-Type: application/json" \
  -d '{
    "html_content": "<div>BUY BTC 0.1 at 50000</div>",
    "url": "https://example.com/signal"
  }'
```

#### Monitor Cryptet Signals
```bash
# Get recent processed signals
curl -X GET "http://localhost:8080/cryptet/signals?limit=5"

# Get signal statistics
curl -X GET "http://localhost:8080/cryptet/stats"
```

---

## 📊 Monitoring Examples

### Prometheus Metrics
```bash
# View all metrics
curl http://localhost:8080/metrics

# Filter specific metrics
curl http://localhost:8080/metrics | grep orders_total

# Example metrics output:
# HELP orders_total Total number of orders processed
# TYPE orders_total counter
orders_total{status="filled"} 120
orders_total{status="rejected"} 5
orders_total{status="pending"} 3
```

### Custom Metrics Queries
```bash
# Orders per minute
curl "http://localhost:8080/metrics" | grep -E '(orders_total|rate.*orders_total)'

# Error rates
curl "http://localhost:8080/metrics" | grep -E '(errors_total|_error)'

# System health metrics
curl "http://localhost:8080/metrics" | grep -E '(up|health|status)'
```

---

## 🔧 Configuration Examples

### Environment Configuration

**Development Environment (.env.dev)**
```bash
# Development settings
TRADING_ENABLED=false
BINGX_TESTNET=true
LOG_LEVEL=DEBUG
TELEGRAM_BOT_TOKEN=dev-bot-token
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/trading_bot_dev
CRYPTET_ENABLED=true
CRYPTET_HEADLESS=false
```

**Production Environment (.env.prod)**
```bash
# Production settings
TRADING_ENABLED=true
BINGX_TESTNET=false
LOG_LEVEL=INFO
TELEGRAM_BOT_TOKEN=prod-bot-token
DATABASE_URL=postgresql+asyncpg://user:strong-password@prod-db:5432/trading_bot
CRYPTET_ENABLED=true
CRYPTET_HEADLESS=true
PROMETHEUS_ENABLED=true
```

### Runtime Configuration Changes

#### Enable/Disable Trading
```bash
# Disable trading temporarily
curl -X POST http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{"trading_enabled": false}'

# Enable trading
curl -X POST http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{"trading_enabled": true}'

# Change log level
curl -X POST http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{"log_level": "DEBUG"}'
```

#### Get Current Configuration
```bash
curl -X GET http://localhost:8080/config

# Response:
{
  "trading_enabled": true,
  "bingx_testnet": false,
  "log_level": "INFO",
  "cryptet_enabled": true,
  "database_url": "postgresql+asyncpg://user:****@db:5432/trading_bot",
  "telegram_bot_token": "****"
}
```

---

## 🧪 Testing Scenarios

### Unit Tests

#### Run All Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_signal_processing.py

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run tests in verbose mode
pytest -v
```

#### Test Examples

**Test Signal Parsing**
```python
# tests/test_signal_processing.py
def test_buy_signal_parsing():
    signal = "BUY BTCUSDT 0.1"
    result = parse_signal(signal)
    assert result["action"] == "BUY"
    assert result["symbol"] == "BTCUSDT"
    assert result["quantity"] == 0.1

def test_sell_signal_with_price():
    signal = "SELL ETHUSDT 2.5 at 2500"
    result = parse_signal(signal)
    assert result["action"] == "SELL"
    assert result["symbol"] == "ETHUSDT"
    assert result["quantity"] == 2.5
    assert result["price"] == 2500
```

**Test Order Placement**
```python
# tests/test_order_management.py
@pytest.mark.asyncio
async def test_place_test_order():
    order_data = {
        "symbol": "BTC-USDT",
        "side": "BUY",
        "quantity": 0.01,
        "order_type": "LIMIT",
        "test": True
    }
    
    result = await place_order(order_data)
    assert result["success"] == True
    assert result["order_id"] is not None
    assert result["test"] == True
```

### Integration Tests

#### Test Telegram Integration
```python
# tests/test_telegram_integration.py
@pytest.mark.asyncio
async def test_telegram_message_reception():
    # Simulate receiving a message
    message = "BUY BTCUSDT 0.1"
    result = await process_telegram_message(message)
    
    assert result["processed"] == True
    assert "signal_id" in result
```

#### Test Exchange Integration
```python
# tests/test_exchange_integration.py
@pytest.mark.asyncio
async def test_exchange_connectivity():
    # Test exchange connection
    connected = await check_exchange_connection()
    assert connected == True
    
    # Test balance check
    balance = await get_exchange_balance()
    assert "USDT" in balance
```

### End-to-End Tests

#### Complete Trading Flow
```python
# tests/test_e2e_flow.py
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_trading_flow():
    # 1. Receive signal
    signal = await receive_signal("BUY BTCUSDT 0.1")
    
    # 2. Process signal
    processed = await process_signal(signal)
    
    # 3. Place order
    order = await place_order(processed)
    
    # 4. Verify order
    status = await check_order_status(order["order_id"])
    
    assert status["status"] in ["filled", "pending"]
```

---

## 🚀 Performance Testing

### Load Testing

#### Basic Load Test with wrk
```bash
# Test health endpoint
wrk -t4 -c100 -d30s http://localhost:8080/health

# Test signal processing
wrk -t4 -c50 -d30s -s scripts/signal_test.lua http://localhost:8080/signal

# scripts/signal_test.lua
wrk.method = "POST"
wrk.body = '{"message": "BUY BTCUSDT 0.1", "source": "test"}'
wrk.headers["Content-Type"] = "application/json"
```

#### Advanced Load Testing with k6
```javascript
// loadtest.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '1m', target: 100 },
    { duration: '30s', target: 0 },
  ],
};

export default function() {
  let res = http.post('http://localhost:8080/signal', JSON.stringify({
    message: "BUY BTCUSDT 0.1",
    source: "load-test"
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  sleep(1);
}
```

### Stress Testing

#### Database Stress Test
```bash
# Test database under load
pgbench -h localhost -U postgres -i trading_bot_test
pgbench -h localhost -U postgres -c 20 -j 4 -t 1000 trading_bot_test

# Monitor database performance during test
psql -h localhost -U postgres -d trading_bot_test -c "
SELECT 
    datname, 
    numbackends, 
    xact_commit, 
    xact_rollback,
    blks_read, 
    blks_hit,
    round(blks_hit::decimal / (blks_hit + blks_read), 3) as hit_ratio
FROM pg_stat_database 
WHERE datname = 'trading_bot_test';
"
```

#### API Stress Test
```bash
# High concurrency test
wrk -t12 -c500 -d60s http://localhost:8080/health

# Mixed workload test
# (combine health checks, signal processing, order status checks)
```

---

## 🐛 Debugging Examples

### Debug Mode Operation

#### Enable Debug Logging
```bash
# Set debug environment
export LOG_LEVEL=DEBUG
export SQL_ECHO=true

# Or via API
curl -X POST http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{"log_level": "DEBUG", "sql_echo": true}'
```

#### Debug Signal Processing
```bash
# Test signal parsing
curl -X POST http://localhost:8080/debug/signal \
  -H "Content-Type: application/json" \
  -d '{
    "message": "BUY BTCUSDT 0.1 SL 48000 TP 52000",
    "source": "debug"
  }'

# Response shows detailed parsing steps:
{
  "input": "BUY BTCUSDT 0.1 SL 48000 TP 52000",
  "tokens": ["BUY", "BTCUSDT", "0.1", "SL", "48000", "TP", "52000"],
  "parsed": {
    "action": "BUY",
    "symbol": "BTCUSDT",
    "quantity": 0.1,
    "stop_loss": 48000,
    "take_profit": 52000
  },
  "confidence": 0.95
}
```

#### Debug Order Placement
```bash
# Dry-run order placement
curl -X POST http://localhost:8080/debug/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC-USDT",
    "side": "BUY",
    "quantity": 0.01,
    "order_type": "LIMIT",
    "price": 50000,
    "dry_run": true
  }'
```

### Log Analysis Examples

#### Common Log Patterns
```bash
# Find errors
grep -i error logs/app.log

# Find specific order IDs
grep "order_12345" logs/app.log

# Trace specific signal
grep "signal_abc123" logs/app.log

# Monitor real-time logs
tail -f logs/app.log | grep -E '(ERROR|WARNING)'

# Structured log analysis
jq '. | select(.level == "ERROR")' logs/app.log
```

#### Performance Log Analysis
```bash
# Find slow requests
grep "duration_ms" logs/app.log | jq 'select(.duration_ms > 1000)'

# API call timing
grep "api_call" logs/app.log | jq 'select(.duration > 500)'

# Database query performance
grep "db_query" logs/app.log | jq 'select(.duration > 100)'
```

---

## 📊 Example Workflows

### Daily Trading Workflow

#### Morning Routine
```bash
# 1. Check system health
curl http://localhost:8080/health

# 2. Review overnight activity
curl "http://localhost:8080/orders?since=2024-01-15T00:00:00Z"

# 3. Check exchange balance
curl http://localhost:8080/balance

# 4. Enable trading
curl -X POST http://localhost:8080/config \
  -d '{"trading_enabled": true}'
```

#### Monitoring During Day
```bash
# Watch real-time metrics
watch -n 5 'curl -s http://localhost:8080/status | jq .'

# Monitor order queue
watch -n 2 'curl -s "http://localhost:8080/orders?status=pending" | jq length'

# Check signal processing
tail -f logs/app.log | grep -E '(signal_received|order_placed)'
```

#### Evening Routine
```bash
# 1. Disable trading
curl -X POST http://localhost:8080/config \
  -d '{"trading_enabled": false}'

# 2. Generate daily report
curl "http://localhost:8080/reports/daily?date=2024-01-15"

# 3. Backup database
pg_dump -h localhost -U postgres trading_bot > backup_20240115.sql

# 4. Review performance metrics
curl -s http://localhost:8080/metrics | grep -E '(orders_total|signals_received)'
```

### Incident Response Workflow

#### Detect Issue
```bash
# 1. Receive alert about high error rate
# 2. Check system status
curl http://localhost:8080/health

# 3. Review recent errors
grep -A5 -B5 "ERROR" logs/app.log | tail -20

# 4. Check specific component
curl http://localhost:8080/status | jq '.exchange_connected'
```

#### Investigate and Resolve
```bash
# 1. Identify root cause (e.g., exchange API issue)
curl "https://api.bingx.com/api/v1/ping"

# 2. Temporary mitigation
curl -X POST http://localhost:8080/config \
  -d '{"trading_enabled": false}'

# 3. Monitor resolution
watch -n 10 'curl -s http://localhost:8080/status | jq .exchange_connected'

# 4. Restore service
curl -X POST http://localhost:8080/config \
  -d '{"trading_enabled": true}'
```

#### Post-Mortem
```bash
# 1. Gather logs for analysis
grep "2024-01-15T10:" logs/app.log > incident_analysis.log

# 2. Extract metrics during incident period
curl "http://localhost:8080/metrics" | grep -E '(errors_total|api_calls)'

# 3. Document incident and resolution
# 4. Update runbooks and monitoring
```

---

## 🎓 Training Scenarios

### Beginner Exercises

#### Exercise 1: Basic System Setup
```bash
# Task: Setup development environment
# Steps:
1. Clone repository
2. Create virtual environment
3. Install dependencies
4. Setup test database
5. Run health check
```

#### Exercise 2: Signal Processing Test
```bash
# Task: Test signal parsing
# Steps:
1. Send test BUY signal
2. Verify parsing results
3. Send test SELL signal
4. Test error handling with invalid signal
```

### Intermediate Exercises

#### Exercise 3: Order Management
```bash
# Task: Complete order lifecycle
# Steps:
1. Place test order
2. Check order status
3. Cancel order
4. Verify order cancellation
```

#### Exercise 4: Monitoring Setup
```bash
# Task: Configure monitoring
# Steps:
1. Setup Prometheus
2. Configure Grafana dashboard
3. Create basic alerts
4. Test alert notifications
```

### Advanced Exercises

#### Exercise 5: Performance Testing
```bash
# Task: Load test system
# Steps:
1. Design load test scenario
2. Execute load test
3. Analyze results
4. Identify bottlenecks
```

#### Exercise 6: Incident Response
```bash
# Task: Simulate and resolve incident
# Steps:
1. Simulate exchange API outage
2. Detect issue
3. Implement mitigation
4. Restore service
5. Conduct post-mortem
```

---

## 📝 Cheat Sheet

### Quick Commands
```bash
# Health check
curl http://localhost:8080/health

# Status overview
curl http://localhost:8080/status | jq .

# Send test signal
curl -X POST http://localhost:8080/signal -d '{"message": "BUY BTCUSDT 0.1"}'

# Toggle trading
curl -X POST http://localhost:8080/config -d '{"trading_enabled": false}'

# View metrics
curl http://localhost:8080/metrics | grep orders_total

# Tail logs
tail -f logs/app.log
```

### Common Debug Commands
```bash
# Enable debug mode
export LOG_LEVEL=DEBUG

# Test database connection
psql $DATABASE_URL -c "SELECT 1"

# Test Telegram API
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Test Exchange API
curl "https://api-swap.bingx.com/api/v1/ticker/price?symbol=BTC-USDT"
```

### Emergency Commands
```bash
# Immediate stop trading
curl -X POST http://localhost:8080/config -d '{"trading_enabled": false}'

# Cancel all orders
curl -X DELETE http://localhost:8080/orders

# Force restart
docker-compose restart bot

# Database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Remember**: Always test in a safe environment before running commands in production! Start with testnet trading and small amounts when learning the system.