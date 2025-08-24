# 📊 Monitoring & Troubleshooting Guide

## 👁️ Overview

This guide covers comprehensive monitoring strategies, alert configurations, and detailed troubleshooting procedures for the trading bot system.

---

## 📈 Monitoring Framework

### Prometheus Metrics

The system exposes the following metrics endpoints:

- **Health**: `GET /health`
- **Status**: `GET /status` 
- **Metrics**: `GET /metrics` (Prometheus format)

### Key Metrics to Monitor

#### Order Processing Metrics
```promql
# Total orders processed
orders_total

# Failed orders
orders_failed_total

# Orders by status
orders_by_status{status="filled"}
orders_by_status{status="rejected"}
orders_by_status{status="pending"}

# Order processing latency
order_processing_seconds
```

#### Signal Processing Metrics
```promql
# Signals received
signals_received_total

# Signal processing errors
signal_processing_errors_total

# Signal source distribution
signals_by_source{source="telegram"}
signals_by_source{source="cryptet"}
```

#### Exchange Integration Metrics
```promql
# API call success rate
bingx_api_calls_total
bingx_api_errors_total

# Order execution time
bingx_order_execution_seconds

# Balance monitoring
exchange_balance_usdt
exchange_balance_btc
```

#### Database Metrics
```promql
# Database connections
db_connections_active
db_connections_idle

# Query performance
db_query_duration_seconds

# Transaction rates
db_transactions_total
```

### Grafana Dashboards

**Recommended Dashboards:**
1. **Trading Overview**: High-level trading performance
2. **Signal Processing**: Signal reception and processing
3. **Exchange Health**: Exchange API performance
4. **Database Performance**: Database metrics and connections
5. **System Health**: Infrastructure and application health

---

## 🔔 Alert Configuration

### Critical Alerts

#### Order Processing Alerts
```yaml
- alert: HighOrderFailureRate
  expr: rate(orders_failed_total[5m]) / rate(orders_total[5m]) > 0.1
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High order failure rate detected"
    description: "Order failure rate exceeds 10% for 5 minutes"

- alert: OrderProcessingStalled
  expr: rate(orders_total[10m]) == 0
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "Order processing stalled"
    description: "No orders processed in last 10 minutes"
```

#### Signal Processing Alerts
```yaml
- alert: SignalProcessingErrors
  expr: rate(signal_processing_errors_total[5m]) > 5
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Signal processing errors detected"
    description: "Multiple signal processing errors in last 5 minutes"

- alert: NoSignalsReceived
  expr: rate(signals_received_total[30m]) == 0
  for: 30m
  labels:
    severity: warning
  annotations:
    summary: "No signals received"
    description: "No trading signals received in last 30 minutes"
```

#### Exchange API Alerts
```yaml
- alert: ExchangeAPIDown
  expr: rate(bingx_api_errors_total[5m]) / rate(bingx_api_calls_total[5m]) > 0.5
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Exchange API failing"
    description: "Exchange API error rate exceeds 50%"

- alert: LowExchangeBalance
  expr: exchange_balance_usdt < 100
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Low exchange balance"
    description: "Exchange balance below $100 USDT"
```

#### System Health Alerts
```yaml
- alert: HighCPULoad
  expr: node_cpu_seconds_total{mode="idle"} < 20
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High CPU load"
    description: "CPU idle time below 20% for 5 minutes"

- alert: HighMemoryUsage
  expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 10
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High memory usage"
    description: "Available memory below 10% for 5 minutes"

- alert: DatabaseConnectionErrors
  expr: rate(db_connection_errors_total[5m]) > 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Database connection errors"
    description: "Database connection errors detected"
```

### Alert Routing

Configure alert routing based on severity:
- **Critical**: Immediate notification (SMS, Phone call)
- **Warning**: Email notification within 15 minutes
- **Info**: Daily summary email

---

## 🔧 Troubleshooting Procedures

### Quick Diagnosis Commands

#### Health Check
```bash
# Check application health
curl -s http://localhost:8080/health | jq .

# Get detailed status
curl -s http://localhost:8080/status | jq .

# Check metrics endpoint
curl -s http://localhost:8080/metrics | head -20
```

#### Database Checks
```bash
# Check database connectivity
psql -h localhost -U postgres -d trading_bot -c "SELECT 1"

# Check recent orders
psql -h localhost -U postgres -d trading_bot -c "SELECT * FROM orders ORDER BY created_at DESC LIMIT 5"

# Check database size
psql -h localhost -U postgres -d trading_bot -c "SELECT pg_size_pretty(pg_database_size('trading_bot'))"
```

#### Log Analysis
```bash
# View application logs
docker-compose logs -f bot

# Search for errors
docker-compose logs bot | grep -i error

# Follow logs in real-time
docker-compose logs -f --tail=100 bot

# Kubernetes logs
kubectl logs -f deployment/trading-bot
kubectl describe pod trading-bot-xyz
```

### Common Issues and Solutions

#### Issue: Database Connection Problems
**Symptoms**: 
- Application fails to start
- Database connection errors in logs
- "Connection refused" or "timeout" errors

**Solutions**:
1. Check if database is running:
   ```bash
   docker-compose ps db
   # or
   systemctl status postgresql
   ```

2. Verify connection string:
   ```bash
   echo $DATABASE_URL
   # Should be: postgresql+asyncpg://user:password@host:port/database
   ```

3. Test connectivity:
   ```bash
   telnet db-host 5432
   # or
   nc -zv db-host 5432
   ```

4. Check firewall rules if applicable

#### Issue: Telegram API Connection Issues
**Symptoms**:
- Bot not responding to messages
- "Invalid API ID" or "AuthKey" errors
- Connection timeouts

**Solutions**:
1. Verify API credentials:
   ```bash
   echo "API ID: $TELEGRAM_API_ID"
   echo "API Hash: $TELEGRAM_API_HASH" 
   echo "Bot Token: $TELEGRAM_BOT_TOKEN"
   ```

2. Test Telegram API:
   ```bash
   curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"
   ```

3. Check bot permissions in Telegram groups

#### Issue: BingX API Errors
**Symptoms**:
- Order execution failures
- "Invalid API key" errors
- Rate limiting errors

**Solutions**:
1. Verify API keys:
   ```bash
   echo "BingX API Key: $BINGX_API_KEY"
   echo "BingX Secret Key: [hidden]"
   ```

2. Check testnet vs mainnet configuration:
   ```bash
   echo "BINGX_TESTNET: $BINGX_TESTNET"
   ```

3. Test API connectivity:
   ```bash
   # Test connectivity (adjust for your exchange)
   curl "https://api-swap.bingx.com/api/v1/ticker/price?symbol=BTC-USDT"
   ```

#### Issue: Signal Processing Failures
**Symptoms**:
- Signals not being processed
- Parsing errors in logs
- Incorrect order placement

**Solutions**:
1. Check signal format:
   ```bash
   # View recent signals
   psql -h localhost -U postgres -d trading_bot -c "SELECT * FROM signals ORDER BY created_at DESC LIMIT 10"
   ```

2. Test signal parsing:
   ```bash
   curl -X POST http://localhost:8080/debug/signal \
     -H "Content-Type: application/json" \
     -d '{"message": "BUY BTCUSDT 0.1", "source": "test"}'
   ```

3. Verify signal source configuration

#### Issue: Performance Degradation
**Symptoms**:
- Slow order processing
- High CPU/Memory usage
- Database timeouts

**Solutions**:
1. Monitor resource usage:
   ```bash
   docker stats
   # or
   top
   # or
   kubectl top pods
   ```

2. Check database performance:
   ```bash
   # Check slow queries
   psql -h localhost -U postgres -d trading_bot -c "SELECT * FROM pg_stat_activity WHERE state = 'active'"

   # Check index usage
   psql -h localhost -U postgres -d trading_bot -c "SELECT * FROM pg_stat_all_indexes WHERE idx_scan = 0"
   ```

3. Optimize configuration:
   ```bash
   # Increase connection pool
   export DATABASE_POOL_SIZE=50
   export DATABASE_MAX_OVERFLOW=20
   ```

### Advanced Troubleshooting

#### Database Performance Analysis
```sql
-- Find slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check table sizes
SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;

-- Check index usage
SELECT 
    schemaname,
    relname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_all_indexes 
WHERE idx_scan = 0;
```

#### Application Performance Profiling
```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
export SQL_ECHO=true

# Use Python profiler
python -m cProfile -o profile.stats src/main.py

# Analyze profile
python -m pstats profile.stats
```

#### Memory Leak Detection
```bash
# Monitor memory usage over time
watch -n 5 'docker stats --no-stream trading-bot-bot-1 | grep trading-bot'

# Use memory profiler
pip install memory-profiler
python -m memory_profiler src/main.py
```

### Incident Response Procedures

#### Critical Incident: Exchange API Outage
1. **Immediate Action**: Disable trading
   ```bash
   export TRADING_ENABLED=false
   docker-compose restart bot
   ```

