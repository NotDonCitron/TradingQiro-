# 🚀 Deployment Guides

## 📋 Overview

This document provides comprehensive deployment guides for different environments, including local development, Docker, Kubernetes, and production deployments.

---

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL (or use Docker)
- Chrome/Chromium browser
- Git

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd trading-bot
```

### Step 2: Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Database Setup
```bash
# Using local PostgreSQL
createdb trading_bot

# Or using Docker
docker run --name trading-bot-db -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:15
```

### Step 5: Configuration
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Step 6: Database Migrations
```bash
alembic upgrade head
```

### Step 7: Run Application
```bash
python src/main.py
```

### Step 8: Verify Setup
```bash
curl http://localhost:8080/health
curl http://localhost:8080/status
```

---

## 🐳 Docker Deployment

### Prerequisites
- Docker
- Docker Compose

### Quick Start
```bash
# Clone and setup
git clone <repository-url>
cd trading-bot

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Build and start
docker-compose up --build
```

### Docker Compose Configuration

**File**: `docker-compose.yml`
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: change-me-in-production
      POSTGRES_DB: trading_bot
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  bot:
    build: .
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8080:8080"
      - "9090:9090"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:change-me-in-production@db:5432/trading_bot
      - TRADING_ENABLED=false
      - BINGX_TESTNET=true
      - LOG_LEVEL=INFO
```

### Environment Variables for Docker

**File**: `.env`
```bash
# Telegram API
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token

# BingX API (if trading enabled)
BINGX_API_KEY=your_api_key
BINGX_SECRET_KEY=your_secret_key

# Cryptet Automation
CRYPTET_ENABLED=true
OWN_GROUP_CHAT_ID=-1001234567890

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=strong-password-here
POSTGRES_DB=trading_bot
```

### Useful Docker Commands

```bash
# Build and start
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f bot
docker-compose logs -f db

# Run migrations
docker-compose exec bot alembic upgrade head

# Run tests
docker-compose exec bot pytest

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes cluster
- Helm
- kubectl

### Helm Chart Structure

**File**: `helm/trading-bot/Chart.yaml`
```yaml
apiVersion: v2
name: trading-bot
description: Trading Bot for Telegram signal processing
version: 0.1.0
type: application
```

### Values Configuration

**File**: `helm/trading-bot/values.yaml`
```yaml
replicaCount: 1

image:
  repository: ghcr.io/myorg/trading-bot
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: ClusterIP
  port: 8080

env:
  TRADING_ENABLED: "false"
  BINGX_TESTNET: "true"
  LOG_LEVEL: "INFO"

secrets: {}
```

### Deployment Steps

#### Step 1: Build and Push Docker Image
```bash
docker build -t ghcr.io/myorg/trading-bot:latest .
docker push ghcr.io/myorg/trading-bot:latest
```

#### Step 2: Create Kubernetes Secrets
```bash
kubectl create secret generic trading-bot-secrets \
  --from-literal=telegram_api_id="$TELEGRAM_API_ID" \
  --from-literal=telegram_api_hash="$TELEGRAM_API_HASH" \
  --from-literal=telegram_bot_token="$TELEGRAM_BOT_TOKEN" \
  --from-literal=database_url="$DATABASE_URL" \
  --from-literal=bingx_api_key="$BINGX_API_KEY" \
  --from-literal=bingx_secret_key="$BINGX_SECRET_KEY"
```

#### Step 3: Deploy with Helm
```bash
helm install trading-bot ./helm/trading-bot \
  --set image.tag=latest \
  --set env.TRADING_ENABLED=true
