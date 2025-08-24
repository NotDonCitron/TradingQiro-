# feat(connector): Multi-exchange API connectors for arbitrage
from __future__ import annotations
import asyncio
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class ExchangeConnector(ABC):
    """Abstract base class for exchange connectors."""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.api_key = os.getenv(config["api_key_env"])
        self.secret_key = os.getenv(config["secret_key_env"]) if config.get("secret_key_env") else None
        self.testnet = config.get("testnet", False)
        self.rate_limit = config.get("rate_limit", 1000)
        self.fee_structure = config.get("fee_structure", {"maker": 0.001, "taker": 0.001})

        # Rate limiting
        self._request_times = []
        self._min_request_interval = 60 / self.rate_limit

    @abstractmethod
    async def get_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price for a symbol."""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ticker information for a symbol."""
        pass

    @abstractmethod
    async def get_order_book(self, symbol: str, depth: int = 20) -> Optional[Dict[str, Any]]:
        """Get order book for a symbol."""
        pass

    async def _rate_limit_wait(self):
        """Enforce rate limiting."""
        now = datetime.now()

        # Clean old request times
        cutoff = now.replace(second=0, microsecond=0)
        cutoff = cutoff.replace(minute=cutoff.minute - 1)
        self._request_times = [t for t in self._request_times if t > cutoff]

        if len(self._request_times) >= self.rate_limit:
            # Wait until we can make another request
            oldest_request = min(self._request_times)
            wait_time = 60 - (now - oldest_request).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self._request_times.append(now)

    def calculate_fees(self, amount: float, is_maker: bool = False) -> float:
        """Calculate trading fees for an amount."""
        fee_rate = self.fee_structure["maker"] if is_maker else self.fee_structure["taker"]
        return amount * fee_rate

class BinanceConnector(ExchangeConnector):
    """Binance exchange connector."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("binance", config)
        self.base_url = "https://testnet.binance.vision" if self.testnet else "https://api.binance.com"

    async def get_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price from Binance."""
        try:
            await self._rate_limit_wait()

            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v3/ticker/price"
                params = {"symbol": symbol.replace("/", "")}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "exchange": self.name,
                            "symbol": symbol,
                            "price": float(data["price"]),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"Binance API error: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error getting price from Binance: {e}")
            return None

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ticker information from Binance."""
        try:
            await self._rate_limit_wait()

            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v3/ticker/24hr"
                params = {"symbol": symbol.replace("/", "")}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "exchange": self.name,
                            "symbol": symbol,
                            "bid_price": float(data["bidPrice"]),
                            "ask_price": float(data["askPrice"]),
                            "volume_24h": float(data["volume"]),
                            "price_change_percent": float(data["priceChangePercent"]),
                            "last_price": float(data["lastPrice"]),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"Binance ticker API error: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error getting ticker from Binance: {e}")
            return None

    async def get_order_book(self, symbol: str, depth: int = 20) -> Optional[Dict[str, Any]]:
        """Get order book from Binance."""
        try:
            await self._rate_limit_wait()

            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v3/depth"
                params = {"symbol": symbol.replace("/", ""), "limit": depth}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "exchange": self.name,
                            "symbol": symbol,
                            "bids": [[float(price), float(qty)] for price, qty in data["bids"]],
                            "asks": [[float(price), float(qty)] for price, qty in data["asks"]],
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"Binance order book API error: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error getting order book from Binance: {e}")
            return None

class CoinbaseConnector(ExchangeConnector):
    """Coinbase Pro exchange connector."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("coinbase", config)
        self.base_url = "https://api-public.sandbox.pro.coinbase.com" if config.get("sandbox") else "https://api.pro.coinbase.com"

    async def get_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price from Coinbase."""
        try:
            await self._rate_limit_wait()

            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Coinbase uses different symbol format (BTC-USD instead of BTC/USD)
                coinbase_symbol = symbol.replace("/", "-")
                url = f"{self.base_url}/products/{coinbase_symbol}/ticker"

                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "exchange": self.name,
                            "symbol": symbol,
                            "price": float(data["price"]),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"Coinbase API error: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error getting price from Coinbase: {e}")
            return None

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ticker information from Coinbase."""
        try:
            await self._rate_limit_wait()

            import aiohttp
            async with aiohttp.ClientSession() as session:
                coinbase_symbol = symbol.replace("/", "-")
                url = f"{self.base_url}/products/{coinbase_symbol}/stats"

                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "exchange": self.name,
                            "symbol": symbol,
                            "bid_price": float(data.get("high", 0)),
                            "ask_price": float(data.get("low", 0)),
                            "volume_24h": float(data.get("volume", 0)),
                            "last_price": float(data.get("last", 0)),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"Coinbase ticker API error: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error getting ticker from Coinbase: {e}")
            return None

    async def get_order_book(self, symbol: str, depth: int = 20) -> Optional[Dict[str, Any]]:
        """Get order book from Coinbase."""
        try:
            await self._rate_limit_wait()

            import aiohttp
            async with aiohttp.ClientSession() as session:
                coinbase_symbol = symbol.replace("/", "-")
                url = f"{self.base_url}/products/{coinbase_symbol}/book"
                params = {"level": 2}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "exchange": self.name,
                            "symbol": symbol,
                            "bids": [[float(price), float(qty)] for price, qty in data.get("bids", [])[:depth]],
                            "asks": [[float(price), float(qty)] for price, qty in data.get("asks", [])[:depth]],
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"Coinbase order book API error: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error getting order book from Coinbase: {e}")
            return None

