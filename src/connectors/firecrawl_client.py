# feat(connector): Firecrawl client for premium signal scraping and market data
from __future__ import annotations
import asyncio
import json
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import aiohttp
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

class FirecrawlClient:
    """Client for Firecrawl API to scrape premium trading signals and market data."""

    def __init__(self, config_path: str = "config/arbitrage_config.json"):
        """Initialize Firecrawl client with configuration."""
        self.config = self._load_config(config_path)
        self.api_key = os.getenv(self.config["firecrawl"]["api_key_env"])
        self.base_url = self.config["firecrawl"]["base_url"]
        self.rate_limit = self.config["firecrawl"]["rate_limit"]
        self.premium_sources = self.config["firecrawl"]["premium_sources"]

        # Rate limiting
        self._request_times = []
        self._min_request_interval = 60 / self.rate_limit

        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()

        # Cache for scraped data
        self._cache = {}
        self._cache_expiry = {}

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
            "firecrawl": {
                "api_key_env": "FIRECRAWL_API_KEY",
                "base_url": "https://api.firecrawl.com",
                "rate_limit": 100,
                "premium_sources": []
            }
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        async with self._session_lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
            return self._session

    async def _rate_limit_wait(self):
        """Enforce rate limiting."""
        now = datetime.now()

        # Clean old request times
        cutoff = now - timedelta(seconds=60)
        self._request_times = [t for t in self._request_times if t > cutoff]

        if len(self._request_times) >= self.rate_limit:
            # Wait until we can make another request
            oldest_request = min(self._request_times)
            wait_time = 60 - (now - oldest_request).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self._request_times.append(now)

    async def scrape_premium_content(self, url: str, options: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Scrape premium content from a URL using Firecrawl."""
        if not self.api_key:
            logger.error("Firecrawl API key not configured")
            return None

        try:
            await self._rate_limit_wait()

            session = await self._get_session()

            # Default scraping options
            scrape_options = {
                "formats": ["markdown", "html"],
                "onlyMainContent": True,
                "includeTags": ["p", "div", "span", "h1", "h2", "h3", "table"],
                "excludeTags": ["script", "style", "nav", "footer", "aside"],
                "waitFor": 2000,
                "mobile": False
            }

            if options:
                scrape_options.update(options)

            payload = {
                "url": url,
                "scrapeOptions": scrape_options
            }

            async with session.post(f"{self.base_url}/v1/scrape", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "url": url,
                        "content": data.get("data", {}),
                        "scraped_at": datetime.now().isoformat(),
                        "success": True
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Firecrawl scrape failed: {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    async def batch_scrape_premium_sources(self, sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Batch scrape multiple premium sources."""
        if sources is None:
            sources = [source["url_patterns"] for source in self.premium_sources]
            # Flatten the list
            sources = [url for sublist in sources for url in sublist]

        tasks = []
        for url in sources:
            tasks.append(self.scrape_premium_content(url))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and None results
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch scrape error: {result}")
            elif result is not None:
                valid_results.append(result)

        return valid_results

    async def extract_premium_signals(self, scraped_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract premium trading signals from scraped content."""
        signals = []

        try:
            content = scraped_content.get("content", {})
            url = scraped_content.get("url", "")

            # Extract text content
            markdown_content = content.get("markdown", "")
            html_content = content.get("html", "")

            # Look for trading signals in content
            signal_patterns = [
                r'(?:LONG|SHORT|BUY|SELL)\s+(\w+)/(\w+)',
                r'(\w+)/(\w+)\s+(?:LONG|SHORT|BUY|SELL)',
                r'Entry:\s*\$?([0-9.]+)',
                r'Targets?:\s*\$?([0-9.,\s]+)',
                r'Stop Loss:\s*\$?([0-9.]+)'
            ]

            import re
            signal_data = {}

            for pattern in signal_patterns:
                matches = re.findall(pattern, markdown_content, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if len(match) >= 2:
                            if not signal_data.get('symbol'):
                                signal_data['symbol'] = f"{match[0]}/{match[1]}"
                            if len(match) >= 3 and not signal_data.get('entry_price'):
                                signal_data['entry_price'] = float(match[2])

            # Extract direction
            if 'long' in markdown_content.lower() or 'buy' in markdown_content.lower():
                signal_data['direction'] = 'LONG'
            elif 'short' in markdown_content.lower() or 'sell' in markdown_content.lower():
                signal_data['direction'] = 'SHORT'

            if signal_data.get('symbol') and signal_data.get('direction'):
                signal = {
                    "source": "firecrawl_premium",
                    "symbol": signal_data['symbol'],
                    "direction": signal_data['direction'],
                    "entry_price": signal_data.get('entry_price'),
                    "confidence": 0.8,  # Default confidence for premium sources
                    "timestamp": scraped_content.get("scraped_at", datetime.now().isoformat()),
                    "source_url": url,
                    "raw_content": markdown_content[:500]  # Store first 500 chars for reference
                }
                signals.append(signal)

        except Exception as e:
            logger.error(f"Error extracting signals from content: {e}")

        return signals

    async def search_premium_telegram_groups(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for premium Telegram groups using Firecrawl."""
        try:
            await self._rate_limit_wait()

            session = await self._get_session()

            payload = {
                "query": f"{query} premium trading signals telegram",
                "limit": limit,
                "sources": ["web"],
                "scrapeOptions": {
                    "onlyMainContent": True
                }
            }

            async with session.post(f"{self.base_url}/v1/search", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    logger.error(f"Firecrawl search failed: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error searching premium groups: {e}")
            return []

    async def close(self):
        """Close the client session."""
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
