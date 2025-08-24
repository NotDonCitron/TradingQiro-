"""
Triangular Arbitrage Scanner Module

Detects triangular arbitrage opportunities across three currency pairs
to find risk-free profit opportunities through cyclic trading.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN
import math

from ..core.models import ArbitrageOpportunity
from ..connectors.exchange_apis import ExchangeAPIManager
from ..core.risk_manager import RiskManager
from ..config.arbitrage_config import ArbitrageConfig
from ..utils.arbitrage_cache import ArbitrageCache

logger = logging.getLogger(__name__)


@dataclass
class TriangularOpportunity:
    """Represents a triangular arbitrage opportunity"""
    symbol1: str  # Base currency (e.g., BTC/USDT)
    symbol2: str  # Second pair (e.g., BTC/ETH)
    symbol3: str  # Third pair (e.g., ETH/USDT)
    exchange: str
    profit_percent: float
    volume: float
    path: List[str]  # Trading path: [USDT -> BTC -> ETH -> USDT]
    prices: Dict[str, float]  # Current prices for each pair
    timestamp: datetime = field(default_factory=datetime.now)
    risk_score: float = 0.0
    execution_time_estimate: float = 0.0

    def __post_init__(self):
        # Calculate execution time estimate based on complexity
        self.execution_time_estimate = 0.5  # 500ms for triangular arbitrage


@dataclass
class TrianglePair:
    """Represents a currency triangle for arbitrage scanning"""
    base_currency: str
    intermediate_currency: str
    quote_currency: str
    pairs: List[str]  # [base/intermediate, intermediate/quote, quote/base]
    enabled: bool = True
    last_profit: float = 0.0
    total_scanned: int = 0
    profitable_trades: int = 0


class TriangularArbitrageScanner:
    """
    Scans for triangular arbitrage opportunities across three currency pairs.
    Triangular arbitrage exploits price inefficiencies in currency triangles
    to guarantee risk-free profits.
    """

    def __init__(self, config: ArbitrageConfig):
        self.config = config
        self.exchange_manager = ExchangeAPIManager(config)
        self.risk_manager = RiskManager(config)
        self.cache = ArbitrageCache()
        self.is_running = False

        # Triangular arbitrage settings
        self.min_profit_threshold = 0.3  # Minimum 0.3% profit
        self.max_profit_threshold = 3.0  # Maximum 3% profit (avoid outliers)
        self.min_volume_threshold = 50000  # Minimum volume in USD
        self.scan_interval = 2.0  # Scan every 2 seconds
        self.max_opportunity_age = 5.0  # Max age in seconds

        # Currency triangles to monitor
        self.triangles = self._initialize_triangles()
        self.opportunity_callbacks: List[callable] = []

        # Statistics
        self.stats = {
            'total_scans': 0,
            'opportunities_found': 0,
            'profitable_trades': 0,
            'total_profit': 0.0,
            'last_scan_time': None,
            'avg_scan_time': 0.0
        }

        logger.info(f"TriangularArbitrageScanner initialized with {len(self.triangles)} triangles")

    def _initialize_triangles(self) -> List[TrianglePair]:
        """Initialize currency triangles for arbitrage scanning"""
        # Major currency triangles with USDT as base
        triangles = [
            TrianglePair(
                base_currency="USDT",
                intermediate_currency="BTC",
                quote_currency="ETH",
                pairs=["BTC/USDT", "ETH/BTC", "ETH/USDT"]
            ),
            TrianglePair(
                base_currency="USDT",
                intermediate_currency="ETH",
                quote_currency="BNB",
                pairs=["ETH/USDT", "BNB/ETH", "BNB/USDT"]
            ),
            TrianglePair(
                base_currency="USDT",
                intermediate_currency="BTC",
                quote_currency="BNB",
                pairs=["BTC/USDT", "BNB/BTC", "BNB/USDT"]
            ),
            TrianglePair(
                base_currency="USDT",
                intermediate_currency="ADA",
                quote_currency="DOT",
                pairs=["ADA/USDT", "DOT/ADA", "DOT/USDT"]
            ),
            TrianglePair(
                base_currency="USDT",
                intermediate_currency="SOL",
                quote_currency="AVAX",
                pairs=["SOL/USDT", "AVAX/SOL", "AVAX/USDT"]
            ),
            TrianglePair(
                base_currency="BTC",
                intermediate_currency="ETH",
                quote_currency="USDT",
                pairs=["ETH/BTC", "ETH/USDT", "BTC/USDT"]
            ),
            TrianglePair(
                base_currency="ETH",
                intermediate_currency="BNB",
                quote_currency="USDT",
                pairs=["BNB/ETH", "BNB/USDT", "ETH/USDT"]
            )
        ]

        return triangles

    async def start_scanning(self):
        """Start triangular arbitrage scanning"""
        if self.is_running:
            logger.warning("Triangular arbitrage scanner is already running")
            return

        self.is_running = True
        logger.info("Starting triangular arbitrage scanning...")

        try:
            while self.is_running:
                try:
                    await self._scan_all_triangles()
                    await asyncio.sleep(self.scan_interval)

                except Exception as e:
                    logger.error("Error in triangular arbitrage scan cycle: %s", str(e))
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error("Error in triangular arbitrage scanner: %s", str(e))
            self.is_running = False

    async def stop_scanning(self):
        """Stop triangular arbitrage scanning"""
        logger.info("Stopping triangular arbitrage scanning...")
        self.is_running = False

    async def _scan_all_triangles(self):
        """Scan all configured currency triangles for arbitrage opportunities"""
        scan_start = datetime.now()

        for triangle in self.triangles:
            if not triangle.enabled:
                continue

            try:
                await self._scan_triangle(triangle)

            except Exception as e:
                logger.error("Error scanning triangle %s: %s", triangle.pairs, str(e))

        # Update scan statistics
        scan_time = (datetime.now() - scan_start).total_seconds()
        self.stats['total_scans'] += 1
        self.stats['last_scan_time'] = datetime.now()

        # Update average scan time
        if self.stats['avg_scan_time'] == 0:
            self.stats['avg_scan_time'] = scan_time
        else:
            self.stats['avg_scan_time'] = (self.stats['avg_scan_time'] + scan_time) / 2

    async def _scan_triangle(self, triangle: TrianglePair):
        """Scan a specific currency triangle for arbitrage opportunities"""
        try:
            # Get current prices for all three pairs
            prices = await self._get_triangle_prices(triangle)
            if not prices:
                return

            # Check for arbitrage opportunities
            opportunities = self._find_arbitrage_opportunities(triangle, prices)

            for opportunity in opportunities:
                triangle.total_scanned += 1

                # Validate opportunity
                if await self._validate_opportunity(opportunity):
                    triangle.profitable_trades += 1
                    triangle.last_profit = opportunity.profit_percent

                    # Convert to standard ArbitrageOpportunity format
                    standard_opportunity = self._convert_to_standard_opportunity(opportunity)

                    # Notify callbacks
                    await self._notify_opportunity_callbacks(standard_opportunity)

                    # Cache the opportunity
                    await self.cache.set_triangular_opportunity(
                        f"tri_{triangle.base_currency}_{triangle.intermediate_currency}_{int(opportunity.timestamp.timestamp())}",
                        {
                            'symbol1': opportunity.symbol1,
                            'symbol2': opportunity.symbol2,
                            'symbol3': opportunity.symbol3,
                            'exchange': opportunity.exchange,
                            'profit_percent': opportunity.profit_percent,
                            'volume': opportunity.volume,
                            'path': opportunity.path,
                            'prices': opportunity.prices,
                            'timestamp': opportunity.timestamp.isoformat(),
                            'risk_score': opportunity.risk_score
                        }
                    )

                    logger.info(
                        "🎯 Triangular arbitrage opportunity: %s -> %s -> %s | Profit: %.4f%% | Exchange: %s",
                        opportunity.path[0], opportunity.path[1], opportunity.path[2],
                        opportunity.profit_percent, opportunity.exchange
                    )

        except Exception as e:
            logger.error("Error scanning triangle %s: %s", triangle.pairs, str(e))

    async def _get_triangle_prices(self, triangle: TrianglePair) -> Optional[Dict[str, Dict[str, Any]]]:
        """Get current prices for all three pairs in a triangle"""
        prices = {}

        try:
            for symbol in triangle.pairs:
                # Get price from exchange monitor or API
                price_data = await self._get_current_price(symbol)
                if price_data:
                    prices[symbol] = price_data

            # Check if we have prices for all pairs
            if len(prices) == len(triangle.pairs):
                return prices

        except Exception as e:
            logger.error("Error getting triangle prices: %s", str(e))

        return None

    async def _get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price for a symbol (placeholder implementation)"""
        try:
            # In a real implementation, this would fetch from exchange APIs
            # or use the exchange monitor's cached prices

            # For now, simulate price data
            # This would be replaced with actual price fetching logic
            return {
                'symbol': symbol,
                'bid_price': 1.0,  # Placeholder
                'ask_price': 1.0,  # Placeholder
                'volume': 1000000,
                'timestamp': datetime.now()
            }

        except Exception as e:
            logger.error("Error getting price for %s: %s", symbol, str(e))
            return None

    def _find_arbitrage_opportunities(self, triangle: TrianglePair,
                                    prices: Dict[str, Dict[str, Any]]) -> List[TriangularOpportunity]:
        """Find arbitrage opportunities in a currency triangle"""
        opportunities = []

        try:
            # Extract prices for the three pairs
            pair1, pair2, pair3 = triangle.pairs

            if pair1 not in prices or pair2 not in prices or pair3 not in prices:
                return []

            p1_ask = prices[pair1]['ask_price']
            p2_ask = prices[pair2]['ask_price']
            p3_ask = prices[pair3]['ask_price']

            p1_bid = prices[pair1]['bid_price']
            p2_bid = prices[pair2]['bid_price']
            p3_bid = prices[pair3]['bid_price']

            # Calculate triangular arbitrage for both directions
            # Direction 1: Base -> Intermediate -> Quote -> Base
            profit1 = self._calculate_triangular_profit(
                triangle.base_currency,
                triangle.intermediate_currency,
                triangle.quote_currency,
                p1_ask, p2_ask, p3_bid
            )

            # Direction 2: Base -> Quote -> Intermediate -> Base
            profit2 = self._calculate_triangular_profit(
                triangle.base_currency,
                triangle.quote_currency,
                triangle.intermediate_currency,
                p1_ask, p3_ask, p2_bid
            )

            # Check if either direction is profitable
            for profit, path in [(profit1, [triangle.base_currency, triangle.intermediate_currency, triangle.quote_currency, triangle.base_currency]),
                                (profit2, [triangle.base_currency, triangle.quote_currency, triangle.intermediate_currency, triangle.base_currency])]:

                if profit > self.min_profit_threshold and profit < self.max_profit_threshold:
                    # Calculate volume (use minimum of the three pairs)
                    volume = min(
                        prices[pair1]['volume'],
                        prices[pair2]['volume'],
                        prices[pair3]['volume']
                    )

                    if volume >= self.min_volume_threshold:
                        opportunity = TriangularOpportunity(
                            symbol1=pair1,
                            symbol2=pair2,
                            symbol3=pair3,
                            exchange="binance",  # Default to Binance for now
                            profit_percent=profit,
                            volume=volume,
                            path=path,
                            prices={
                                pair1: p1_ask,
                                pair2: p2_ask,
                                pair3: p3_ask
                            }
                        )

                        opportunities.append(opportunity)

        except Exception as e:
            logger.error("Error finding arbitrage opportunities: %s", str(e))

        return opportunities

    def _calculate_triangular_profit(self, base: str, intermediate: str, quote: str,
                                   price1: float, price2: float, price3: float) -> float:
        """Calculate profit percentage for a triangular arbitrage path"""
        try:
            # Start with 1 unit of base currency
            initial_amount = 1.0

            # Step 1: Base -> Intermediate
            intermediate_amount = initial_amount / price1  # Buy intermediate with base

            # Step 2: Intermediate -> Quote
            quote_amount = intermediate_amount * price2  # Sell intermediate for quote

            # Step 3: Quote -> Base
            final_amount = quote_amount * price3  # Buy base with quote

            # Calculate profit percentage
            profit = (final_amount - initial_amount) / initial_amount * 100

            return profit

        except Exception as e:
            logger.error("Error calculating triangular profit: %s", str(e))
            return 0.0

    async def _validate_opportunity(self, opportunity: TriangularOpportunity) -> bool:
        """Validate a triangular arbitrage opportunity"""
        try:
            # Check if opportunity is still fresh
            age = (datetime.now() - opportunity.timestamp).total_seconds()
            if age > self.max_opportunity_age:
                return False

            # Check risk limits
            risk_check = self.risk_manager.can_execute_opportunity(
                self._convert_to_standard_opportunity(opportunity)
            )

            if not risk_check['can_execute']:
                return False

            opportunity.risk_score = risk_check['risk_score']
            return True

        except Exception as e:
            logger.error("Error validating opportunity: %s", str(e))
            return False

    def _convert_to_standard_opportunity(self, triangular_opp: TriangularOpportunity) -> ArbitrageOpportunity:
        """Convert triangular opportunity to standard ArbitrageOpportunity format"""
        return ArbitrageOpportunity(
            symbol=f"{triangular_opp.symbol1}_{triangular_opp.symbol2}_{triangular_opp.symbol3}",
            buy_exchange=triangular_opp.exchange,
            sell_exchange=triangular_opp.exchange,
            buy_price=0.0,  # Not applicable for triangular
            sell_price=0.0,  # Not applicable for triangular
            profit_percent=triangular_opp.profit_percent,
            volume=triangular_opp.volume,
            timestamp=triangular_opp.timestamp,
            risk_score=triangular_opp.risk_score,
            triangular_data={
                'symbol1': triangular_opp.symbol1,
                'symbol2': triangular_opp.symbol2,
                'symbol3': triangular_opp.symbol3,
                'path': triangular_opp.path,
                'prices': triangular_opp.prices
            }
        )

    # Callback management
    def add_opportunity_callback(self, callback):
        """Add callback for triangular arbitrage opportunities"""
        self.opportunity_callbacks.append(callback)
        logger.info("Added triangular arbitrage opportunity callback")

    async def _notify_opportunity_callbacks(self, opportunity: ArbitrageOpportunity):
        """Notify all opportunity callbacks"""
        for callback in self.opportunity_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(opportunity)
                else:
                    callback(opportunity)
            except Exception as e:
                logger.error("Error in opportunity callback: %s", str(e))

    # Data access methods
    def get_scanner_stats(self) -> Dict[str, Any]:
        """Get scanner statistics"""
        return {
            'is_running': self.is_running,
            'total_scans': self.stats['total_scans'],
            'opportunities_found': self.stats['opportunities_found'],
            'profitable_trades': self.stats['profitable_trades'],
            'total_profit': self.stats['total_profit'],
            'avg_scan_time': self.stats['avg_scan_time'],
            'last_scan_time': self.stats['last_scan_time'],
            'triangles_configured': len(self.triangles),
            'triangles_enabled': sum(1 for t in self.triangles if t.enabled),
            'min_profit_threshold': self.min_profit_threshold,
            'max_profit_threshold': self.max_profit_threshold,
            'scan_interval': self.scan_interval
        }

    def get_triangle_performance(self) -> List[Dict[str, Any]]:
        """Get performance statistics for each triangle"""
        return [
            {
                'base': triangle.base_currency,
                'intermediate': triangle.intermediate_currency,
                'quote': triangle.quote_currency,
                'pairs': triangle.pairs,
                'enabled': triangle.enabled,
                'total_scanned': triangle.total_scanned,
                'profitable_trades': triangle.profitable_trades,
                'success_rate': (triangle.profitable_trades / max(triangle.total_scanned, 1)) * 100,
                'last_profit': triangle.last_profit
            }
            for triangle in self.triangles
        ]

    def enable_triangle(self, base: str, intermediate: str, quote: str):
        """Enable a specific currency triangle"""
        for triangle in self.triangles:
            if (triangle.base_currency == base and
                triangle.intermediate_currency == intermediate and
                triangle.quote_currency == quote):
                triangle.enabled = True
                logger.info("Enabled triangle: %s -> %s -> %s", base, intermediate, quote)
                break

    def disable_triangle(self, base: str, intermediate: str, quote: str):
        """Disable a specific currency triangle"""
        for triangle in self.triangles:
            if (triangle.base_currency == base and
                triangle.intermediate_currency == intermediate and
                triangle.quote_currency == quote):
                triangle.enabled = False
                logger.info("Disabled triangle: %s -> %s -> %s", base, intermediate, quote)
                break

    def get_supported_triangles(self) -> List[Dict[str, str]]:
        """Get list of supported currency triangles"""
        return [
            {
                'base': triangle.base_currency,
                'intermediate': triangle.intermediate_currency,
                'quote': triangle.quote_currency,
                'pairs': triangle.pairs
            }
            for triangle in self.triangles
        ]

    def update_scan_parameters(self, min_profit: Optional[float] = None,
                             max_profit: Optional[float] = None,
                             scan_interval: Optional[float] = None):
        """Update scanning parameters"""
        if min_profit is not None:
            self.min_profit_threshold = min_profit
        if max_profit is not None:
            self.max_profit_threshold = max_profit
        if scan_interval is not None:
            self.scan_interval = scan_interval

        logger.info("Updated scan parameters: min_profit=%.4f, max_profit=%.4f, interval=%.1f",
                   self.min_profit_threshold, self.max_profit_threshold, self.scan_interval)
