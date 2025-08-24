"""
Arbitrage Configuration Module

Handles loading and parsing of arbitrage configuration from JSON file
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExchangeConfig:
    """Configuration for a single exchange"""
    name: str
    enabled: bool
    api_key_env: str
    secret_key_env: str
    testnet: bool = True
    sandbox: bool = True
    rate_limit: int = 1000
    fee_structure: Optional[Dict[str, float]] = None

    def __post_init__(self):
        if self.fee_structure is None:
            self.fee_structure = {'maker': 0.001, 'taker': 0.001}


@dataclass
class ArbitrageConfig:
    """Main configuration class for arbitrage system"""

    # Arbitrage settings
    enabled: bool = True
    min_profit_threshold_percent: float = 0.5
    max_profit_threshold_percent: float = 5.0
    min_volume_threshold: float = 1000.0
    scan_interval_seconds: int = 5
    max_opportunity_age_seconds: int = 30

    # Risk limits
    max_single_trade_usd: float = 1000.0
    max_daily_loss_usd: float = 5000.0
    max_open_positions: int = 5

    # Trading symbols to monitor
    trading_symbols: List[str] = None

    # Exchange configurations
    exchanges: Dict[str, ExchangeConfig] = None

    # Firecrawl settings
    firecrawl_enabled: bool = True
    firecrawl_api_key_env: str = "FIRECRAWL_API_KEY"
    firecrawl_base_url: str = "https://api.firecrawl.com"
    firecrawl_rate_limit: int = 100

    # Cache settings
    redis_url: str = "redis://localhost:6379"
    price_cache_ttl_seconds: int = 30
    arbitrage_cache_ttl_seconds: int = 60
    whale_cache_ttl_seconds: int = 300

    # Alert settings
    telegram_alerts: bool = True
    min_profit_alert: float = 1.0

    # Whale tracking settings
    whale_tracking: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.trading_symbols is None:
            self.trading_symbols = [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT',
                'SOL/USDT', 'DOT/USDT', 'MATIC/USDT', 'AVAX/USDT'
            ]

        if self.exchanges is None:
            self.exchanges = {}

        if self.whale_tracking is None:
            self.whale_tracking = {
                'enabled': True,
                'min_transaction_usd': 100000,
                'whale_addresses': [],
                'tracking_exchanges': ['binance', 'coinbase', 'kraken'],
                'alert_thresholds': {
                    'large_buy': 500000,
                    'large_sell': 500000,
                    'whale_movement': 1000000
                }
            }

    @classmethod
    def from_json_file(cls, file_path: str = "config/arbitrage_config.json") -> "ArbitrageConfig":
        """Load configuration from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            return cls.from_dict(data)
        except FileNotFoundError:
            logger.warning(f"Config file {file_path} not found, using defaults")
            return cls()
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config file: {e}")
            return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArbitrageConfig":
        """Create configuration from dictionary"""
        arbitrage_data = data.get('arbitrage', {})
        exchanges_data = data.get('exchanges', {})
        firecrawl_data = data.get('firecrawl', {})
        cache_data = data.get('cache', {})
        alerts_data = data.get('alerts', {})

        # Parse exchanges
        exchanges = {}
        for name, exchange_data in exchanges_data.items():
            if exchange_data.get('enabled', False):
                exchanges[name] = ExchangeConfig(
                    name=name,
                    enabled=exchange_data.get('enabled', True),
                    api_key_env=exchange_data.get('api_key_env', f"{name.upper()}_API_KEY"),
                    secret_key_env=exchange_data.get('secret_key_env', f"{name.upper()}_SECRET_KEY"),
                    testnet=exchange_data.get('testnet', True),
                    sandbox=exchange_data.get('sandbox', True),
                    rate_limit=exchange_data.get('rate_limit', 1000),
                    fee_structure=exchange_data.get('fee_structure', {'maker': 0.001, 'taker': 0.001})
                )

        # Create config instance
        config = cls(
            enabled=arbitrage_data.get('enabled', True),
            min_profit_threshold_percent=arbitrage_data.get('min_profit_threshold', 0.5),
            max_profit_threshold_percent=arbitrage_data.get('max_profit_threshold', 5.0),
            min_volume_threshold=arbitrage_data.get('min_volume_threshold', 1000.0),
            scan_interval_seconds=arbitrage_data.get('scan_interval_seconds', 5),
            max_opportunity_age_seconds=arbitrage_data.get('max_opportunity_age_seconds', 30),
            max_single_trade_usd=arbitrage_data.get('risk_limits', {}).get('max_single_trade_usd', 1000.0),
            max_daily_loss_usd=arbitrage_data.get('risk_limits', {}).get('max_daily_loss_usd', 5000.0),
            max_open_positions=arbitrage_data.get('risk_limits', {}).get('max_open_positions', 5),
            exchanges=exchanges,
            firecrawl_enabled=firecrawl_data.get('enabled', True),
            firecrawl_api_key_env=firecrawl_data.get('api_key_env', 'FIRECRAWL_API_KEY'),
            firecrawl_base_url=firecrawl_data.get('base_url', 'https://api.firecrawl.com'),
            firecrawl_rate_limit=firecrawl_data.get('rate_limit', 100),
            redis_url=cache_data.get('redis_url', 'redis://localhost:6379'),
            price_cache_ttl_seconds=cache_data.get('price_cache_ttl_seconds', 30),
            arbitrage_cache_ttl_seconds=cache_data.get('arbitrage_cache_ttl_seconds', 60),
            whale_cache_ttl_seconds=cache_data.get('whale_cache_ttl_seconds', 300),
            telegram_alerts=alerts_data.get('telegram_alerts', True),
            min_profit_alert=alerts_data.get('min_profit_alert', 1.0)
        )

        return config

    def get_exchange_config(self, exchange_name: str) -> Optional[ExchangeConfig]:
        """Get configuration for a specific exchange"""
        return self.exchanges.get(exchange_name)

    def get_api_keys(self, exchange_name: str) -> Dict[str, str]:
        """Get API keys for an exchange from environment variables"""
        exchange_config = self.get_exchange_config(exchange_name)
        if not exchange_config:
            return {}

        api_key = os.getenv(exchange_config.api_key_env, '')
        secret_key = os.getenv(exchange_config.secret_key_env, '')

        return {
            'api_key': api_key,
            'secret_key': secret_key
        }

    def get_firecrawl_api_key(self) -> str:
        """Get Firecrawl API key from environment"""
        return os.getenv(self.firecrawl_api_key_env, '')

    def is_exchange_enabled(self, exchange_name: str) -> bool:
        """Check if an exchange is enabled"""
        exchange_config = self.get_exchange_config(exchange_name)
        return exchange_config is not None and exchange_config.enabled

    def get_enabled_exchanges(self) -> List[str]:
        """Get list of enabled exchanges"""
        return [name for name, config in self.exchanges.items() if config.enabled]

    def get_fee_rate(self, exchange_name: str, fee_type: str = 'taker') -> float:
        """Get fee rate for an exchange"""
        exchange_config = self.get_exchange_config(exchange_name)
        if exchange_config and exchange_config.fee_structure:
            return exchange_config.fee_structure.get(fee_type, 0.001)
        return 0.001  # Default 0.1%

    def validate(self) -> List[str]:
        """Validate the configuration and return any issues"""
        issues = []

        if not self.enabled:
            return issues  # No need to validate if disabled

        if self.min_profit_threshold_percent <= 0:
            issues.append("Minimum profit threshold must be greater than 0")

        if self.max_profit_threshold_percent <= self.min_profit_threshold_percent:
            issues.append("Maximum profit threshold must be greater than minimum")

        if self.scan_interval_seconds <= 0:
            issues.append("Scan interval must be greater than 0")

        if not self.trading_symbols:
            issues.append("At least one trading symbol must be configured")

        if not self.exchanges:
            issues.append("At least one exchange must be configured")

        # Check for enabled exchanges without API keys
        for name, exchange in self.exchanges.items():
            if exchange.enabled:
                keys = self.get_api_keys(name)
                if not keys.get('api_key') or not keys.get('secret_key'):
                    issues.append(f"API keys not found for enabled exchange: {name}")

        return issues

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'enabled': self.enabled,
            'min_profit_threshold_percent': self.min_profit_threshold_percent,
            'max_profit_threshold_percent': self.max_profit_threshold_percent,
            'min_volume_threshold': self.min_volume_threshold,
            'scan_interval_seconds': self.scan_interval_seconds,
            'max_opportunity_age_seconds': self.max_opportunity_age_seconds,
            'max_single_trade_usd': self.max_single_trade_usd,
            'max_daily_loss_usd': self.max_daily_loss_usd,
            'max_open_positions': self.max_open_positions,
            'trading_symbols': self.trading_symbols,
            'exchanges': {name: {
                'enabled': config.enabled,
                'api_key_env': config.api_key_env,
                'secret_key_env': config.secret_key_env,
                'testnet': config.testnet,
                'sandbox': config.sandbox,
                'rate_limit': config.rate_limit,
                'fee_structure': config.fee_structure
            } for name, config in self.exchanges.items()},
            'firecrawl_enabled': self.firecrawl_enabled,
            'firecrawl_api_key_env': self.firecrawl_api_key_env,
            'firecrawl_base_url': self.firecrawl_base_url,
            'firecrawl_rate_limit': self.firecrawl_rate_limit,
            'redis_url': self.redis_url,
            'price_cache_ttl_seconds': self.price_cache_ttl_seconds,
            'arbitrage_cache_ttl_seconds': self.arbitrage_cache_ttl_seconds,
            'whale_cache_ttl_seconds': self.whale_cache_ttl_seconds,
            'telegram_alerts': self.telegram_alerts,
            'min_profit_alert': self.min_profit_alert
        }
