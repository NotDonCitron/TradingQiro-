#!/usr/bin/env python3
"""Health Check für Signal Forwarder Service"""

import os
import sys
import redis.asyncio as redis
import asyncio

async def health_check():
    try:
        redis_url = os.getenv("REDIS_URL", "redis://trading-bot-redis:6379/0")
        redis_client = redis.from_url(redis_url)
        
        # Test Redis Connection
        await redis_client.ping()
        
        # Test Bot Token
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            raise Exception("TELEGRAM_BOT_TOKEN not set")
        
        await redis_client.close()
        
        print("✅ Signal Forwarder healthy")
        return True
        
    except Exception as e:
        print(f"❌ Signal Forwarder unhealthy: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(health_check())
    sys.exit(0 if result else 1)