class KrakenConnector(ExchangeConnector):
    """Kraken exchange connector."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("kraken", config)
        self.base_url = "https://api.kraken.com"

    async def get_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price from Kraken."""
        try:
            await self._rate_limit_wait()

            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Kraken uses different symbol format (XXBTZUSD instead of BTC/USD)
                kraken_symbol = self._convert_symbol(symbol)
                url = f"{self.base_url}/0/public/Ticker"
                params = {"pair": kraken_symbol}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("error"):
                            logger.error(f"Kraken API error: {data['error']}")
                            return None

                        result = data.get("result", {})
                        if kraken_symbol in result:
                            ticker_data = result[kraken_symbol]
                            return {
                                "exchange": self.name,
                                "symbol": symbol,
                                "price": float(ticker_data["c"][0]),  # Last trade closed price
                                "timestamp": datetime.now().isoformat()
                            }
                        return None
                    else:
                        logger.error(f"Kraken API error: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error getting price from Kraken: {e}")
            return None

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ticker information from Kraken."""
        try:
            await self._rate_limit_wait()

            import aiohttp
            async with aiohttp.ClientSession() as session:
                kraken_symbol = self._convert_symbol(symbol)
                url = f"{self.base_url}/0/public/Ticker"
                params = {"pair": kraken_symbol}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("error"):
                            logger.error(f"Kraken ticker API error: {data['error']}")
                            return None

                        result = data.get("result", {})
                        if kraken_symbol in result:
                            ticker_data = result[kraken_symbol]
                            return {
                                "exchange": self.name,
                                "symbol": symbol,
                                "bid_price": float(ticker_data["b"][0]),
                                "ask_price": float(ticker_data["a"][0]),
                                "volume_24h": float(ticker_data["v"][1]),  # 24h volume
                                "last_price": float(ticker_data["c"][0]),
                                "timestamp": datetime.now().isoformat()
                            }
                        return None
                    else:
                        logger.error(f"Kraken ticker API error: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error getting ticker from Kraken: {e}")
            return None

    async def get_order_book(self, symbol: str, depth: int = 20) -> Optional[Dict[str, Any]]:
        """Get order book from Kraken."""
        try:
            await self._rate_limit_wait()

            import aiohttp
            async with aiohttp.ClientSession() as session:
                kraken_symbol = self._convert_symbol(symbol)
                url = f"{self.base_url}/0/public/Depth"
                params = {"pair": kraken_symbol, "count": depth}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("error"):
                            logger.error(f"Kraken order book API error: {data['error']}")
                            return None

                        result = data.get("result", {})
                        if kraken_symbol in result:
                            book_data = result[kraken_symbol]
                            return {
                                "exchange": self.name,
                                "symbol": symbol,
                                "bids": [[float(price), float(qty)] for price, qty in book_data["bids"]],
                                "asks": [[float(price), float(qty)] for price, qty in book_data["asks"]],
                                "timestamp": datetime.now().isoformat()
                            }
                        return None
                    else:
                        logger.error(f"Kraken order book API error: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error getting order book from Kraken: {e}")
            return None

    def _convert_symbol(self, symbol: str) -> str:
        """Convert standard symbol format to Kraken format."""
        # Kraken uses different naming conventions
        conversions = {
            "BTC/USD": "XXBTZUSD",
            "ETH/USD": "XETHZUSD",
            "LTC/USD": "XLTCZUSD",
            "ADA/USD": "ADAUSD",
            "DOT/USD": "DOTUSD"
        }
        return conversions.get(symbol, symbol.replace("/", ""))

class ExchangeManager:
    """Manager for multiple exchange connectors."""

    def __init__(self, config_path: str = "config/arbitrage_config.json"):
        """Initialize exchange manager with configuration."""
        self.config = self._load_config(config_path)
        self.exchanges = {}
        self._initialize_exchanges()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            return {"exchanges": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return {"exchanges": {}}

    def _initialize_exchanges(self):
        """Initialize exchange connectors based on configuration."""
        for exchange_name, exchange_config in self.config.get("exchanges", {}).items():
            if exchange_config.get("enabled", False):
                if exchange_name == "binance":
                    self.exchanges[exchange_name] = BinanceConnector(exchange_config)
                elif exchange_name == "coinbase":
                    self.exchanges[exchange_name] = CoinbaseConnector(exchange_config)
                elif exchange_name == "kraken":
                    self.exchanges[exchange_name] = KrakenConnector(exchange_config)
                elif exchange_name == "bingx":
                    # BingX would use similar structure to Binance
                    self.exchanges[exchange_name] = BinanceConnector(exchange_config)

    async def get_price_from_all_exchanges(self, symbol: str) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get price for a symbol from all enabled exchanges."""
        tasks = []
        for exchange_name, connector in self.exchanges.items():
            tasks.append(self._get_price_with_fallback(connector, symbol))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        price_data = {}
        for i, (exchange_name, _) in enumerate(self.exchanges.items()):
            result = results[i]
            if isinstance(result, Exception):
                logger.error(f"Error getting price from {exchange_name}: {result}")
                price_data[exchange_name] = None
            else:
                price_data[exchange_name] = result

        return price_data

    async def _get_price_with_fallback(self, connector: ExchangeConnector, symbol: str) -> Optional[Dict[str, Any]]:
        """Get price with retry logic."""
        for attempt in range(3):
            try:
                return await connector.get_price(symbol)
            except Exception as e:
                if attempt == 2:  # Last attempt
                    logger.error(f"Failed to get price from {connector.name} after 3 attempts: {e}")
                    return None
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return None

    async def get_ticker_from_exchange(self, exchange_name: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ticker from specific exchange."""
        if exchange_name not in self.exchanges:
            logger.error(f"Exchange {exchange_name} not configured")
            return None

        connector = self.exchanges[exchange_name]
        return await connector.get_ticker(symbol)

    async def get_order_book_from_exchange(self, exchange_name: str, symbol: str, depth: int = 20) -> Optional[Dict[str, Any]]:
        """Get order book from specific exchange."""
        if exchange_name not in self.exchanges:
            logger.error(f"Exchange {exchange_name} not configured")
            return None

        connector = self.exchanges[exchange_name]
        return await connector.get_order_book(symbol, depth)

    def get_enabled_exchanges(self) -> List[str]:
        """Get list of enabled exchanges."""
        return list(self.exchanges.keys())

    def get_exchange_connector(self, exchange_name: str) -> Optional[ExchangeConnector]:
        """Get exchange connector by name."""
        return self.exchanges.get(exchange_name)


class ExchangeAPIManager:
    """Manager for arbitrage-specific exchange API operations."""

    def __init__(self, config):
        self.config = config
        self.exchange_manager = ExchangeManager()
        logger.info("ExchangeAPIManager initialized")

    async def get_price_data(self, exchange_name: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get price data from a specific exchange for arbitrage analysis."""
        try:
            # Try ticker first for more complete data
            ticker_data = await self.exchange_manager.get_ticker_from_exchange(exchange_name, symbol)

            if ticker_data:
                # Normalize the data format for arbitrage scanner
                return {
                    'bid': ticker_data.get('bid_price', 0),
                    'ask': ticker_data.get('ask_price', 0),
                    'last': ticker_data.get('last_price', 0),
                    'volume_24h': ticker_data.get('volume_24h', 0),
                    'spread': 0  # Will be calculated if needed
                }

            # Fallback to price endpoint
            price_data = await self.exchange_manager.exchanges[exchange_name].get_price(symbol)
            if price_data:
                return {
                    'bid': price_data.get('price', 0),
                    'ask': price_data.get('price', 0),  # Assume bid = ask for simple price
                    'last': price_data.get('price', 0),
                    'volume_24h': 0,
                    'spread': 0
                }

            return None

        except Exception as e:
            logger.error("Error getting price data from %s for %s: %s", exchange_name, symbol, str(e))
            return None

    async def get_all_price_data(self, symbol: str) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get price data for a symbol from all enabled exchanges."""
        return await self.exchange_manager.get_price_from_all_exchanges(symbol)

    def get_enabled_exchanges(self) -> List[str]:
        """Get list of enabled exchanges."""
        return self.exchange_manager.get_enabled_exchanges()

    def get_exchange_config(self, exchange_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific exchange."""
        return self.exchange_manager.config.get('exchanges', {}).get(exchange_name)

    def calculate_fees(self, exchange_name: str, amount: float, is_maker: bool = False) -> float:
        """Calculate trading fees for an exchange."""
        connector = self.exchange_manager.get_exchange_connector(exchange_name)
        if connector:
            return connector.calculate_fees(amount, is_maker)
        return 0.0

    async def get_order_book(self, exchange_name: str, symbol: str, depth: int = 20) -> Optional[Dict[str, Any]]:
        """Get order book from a specific exchange."""
        return await self.exchange_manager.get_order_book_from_exchange(exchange_name, symbol, depth)
