#!/usr/bin/env python3
"""
Health Check für Telegram Receiver Service
"""

import sys
import os
import asyncio
import redis.asyncio as redis

async def check_health():
    """Prüft ob der Service gesund ist."""
    try:
        # Redis Connection prüfen
        redis_url = os.getenv("REDIS_URL", "redis://trading-bot-redis:6379/0")
        redis_client = redis.from_url(redis_url)
        
        # Redis Ping
        await redis_client.ping()
        await redis_client.aclose()
        
        print("✅ Health check passed")
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(check_health())
    sys.exit(0 if result else 1)