2. **Investigation**: 
   - Check exchange status page
   - Verify API connectivity
   - Monitor error rates

3. **Recovery**:
   - Wait for exchange to be stable
   - Re-enable trading gradually
   - Monitor order execution

#### Critical Incident: Database Corruption
1. **Immediate Action**: Stop application
   ```bash
   docker-compose stop bot
   ```

2. **Investigation**:
   - Check database logs
   - Run database integrity check
   ```bash
   psql -h localhost -U postgres -d trading_bot -c "VACUUM ANALYZE"
   ```

3. **Recovery**:
   - Restore from backup if needed
   - Start application
   - Monitor database performance

#### Critical Incident: Financial Loss Detection
1. **Immediate Action**: Freeze all trading
   ```bash
   export TRADING_ENABLED=false
   docker-compose restart bot
   ```

2. **Investigation**:
   - Review recent orders
   - Check balance discrepancies
   - Analyze trade execution

3. **Recovery**:
   - Identify root cause
   - Implement fixes
   - Gradually resume trading

### Monitoring Best Practices

#### Log Management
- Use structured JSON logging
- Implement log rotation
- Centralize logs for analysis
- Set appropriate log levels:
  - **PRODUCTION**: INFO or WARNING
  - **DEVELOPMENT**: DEBUG
  - **TROUBLESHOOTING**: TRACE

#### Performance Monitoring
- Monitor both application and infrastructure
- Set appropriate thresholds for alerts
- Use percentiles for latency monitoring
- Track both success and error rates

#### Capacity Planning
- Monitor resource usage trends
- Plan for scaling based on metrics
- Set up auto-scaling where appropriate
- Regularly review and adjust resource allocations

### Debug Tools and Utilities

#### Built-in Debug Endpoints
```bash
# Health check
curl http://localhost:8080/health

# Detailed system status
curl http://localhost:8080/status

# Metrics in Prometheus format
curl http://localhost:8080/metrics

# Configuration overview (if enabled)
curl http://localhost:8080/config
```

#### Database Maintenance Scripts
```bash
# Backup database
pg_dump -h localhost -U postgres trading_bot > backup_$(date +%Y%m%d).sql

# Restore database
psql -h localhost -U postgres trading_bot < backup_file.sql

# Vacuum and analyze
psql -h localhost -U postgres trading_bot -c "VACUUM ANALYZE"

# Check database size
psql -h localhost -U postgres trading_bot -c "SELECT pg_size_pretty(pg_database_size('trading_bot'))"
```

#### Performance Testing
```bash
# Load test signal processing
wrk -t4 -c100 -d30s http://localhost:8080/health

# Stress test database
pgbench -h localhost -U postgres -i trading_bot
pgbench -h localhost -U postgres -c 10 -j 2 -t 1000 trading_bot
```

### Recovery Procedures

#### Database Recovery
1. **Identify issue**: Check database logs and metrics
2. **Stop application**: Prevent further data corruption
3. **Backup current state**: Create snapshot if possible
4. **Restore**: Use latest backup or repair database
5. **Verify**: Check data integrity before restarting

#### Application Recovery
1. **Identify root cause**: Analyze logs and metrics
2. **Apply fix**: Update configuration or code
3. **Restart**: Deploy fixed version
4. **Monitor**: Watch for recurrence of issue

#### Exchange Integration Recovery
1. **Check exchange status**: Verify exchange is operational
2. **Test connectivity**: Simple API calls to confirm
3. **Review credentials**: Ensure API keys are valid
4. **Gradual restart**: Enable trading with monitoring

---

## 📋 Maintenance Checklist

### Daily Checks
- [ ] Review application logs for errors
- [ ] Check database connection pool usage
- [ ] Verify exchange connectivity
- [ ] Monitor order success rates
- [ ] Check system resource usage

### Weekly Checks
- [ ] Review performance metrics trends
- [ ] Check database size and growth
- [ ] Verify backup procedures
- [ ] Review alert configurations
- [ ] Update dependencies if needed

### Monthly Checks
- [ ] Performance tuning review
- [ ] Security audit
- [ ] Disaster recovery test
- [ ] Capacity planning review
- [ ] Documentation updates

### Incident Response Kit
Keep these tools ready:
- Database backup and restore scripts
- Configuration templates for quick deployment
- Contact information for exchange support
- Monitoring dashboard access credentials
- Emergency stop procedures documented

**Remember**: Always test recovery procedures in a staging environment before needing them in production!