#!/usr/bin/env python3
"""
API Gateway Service
Bietet Health Checks und Service-Monitoring für die Docker Services
"""

import asyncio
import json
import os
import redis.asyncio as redis
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Trading Bot API Gateway",
    description="Service-Monitoring und Health Checks für Docker Services",
    version="1.0.0"
)

class APIGateway:
    """API Gateway für Service-Monitoring."""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://trading-bot-redis:6379/0")
        self.redis_client = None
        
    async def connect_redis(self):
        """Verbindet mit Redis."""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            return True
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False

# Global Gateway Instance
gateway = APIGateway()

@app.on_event("startup")
async def startup_event():
    """Startup Event Handler."""
    print("🚀 Starting API Gateway...")
    await gateway.connect_redis()
    print("✅ API Gateway ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown Event Handler."""
    if gateway.redis_client:
        await gateway.redis_client.close()

@app.get("/health")
async def health_check():
    """Health Check Endpoint."""
    try:
        # Redis Health
        redis_healthy = False
        if gateway.redis_client:
            await gateway.redis_client.ping()
            redis_healthy = True
        
        health_status = {
            "status": "healthy" if redis_healthy else "unhealthy",
            "timestamp": "2025-08-24T12:00:00Z",
            "services": {
                "redis": "healthy" if redis_healthy else "unhealthy",
                "api_gateway": "healthy"
            }
        }
        
        status_code = 200 if redis_healthy else 503
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e)},
            status_code=503
        )

@app.get("/services")
async def service_status():
    """Service Status Overview."""
    try:
        if not gateway.redis_client:
            raise Exception("Redis not connected")
        
        # Queue Sizes
        telegram_queue_size = await gateway.redis_client.llen("telegram_messages")
        signal_queue_size = await gateway.redis_client.llen("parsed_signals")
        
        # Recent Logs
        recent_logs = await gateway.redis_client.lrange("forwarding_logs", 0, 4)
        
        status = {
            "services": {
                "telegram-receiver": {
                    "status": "running",
                    "description": "Empfängt Telegram-Nachrichten"
                },
                "signal-parser": {
                    "status": "running", 
                    "description": "Parsed empfangene Signale",
                    "queue_size": int(telegram_queue_size)
                },
                "signal-forwarder": {
                    "status": "running",
                    "description": "Leitet Signale weiter",
                    "queue_size": int(signal_queue_size)
                }
            },
            "queues": {
                "telegram_messages": int(telegram_queue_size),
                "parsed_signals": int(signal_queue_size)
            },
            "recent_activity": [
                json.loads(log) if log else {} for log in recent_logs
            ]
        }
        
        return JSONResponse(content=status)
        
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.get("/metrics")
async def metrics():
    """Einfache Metriken für Monitoring."""
    try:
        if not gateway.redis_client:
            raise Exception("Redis not connected")
        
        # Queue Sizes
        telegram_queue = await gateway.redis_client.llen("telegram_messages")
        signal_queue = await gateway.redis_client.llen("parsed_signals")
        
        # Logs Count
        logs_count = await gateway.redis_client.llen("forwarding_logs")
        
        metrics_data = {
            "queue_telegram_messages": int(telegram_queue),
            "queue_parsed_signals": int(signal_queue), 
            "total_forwarded_signals": int(logs_count),
            "system_healthy": 1 if telegram_queue >= 0 else 0
        }
        
        return JSONResponse(content=metrics_data)
        
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.post("/test/signal")
async def test_signal_injection():
    """Test-Endpoint zum Einschleusen eines Test-Signals."""
    try:
        if not gateway.redis_client:
            raise Exception("Redis not connected")
        
        # Test Signal
        test_message = {
            "text": """🟢 Long
Name: BTCUSDT
Margin mode: Cross (10.0X)

↪️ Entry price(USDT):
45000.0

Targets(USDT):
1) 45500.0
2) 46000.0
3) 46500.0""",
            "chat_id": -1002299206473,
            "message_id": 99999,
            "sender_id": 12345,
            "timestamp": "2025-08-24T12:00:00Z",
            "source": "test_injection"
        }
        
        # In Queue einreihen
        await gateway.redis_client.lpush(
            "telegram_messages",
            json.dumps(test_message)
        )
        
        return JSONResponse(content={
            "success": True,
            "message": "Test signal injected into queue",
            "signal": test_message
        })
        
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    uvicorn.run(
        "api_gateway:app",
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )