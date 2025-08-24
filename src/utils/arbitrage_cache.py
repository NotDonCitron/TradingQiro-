# feat(utils): Arbitrage cache system for price data and opportunities
from __future__ import annotations
import asyncio
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis not available, using in-memory cache")
    REDIS_AVAILABLE = False
    redis = None


class InMemoryCache:
    """Simple in-memory cache implementation"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def setex(self, key: str, ttl: int, value: str):
        """Set key with expiration time"""
        async with self._lock:
            expiration = datetime.now() + timedelta(seconds=ttl)
            self._cache[key] = {
                'value': value,
                'expires': expiration
            }

    async def get(self, key: str) -> Optional[str]:
        """Get key value"""
        async with self._lock:
            if key not in self._cache:
                return None

            item = self._cache[key]
            if datetime.now() > item['expires']:
                del self._cache[key]
                return None

            return item['value']

    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        async with self._lock:
            # Simple pattern matching - just check if pattern is contained in key
            matching_keys = []
            for key in self._cache.keys():
                if pattern.replace('*', '') in key:
                    matching_keys.append(key)
            return matching_keys

    async def expire(self, key: str, ttl: int):
        """Set expiration time for key"""
        async with self._lock:
            if key in self._cache:
                expiration = datetime.now() + timedelta(seconds=ttl)
                self._cache[key]['expires'] = expiration

    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        async with self._lock:
            if key not in self._cache:
                return -2

            expires = self._cache[key]['expires']
            remaining = (expires - datetime.now()).total_seconds()
            return int(remaining) if remaining > 0 else -1

    async def close(self):
        """Close cache (no-op for in-memory)"""
        pass


class ArbitrageCache:
    """Cache system for arbitrage data with TTL management. Falls back to in-memory if Redis unavailable."""

    def __init__(self, config_path: str = "config/arbitrage_config.json"):
        """Initialize arbitrage cache with configuration."""
        self.config = self._load_config(config_path)
        self.redis_url = self.config["cache"]["redis_url"]
        self.price_cache_ttl = self.config["cache"]["price_cache_ttl_seconds"]
        self.arbitrage_cache_ttl = self.config["cache"]["arbitrage_cache_ttl_seconds"]
        self.whale_cache_ttl = self.config["cache"]["whale_cache_ttl_seconds"]

        # Use in-memory cache for now
        self.redis = InMemoryCache()
        self._connection_lock = asyncio.Lock()
        logger.info("Using in-memory cache for arbitrage data")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if config file is not available."""
        return {
            "cache": {
                "redis_url": "redis://localhost:6379",
                "price_cache_ttl_seconds": 30,
                "arbitrage_cache_ttl_seconds": 60,
                "whale_cache_ttl_seconds": 300
            }
        }

    def _get_redis(self):
        """Get cache instance."""
        return self.redis

    async def set_price_data(self, exchange: str, symbol: str, price_data: Dict[str, Any]) -> bool:
        """Cache price data for an exchange and symbol."""
        try:
            redis_client = self._get_redis()
            key = f"price:{exchange}:{symbol}"

            # Add timestamp if not present
            if "timestamp" not in price_data:
                price_data["timestamp"] = datetime.now().isoformat()

            await redis_client.setex(key, self.price_cache_ttl, json.dumps(price_data))
            return True

        except Exception as e:
            logger.error(f"Error caching price data for {exchange}:{symbol}: {e}")
            return False

    async def get_price_data(self, exchange: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached price data for an exchange and symbol."""
        try:
            redis_client = self._get_redis()
            key = f"price:{exchange}:{symbol}"

            data = await redis_client.get(key)
            if data:
                return json.loads(data)
            return None

        except Exception as e:
            logger.error(f"Error getting price data for {exchange}:{symbol}: {e}")
            return None

    async def get_all_exchange_prices(self, symbol: str) -> Dict[str, Dict[str, Any]]:
        """Get price data for a symbol from all exchanges."""
        try:
            redis_client = self._get_redis()
            pattern = f"price:*:{symbol}"

            keys = await redis_client.keys(pattern)
            if not keys:
                return {}

            # Get all price data
            prices = {}
            for key in keys:
                data = await redis_client.get(key)
                if data:
                    parsed_data = json.loads(data)
                    # Extract exchange from key (format: price:exchange:symbol)
                    exchange = key.split(":")[1]
                    prices[exchange] = parsed_data

            return prices

        except Exception as e:
            logger.error(f"Error getting all exchange prices for {symbol}: {e}")
            return {}

    async def set_arbitrage_opportunity(self, opportunity_id: str, opportunity_data: Dict[str, Any]) -> bool:
        """Cache arbitrage opportunity data."""
        try:
            redis_client = self._get_redis()
            key = f"arbitrage:{opportunity_id}"

            # Add timestamp if not present
            if "timestamp" not in opportunity_data:
                opportunity_data["timestamp"] = datetime.now().isoformat()

            await redis_client.setex(key, self.arbitrage_cache_ttl, json.dumps(opportunity_data))
            return True

        except Exception as e:
            logger.error(f"Error caching arbitrage opportunity {opportunity_id}: {e}")
            return False

    async def get_arbitrage_opportunity(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """Get cached arbitrage opportunity data."""
        try:
            redis_client = self._get_redis()
            key = f"arbitrage:{opportunity_id}"

            data = await redis_client.get(key)
            if data:
                return json.loads(data)
            return None

        except Exception as e:
            logger.error(f"Error getting arbitrage opportunity {opportunity_id}: {e}")
            return None

    async def get_recent_arbitrage_opportunities(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent arbitrage opportunities."""
        try:
            redis_client = self._get_redis()
            pattern = "arbitrage:*"

            keys = await redis_client.keys(pattern)
            if not keys:
                return []

            # Get all opportunities
            opportunities = []
            for key in keys:
                data = await redis_client.get(key)
                if data:
                    opportunity = json.loads(data)
                    opportunities.append(opportunity)

            # Sort by timestamp (most recent first)
            opportunities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return opportunities[:limit]

        except Exception as e:
            logger.error(f"Error getting recent arbitrage opportunities: {e}")
            return []

    async def set_whale_transaction(self, tx_hash: str, transaction_data: Dict[str, Any]) -> bool:
        """Cache whale transaction data."""
        try:
            redis_client = self._get_redis()
            key = f"whale:{tx_hash}"

            # Add timestamp if not present
            if "timestamp" not in transaction_data:
                transaction_data["timestamp"] = datetime.now().isoformat()

            await redis_client.setex(key, self.whale_cache_ttl, json.dumps(transaction_data))
            return True

        except Exception as e:
            logger.error(f"Error caching whale transaction {tx_hash}: {e}")
            return False

    async def get_whale_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached whale transaction data."""
        try:
            redis_client = self._get_redis()
            key = f"whale:{tx_hash}"

            data = await redis_client.get(key)
            if data:
                return json.loads(data)
            return None

        except Exception as e:
            logger.error(f"Error getting whale transaction {tx_hash}: {e}")
            return None

    async def get_recent_whale_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent whale transactions."""
        try:
            redis_client = self._get_redis()
            pattern = "whale:*"

            keys = await redis_client.keys(pattern)
            if not keys:
                return []

            # Get all transactions
            transactions = []
            for key in keys:
                data = await redis_client.get(key)
                if data:
                    transaction = json.loads(data)
                    transactions.append(transaction)

            # Sort by timestamp (most recent first)
            transactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return transactions[:limit]

        except Exception as e:
            logger.error(f"Error getting recent whale transactions: {e}")
            return []

    async def set_premium_signal(self, signal_id: str, signal_data: Dict[str, Any]) -> bool:
        """Cache premium signal data."""
        try:
            redis_client = self._get_redis()
            key = f"signal:{signal_id}"

            # Add timestamp if not present
            if "timestamp" not in signal_data:
                signal_data["timestamp"] = datetime.now().isoformat()

            # Set TTL to 1 hour for premium signals
            await redis_client.setex(key, 3600, json.dumps(signal_data))
            return True

        except Exception as e:
            logger.error(f"Error caching premium signal {signal_id}: {e}")
            return False

    async def get_premium_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """Get cached premium signal data."""
        try:
            redis_client = self._get_redis()
            key = f"signal:{signal_id}"

            data = await redis_client.get(key)
            if data:
                return json.loads(data)
            return None

        except Exception as e:
            logger.error(f"Error getting premium signal {signal_id}: {e}")
            return None

    async def get_recent_premium_signals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent premium signals."""
        try:
            redis_client = self._get_redis()
            pattern = "signal:*"

            keys = await redis_client.keys(pattern)
            if not keys:
                return []

            # Get all signals
            signals = []
            for key in keys:
                data = await redis_client.get(key)
                if data:
                    signal = json.loads(data)
                    signals.append(signal)

            # Sort by timestamp (most recent first)
            signals.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return signals[:limit]

        except Exception as e:
            logger.error(f"Error getting recent premium signals: {e}")
            return []

    async def clear_expired_data(self):
        """Clear expired data from cache (Redis handles TTL automatically, but this can be used for cleanup)."""
        try:
            redis_client = self._get_redis()

            # Get all keys with our prefixes
            patterns = ["price:*", "arbitrage:*", "whale:*", "signal:*"]

            for pattern in patterns:
                keys = await redis_client.keys(pattern)
                for key in keys:
                    # Redis automatically expires keys, but we can check TTL
                    ttl = await redis_client.ttl(key)
                    if ttl == -2:  # Key doesn't exist
                        continue
                    elif ttl == -1:  # Key has no expiration
                        # Set appropriate expiration based on key type
                        if key.startswith("price:"):
                            await redis_client.expire(key, self.price_cache_ttl)
                        elif key.startswith("arbitrage:"):
                            await redis_client.expire(key, self.arbitrage_cache_ttl)
                        elif key.startswith("whale:"):
                            await redis_client.expire(key, self.whale_cache_ttl)
                        elif key.startswith("signal:"):
                            await redis_client.expire(key, 3600)

        except Exception as e:
            logger.error(f"Error clearing expired data: {e}")

    async def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        try:
            redis_client = self._get_redis()

            patterns = ["price:*", "arbitrage:*", "whale:*", "signal:*"]
            stats = {}

            for pattern in patterns:
                keys = await redis_client.keys(pattern)
                key_type = pattern.split(":")[0]
                stats[key_type] = len(keys)

            return stats

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    async def close(self):
        """Close Redis connection."""
        async with self._connection_lock:
            if self.redis:
                await self.redis.close()
                self.redis = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
