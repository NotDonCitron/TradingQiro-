# 📊 TRADING BOT - MONITORING DASHBOARD

## 🎯 ÜBERSICHT

Das Trading Bot Monitoring Dashboard bietet umfassendes Monitoring und Alerting für Ihre produktionsreife Trading-Bot-Umgebung.

### ✅ **WAS SIE ERHALTEN:**

- **🔥 Real-time Dashboards** - Live-Visualisierung aller Trading-Metriken
- **📈 Performance Monitoring** - Latenz, Durchsatz, Erfolgsraten
- **🚨 Intelligent Alerting** - Sofortige Benachrichtigungen bei Problemen
- **📊 Historical Analytics** - Langzeit-Trends und Analyse
- **💾 Resource Monitoring** - CPU, Memory, Container-Health
- **⚡ Zero-Configuration** - Ein Klick Setup mit Docker

---

## 🚀 SCHNELLSTART

### **Windows:**
```batch
.\start-monitoring.bat
```

### **Linux/Mac:**
```bash
./start-monitoring.sh
```

### **Management:**
```batch
.\manage-monitoring.bat  # Interaktives Management-Menu
```

---

## 🌐 DASHBOARD-ZUGANG

| Service | URL | Beschreibung | Login |
|---------|-----|--------------|-------|
| **📊 Grafana** | http://localhost:3000 | Haupt-Dashboard | admin / tradingbot123 |
| **📈 Prometheus** | http://localhost:9090 | Metrics & Queries | - |
| **🚨 Alertmanager** | http://localhost:9093 | Alert Management | - |
| **📊 cAdvisor** | http://localhost:8081 | Container Metrics | - |
| **💚 Uptime Kuma** | http://localhost:3001 | Service Monitoring | Ersteinrichtung |

### **Trading Bot APIs:**
| Endpoint | URL | Beschreibung |
|----------|-----|--------------|
| **🌐 Status** | http://localhost:8080/status | Bot Health & Config |
| **📊 Metrics** | http://localhost:8080/metrics | Prometheus Metrics |
| **❤️ Health** | http://localhost:8080/health | Liveness Check |

---

## 📊 VERFÜGBARE METRIKEN

### **🎯 Trading Performance**
- `signals_processed_total` - Verarbeitete Signale (mit Status)
- `signal_processing_duration_seconds` - Verarbeitungszeit
- `trading_operations_total` - Trading-Operationen
- `trading_errors_total` - Trading-Fehler

### **📡 Signal Sources**
- `cryptet_scraping_total` - Cryptet Scraping Events
- `cryptet_last_signal_timestamp` - Letztes Cryptet Signal
- `telegram_events_total` - Telegram Events
- `telegram_connection_status` - Verbindungsstatus

### **💾 System Health**
- `system_uptime_seconds` - System-Laufzeit
- `app_healthy` - Application Health (1=healthy, 0=unhealthy)
- `container_memory_usage_bytes` - Memory-Verbrauch
- `container_cpu_usage_seconds_total` - CPU-Nutzung

---

## 🚨 ALERT-KONFIGURATION

### **Kritische Alerts (Telegram-Benachrichtigung):**
- ❌ **Trading Bot Down** - Bot nicht erreichbar (30s)
- 🚨 **Signal Processing Errors** - >5 Fehler in 5min
- ⚠️ **Trading Errors** - >3 Fehler in 5min
- 📡 **Telegram Connection Lost** - Verbindung unterbrochen

### **Warning Alerts (Log-only):**
- ⚡ **High Signal Latency** - >5s Verarbeitungszeit
- 💾 **High Memory Usage** - >90% Memory
- 🔄 **High CPU Usage** - >80% CPU
- 📊 **No Trading Activity** - Keine Signale 10min

### **Cryptet-spezifische Alerts:**
- 🔧 **Scraping Errors** - >3 Fehler in 5min
- ⏰ **Signal Delay** - Kein Signal >1h

---

## 📈 GRAFANA DASHBOARD-FEATURES

### **🎯 Status Overview Panel**
- Bot Online/Offline Status
- Telegram Verbindungsstatus  
- System Uptime

### **📊 Performance Panels**
- Signal Processing Rate (Signale/Sekunde)
- Processing Latency (Verarbeitungszeit)
- Success Rate Trends

### **🚨 Error Monitoring**
- Fehlerrate nach Typ
- Error Rate Timeline
- Alert Status

### **💾 Resource Monitoring**
- Memory Usage
- CPU Usage  
- Container Health

### **📡 Trading Analytics**
- Trading Operations Rate
- Success vs. Failure Rate
- Cryptet Signal Activity

---