```

#### Step 4: Verify Deployment
```bash
kubectl get pods
kubectl get services
kubectl logs deployment/trading-bot
```

### Kubernetes Manifests

#### Deployment
**File**: `helm/trading-bot/templates/deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Chart.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Chart.Name }}
  template:
    metadata:
      labels:
        app: {{ .Chart.Name }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: {{ .Values.service.port }}
        - containerPort: 9090
        env:
        - name: TRADING_ENABLED
          value: {{ .Values.env.TRADING_ENABLED | quote }}
        - name: BINGX_TESTNET
          value: {{ .Values.env.BINGX_TESTNET | quote }}
        - name: LOG_LEVEL
          value: {{ .Values.env.LOG_LEVEL | quote }}
        envFrom:
        - secretRef:
            name: trading-bot-secrets
```

#### Service
**File**: `helm/trading-bot/templates/service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Chart.Name }}
spec:
  type: {{ .Values.service.type }}
  ports:
  - port: {{ .Values.service.port }}
    targetPort: {{ .Values.service.port }}
    protocol: TCP
    name: http
  - port: 9090
    targetPort: 9090
    protocol: TCP
    name: metrics
  selector:
    app: {{ .Chart.Name }}
```

---

## 🌐 Production Deployment

### Production Checklist

- [ ] Use production Docker image tags
- [ ] Set `TRADING_ENABLED=true`
- [ ] Set `BINGX_TESTNET=false`
- [ ] Configure proper database backups
- [ ] Set up monitoring and alerting
- [ ] Configure SSL/TLS termination
- [ ] Set up log aggregation
- [ ] Configure auto-scaling
- [ ] Test disaster recovery procedures

### Production Environment Variables

**File**: `.env.production`
```bash
# Core
TRADING_ENABLED=true
BINGX_TESTNET=false
LOG_LEVEL=INFO

# Telegram
TELEGRAM_API_ID=production_api_id
TELEGRAM_API_HASH=production_api_hash
TELEGRAM_BOT_TOKEN=production_bot_token

# BingX
BINGX_API_KEY=production_api_key
BINGX_SECRET_KEY=production_secret_key

# Cryptet
CRYPTET_ENABLED=true
OWN_GROUP_CHAT_ID=-100production_group_id

# Database
DATABASE_URL=postgresql+asyncpg://user:strong-password@prod-db:5432/trading_bot

# Monitoring
PROMETHEUS_ENABLED=true
ALERTMANAGER_URL=http://alertmanager:9093
```

### High Availability Setup

#### Database High Availability
```yaml
# Use managed database service or replicas
database_url: postgresql+asyncpg://user:password@prod-db-primary:5432,prod-db-replica:5432/trading_bot
```

#### Application Scaling
```bash
# Scale deployment
kubectl scale deployment trading-bot --replicas=3

# Or use HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: trading-bot
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: trading-bot
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 📊 Monitoring Deployment

### Prometheus Setup

**File**: `monitoring/prometheus.yml`
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'trading-bot'
    static_configs:
      - targets: ['trading-bot:9090']
    metrics_path: /metrics
```

### Grafana Dashboard

**File**: `monitoring/grafana/dashboards/trading-bot-dashboard.json`
```json
{
  "title": "Trading Bot Dashboard",
  "panels": [
    {
      "title": "Order Processing",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(orders_total[5m])",
          "legendFormat": "Orders/min"
        }
      ]
    }
  ]
}
```

### Alertmanager Configuration

**File**: `monitoring/alertmanager.yml`
```yaml
route:
  group_by: ['alertname']
  receiver: 'telegram-alerts'

receivers:
- name: 'telegram-alerts'
  webhook_configs:
  - url: 'http://trading-bot:8080/webhook/critical-alert'
```

---

## 🔧 Custom Deployments

### Raspberry Pi Deployment

**Dockerfile.raspberrypi**
```dockerfile
FROM arm32v7/python:3.11-slim

# ARM-specific dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver

# Rest of setup similar to main Dockerfile
```

### Cloud-Specific Deployments

#### AWS ECS Deployment
```bash
# ECS task definition
aws ecs register-task-definition \
  --family trading-bot \
  --container-definitions file://ecs-container-def.json
```

#### Google Cloud Run
```bash
# Deploy to Cloud Run
gcloud run deploy trading-bot \
  --image gcr.io/my-project/trading-bot \
  --set-env-vars TRADING_ENABLED=false
```

#### Azure Container Apps
```bash
# Deploy to Azure
az containerapp create \
  --name trading-bot \
  --image myregistry.azurecr.io/trading-bot:latest \
  --environment-variables TRADING_ENABLED=false
```

---

## 🧪 Testing Deployments

### Health Checks
```bash
# Basic health check
curl http://localhost:8080/health

# Detailed status
curl http://localhost:8080/status

# Metrics endpoint
curl http://localhost:8080/metrics
```

### Integration Tests
```bash
# Test signal processing
curl -X POST http://localhost:8080/signal \
  -H "Content-Type: application/json" \
  -d '{"message": "BUY BTCUSDT 0.1", "metadata": {"source": "test"}}'

# Test Cryptet automation
curl -X POST http://localhost:8080/cryptet/test \
  -H "Content-Type: application/json" \
  -d '{"url": "https://cryptet.com/signal/1234567890"}'
```

### Load Testing
```bash
# Using k6 for load testing
k6 run --vus 10 --duration 30s load-test.js
```

**load-test.js**
```javascript
import http from 'k6/http';

export default function() {
  http.get('http://localhost:8080/health');
  http.post('http://localhost:8080/signal', JSON.stringify({
    message: "BUY BTCUSDT 0.1",
    metadata: {source: "test"}
  }), {
    headers: {'Content-Type': 'application/json'}
  });
}
```

---

## 🚨 Troubleshooting Deployments

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec db psql -U postgres -d trading_bot

# Check migrations
docker-compose exec bot alembic current
```

#### Telegram Connection Issues
```bash
# Check Telegram API credentials
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Verify bot is added to groups
```

#### Exchange API Issues
```bash
# Test BingX connectivity
curl "https://api-swap-testnet.bingx.com/api/v1/ticker/price?symbol=BTC-USDT"
```

### Log Analysis
```bash
# View application logs
docker-compose logs -f bot

# View database logs
docker-compose logs -f db

# Kubernetes logs
kubectl logs -f deployment/trading-bot
```

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG
CRYPTET_HEADLESS=false

# Run with debug
docker-compose up --build
```

---

## 📈 Performance Optimization

### Database Optimization
```sql
-- Create indexes for performance
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

### Application Optimization
```bash
# Increase connection pool
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=20

# Optimize Python
PYTHONOPTIMIZE=2
```

### Monitoring Optimization
```bash
# Reduce metrics scrape interval
SCRAPE_INTERVAL=30s

# Filter metrics
METRICS_FILTER=orders_total,orders_failed_total
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

**File**: `.github/workflows/deploy.yml`
```yaml
name: Deploy Trading Bot

on:
  push:
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .
    
    - name: Push to GitHub Container Registry
      run: docker push ghcr.io/${{ github.repository }}:${{ github.sha }}
    
    - name: Deploy to Kubernetes
      run: |
        echo "$KUBECONFIG" > kubeconfig.yaml
        helm upgrade trading-bot ./helm/trading-bot \
          --set image.tag=${{ github.sha }} \
          --kubeconfig kubeconfig.yaml
      env:
        KUBECONFIG: ${{ secrets.KUBECONFIG }}
```

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Test in staging environment
- [ ] Backup database
- [ ] Verify configuration
- [ ] Check dependencies
- [ ] Test monitoring

### During Deployment
- [ ] Deploy database migrations
- [ ] Update application
- [ ] Verify health checks
- [ ] Test critical functionality

### Post-Deployment
- [ ] Monitor performance
- [ ] Check error rates
- [ ] Verify alerts working
- [ ] Update documentation

**Remember**: Always deploy to a test environment first and verify everything works before production!