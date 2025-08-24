#!/usr/bin/env python3
"""Health Check für Signal Parser Service"""

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
        await redis_client.close()
        
        print("✅ Signal Parser healthy")
        return True
        
    except Exception as e:
        print(f"❌ Signal Parser unhealthy: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(health_check())
    sys.exit(0 if result else 1)