## ⚙️ KONFIGURATION

### **Prometheus Scraping:**
```yaml
# Trading Bot Metrics (5s interval)
- job_name: 'trading-bot'
  static_configs:
    - targets: ['trading-bot:8080']
  metrics_path: '/metrics'
  scrape_interval: 5s
```

### **Alert Thresholds anpassen:**
Editiere `monitoring/alerts.yaml`:
```yaml
# Beispiel: Signal Latency Threshold ändern
- alert: HighSignalProcessingLatency
  expr: signal_processing_duration_seconds > 10  # von 5s auf 10s
```

### **Grafana Dashboard Import:**
1. Login: http://localhost:3000 (admin/tradingbot123)
2. Dashboards → Import
3. JSON aus `monitoring/grafana/dashboards/trading-bot-dashboard.json`

---

## 🔧 MAINTENANCE

### **Log-Zugriff:**
```bash
# Alle Services
docker-compose -f docker-compose.monitoring.yml logs -f

# Specific Service
docker-compose -f docker-compose.monitoring.yml logs -f grafana
docker-compose -f docker-compose.monitoring.yml logs -f prometheus
```

### **Restart Services:**
```bash
# Alles neustarten
docker-compose -f docker-compose.monitoring.yml restart

# Einzelner Service
docker-compose -f docker-compose.monitoring.yml restart grafana
```

### **Backup & Recovery:**
```bash
# Volumes sichern
docker run --rm -v prometheus_data:/source -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz -C /source .
docker run --rm -v grafana_data:/source -v $(pwd):/backup alpine tar czf /backup/grafana-backup.tar.gz -C /source .

# Volumes wiederherstellen
docker run --rm -v prometheus_data:/target -v $(pwd):/backup alpine tar xzf /backup/prometheus-backup.tar.gz -C /target
```

---

## 🛠️ TROUBLESHOOTING

### **Container startet nicht:**
```bash
# Prüfe Container-Status
docker-compose -f docker-compose.monitoring.yml ps

# Prüfe Logs
docker-compose -f docker-compose.monitoring.yml logs [service_name]

# Ports prüfen
netstat -tulpn | grep -E ':(3000|9090|9093|8081|3001)'
```

### **Grafana Dashboard leer:**
1. Prüfe Prometheus Verbindung: http://localhost:9090
2. Prüfe Bot Metrics: http://localhost:8080/metrics
3. Prüfe Prometheus Targets: http://localhost:9090/targets

### **Keine Alerts:**
1. Prüfe Alertmanager: http://localhost:9093
2. Prüfe Alert Rules: http://localhost:9090/rules
3. Prüfe Webhook-Logs: `docker-compose logs trading-bot`

### **Performance Issues:**
```bash
# Resource Usage prüfen
docker stats

# Container Memory Limits
docker-compose -f docker-compose.monitoring.yml config
```

---

## 📱 MOBILE ZUGANG

### **Grafana Mobile App:**
1. Download: Grafana Mobile App
2. Server: http://[your-ip]:3000
3. Login: admin / tradingbot123

### **Uptime Kuma Mobile:**
- Responsive Web-Interface
- Push-Notifications möglich
- Status-Page verfügbar

---

## 🔒 SECURITY NOTES

### **Produktions-Deployment:**
- Ändere default Grafana Passwort
- Verwende HTTPS mit Reverse Proxy
- Restricte Port-Zugang mit Firewall
- Implementiere Authentication für APIs

### **Netzwerk-Sicherheit:**
```yaml
# Beispiel nginx-proxy für HTTPS
networks:
  monitoring:
    external: true
```

---

## 🎯 NEXT STEPS

1. **📱 Alerts konfigurieren** - Telegram/Email-Benachrichtigungen
2. **📊 Custom Dashboards** - Zusätzliche Business-Metriken
3. **🔐 Production Security** - HTTPS, Authentication
4. **📈 Long-term Storage** - InfluxDB/TimescaleDB Integration
5. **🚀 Auto-Scaling** - Kubernetes Deployment

---

## 💡 TIPS & TRICKS

### **Custom Metrics hinzufügen:**
```python
# In Ihrem Bot-Code
metrics.set_gauge('custom_metric_name', value, {'label': 'value'})
```

### **Dashboard Alerts konfigurieren:**
- Grafana Alerting Rules nutzen
- Notification Channels einrichten
- Silence Rules für Maintenance

### **Performance Optimization:**
- Prometheus Retention anpassen
- Grafana Query-Caching aktivieren
- Alert-Debouncing konfigurieren

---

**🎉 Ihr Trading Bot ist jetzt vollständig überwacht und produktionsbereit!**