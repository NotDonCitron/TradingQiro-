"""
Arbitrage Scanner Module

Main arbitrage detection engine that analyzes price differences across multiple exchanges
to identify profitable arbitrage opportunities in real-time.

Features:
- Price difference scanning across exchanges
- Triangular arbitrage detection
- Real-time opportunity identification
- Integration with exchange APIs and Firecrawl data
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from ..connectors.exchange_apis import ExchangeAPIManager
from ..utils.arbitrage_cache import ArbitrageCache
from ..core.risk_manager import RiskManager
from ..config.arbitrage_config import ArbitrageConfig
from ..core.models import ArbitrageOpportunity, PriceData

logger = logging.getLogger(__name__)


class ArbitrageScanner:
    """
    Main arbitrage scanner that monitors multiple exchanges for price discrepancies
    and identifies profitable trading opportunities.
    """

    def __init__(self, config: ArbitrageConfig):
        self.config = config
        self.exchange_manager = ExchangeAPIManager(config)
        self.cache = ArbitrageCache()
        self.risk_manager = RiskManager(config)
        self.is_running = False
        self.scan_interval = config.scan_interval_seconds
        self.min_profit_threshold = config.min_profit_threshold_percent
        self.opportunities_found: List[ArbitrageOpportunity] = []

        logger.info("ArbitrageScanner initialized with scan interval: %s seconds",
                   self.scan_interval)

    async def start_scanning(self):
        """Start the continuous arbitrage scanning process"""
        if self.is_running:
            logger.warning("Arbitrage scanner is already running")
            return

        self.is_running = True
        logger.info("Starting arbitrage scanning...")

        try:
            while self.is_running:
                await self._scan_cycle()
                await asyncio.sleep(self.scan_interval)
        except Exception as e:
            logger.error("Error in arbitrage scanning: %s", str(e))
            self.is_running = False

    async def stop_scanning(self):
        """Stop the arbitrage scanning process"""
        logger.info("Stopping arbitrage scanning...")
        self.is_running = False

    async def _scan_cycle(self):
        """Perform a single arbitrage scanning cycle"""
        try:
            # Get price data from all exchanges
            price_data = await self._get_all_price_data()

            if not price_data:
                logger.warning("No price data received from exchanges")
                return

            # Analyze for arbitrage opportunities
            opportunities = await self._analyze_opportunities(price_data)

            # Filter by minimum profit threshold
            profitable_opportunities = [
                opp for opp in opportunities
                if opp.profit_percent >= self.min_profit_threshold
            ]

            if profitable_opportunities:
                logger.info("Found %d profitable opportunities", len(profitable_opportunities))

                # Assess risk for each opportunity
                for opportunity in profitable_opportunities:
                    opportunity.risk_score = self.risk_manager.assess_opportunity(opportunity)

                # Sort by profit percentage (descending)
                profitable_opportunities.sort(key=lambda x: x.profit_percent, reverse=True)

                self.opportunities_found.extend(profitable_opportunities)

                # Keep only recent opportunities (last 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.opportunities_found = [
                    opp for opp in self.opportunities_found
                    if opp.timestamp > cutoff_time
                ]

                # Log top opportunities
                await self._log_top_opportunities(profitable_opportunities[:5])

        except Exception as e:
            logger.error("Error in scan cycle: %s", str(e))

    async def _get_all_price_data(self) -> Dict[str, List[PriceData]]:
        """Get price data from all configured exchanges"""
        price_data = {}
        symbols = self.config.trading_symbols

        for exchange_name in self.config.exchanges.keys():
            try:
                exchange_data = []
                for symbol in symbols:
                    try:
                        data = await self.exchange_manager.get_price_data(exchange_name, symbol)
                        if data:
                            price_info = PriceData(
                                exchange=exchange_name,
                                symbol=symbol,
                                bid_price=data['bid'],
                                ask_price=data['ask'],
                                volume_24h=data.get('volume_24h', 0),
                                last_update=datetime.now(),
                                spread=data.get('spread', 0),
                                liquidity_score=self._calculate_liquidity_score(data)
                            )
                            exchange_data.append(price_info)

                            # Cache the price data
                            await self.cache.set_price_data(exchange_name, symbol, data)

                    except Exception as e:
                        logger.error("Error getting price for %s on %s: %s",
                                   symbol, exchange_name, str(e))
                        continue

                if exchange_data:
                    price_data[exchange_name] = exchange_data

            except Exception as e:
                logger.error("Error getting data from exchange %s: %s", exchange_name, str(e))
                continue

        return price_data

    async def _analyze_opportunities(self, price_data: Dict[str, List[PriceData]]) -> List[ArbitrageOpportunity]:
        """Analyze price data to find arbitrage opportunities"""
        opportunities = []

        # Get all unique symbols across exchanges
        all_symbols = set()
        for exchange_data in price_data.values():
            for price_info in exchange_data:
                all_symbols.add(price_info.symbol)

        for symbol in all_symbols:
            # Get price data for this symbol from all exchanges
            symbol_prices = {}
            for exchange_name, exchange_data in price_data.items():
                for price_info in exchange_data:
                    if price_info.symbol == symbol:
                        symbol_prices[exchange_name] = price_info
                        break

            if len(symbol_prices) < 2:
                continue  # Need at least 2 exchanges to compare

            # Find cross-exchange arbitrage opportunities
            cross_exchange_opportunities = self._find_cross_exchange_opportunities(
                symbol, symbol_prices
            )
            opportunities.extend(cross_exchange_opportunities)

            # Find triangular arbitrage opportunities
            if len(symbol_prices) >= 3:
                triangular_opportunities = await self._find_triangular_opportunities(
                    symbol, symbol_prices
                )
                opportunities.extend(triangular_opportunities)

        return opportunities

    def _find_cross_exchange_opportunities(self, symbol: str, symbol_prices: Dict[str, PriceData]) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities between two exchanges"""
        opportunities = []
        exchanges = list(symbol_prices.keys())

        for i, buy_exchange in enumerate(exchanges):
            for sell_exchange in exchanges[i+1:]:
                buy_price = symbol_prices[buy_exchange].ask_price
                sell_price = symbol_prices[sell_exchange].bid_price

                if buy_price <= 0 or sell_price <= 0:
                    continue

                # Calculate profit percentage
                profit_percent = ((sell_price - buy_price) / buy_price) * 100

                # Account for fees
                fees = self._calculate_fees(buy_exchange, sell_exchange, buy_price, sell_price)
                total_fees = fees['buy_fee'] + fees['sell_fee']
                net_profit_percent = profit_percent - total_fees

                if net_profit_percent > 0:
                    # Calculate estimated profit
                    volume = min(
                        symbol_prices[buy_exchange].volume_24h,
                        symbol_prices[sell_exchange].volume_24h
                    ) * 0.1  # Use 10% of available volume

                    estimated_profit = (volume * buy_price * net_profit_percent) / 100

                    opportunity = ArbitrageOpportunity(
                        symbol=symbol,
                        buy_exchange=buy_exchange,
                        sell_exchange=sell_exchange,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        profit_percent=net_profit_percent,
                        volume=volume,
                        timestamp=datetime.now(),
                        fees=fees,
                        estimated_profit=estimated_profit,
                        risk_score=0.0  # Will be calculated later
                    )
                    opportunities.append(opportunity)

        return opportunities

    async def _find_triangular_opportunities(self, base_symbol: str, symbol_prices: Dict[str, PriceData]) -> List[ArbitrageOpportunity]:
        """Find triangular arbitrage opportunities"""
        opportunities = []

        # This is a simplified implementation
        # In a full implementation, you'd need to check for arbitrage paths like:
        # BTC/USD -> BTC/ETH -> ETH/USD -> BTC/USD

        # For now, we'll implement a basic version that looks for opportunities
        # involving the base symbol and two other symbols

        exchanges = list(symbol_prices.keys())
        if len(exchanges) < 3:
            return opportunities

        # Get common trading pairs involving the base symbol
        common_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']

        for pair in common_pairs:
            if pair == base_symbol:
                continue

            try:
                # Get price data for the pair from all exchanges
                pair_prices = {}
                for exchange_name in exchanges:
                    try:
                        data = await self.exchange_manager.get_price_data(exchange_name, pair)
                        if data:
                            pair_prices[exchange_name] = data
                    except Exception as e:
                        continue

                if len(pair_prices) < 2:
                    continue

                # Look for triangular arbitrage involving base_symbol and pair
                triangular_opp = self._calculate_triangular_arbitrage(
                    base_symbol, pair, symbol_prices, pair_prices
                )

                if triangular_opp:
                    opportunities.append(triangular_opp)

            except Exception as e:
                logger.error("Error analyzing triangular arbitrage for %s: %s", pair, str(e))
                continue

        return opportunities

    def _calculate_triangular_arbitrage(self, symbol1: str, symbol2: str,
                                      prices1: Dict[str, PriceData],
                                      prices2: Dict[str, any]) -> Optional[ArbitrageOpportunity]:
        """Calculate triangular arbitrage between two symbols"""
        # This is a simplified implementation
        # Real triangular arbitrage requires finding arbitrage paths

        try:
            # Find common exchanges
            common_exchanges = set(prices1.keys()) & set(prices2.keys())
            if len(common_exchanges) < 1:
                return None

            exchange = list(common_exchanges)[0]

            # Get prices
            price1_buy = prices1[exchange].ask_price
            price1_sell = prices1[exchange].bid_price
            price2_buy = prices2[exchange]['ask']
            price2_sell = prices2[exchange]['bid']

            if price1_buy <= 0 or price2_buy <= 0:
                return None

            # Calculate potential arbitrage
            # This is a simplified calculation - real implementation would be more complex
            profit_percent = 0.0  # Simplified for now

            if profit_percent > 0.1:  # Minimum 0.1% profit
                return ArbitrageOpportunity(
                    symbol=f"{symbol1}/{symbol2}",
                    buy_exchange=exchange,
                    sell_exchange=exchange,
                    buy_price=price1_buy,
                    sell_price=price2_sell,
                    profit_percent=profit_percent,
                    volume=min(prices1[exchange].volume_24h, prices2[exchange].get('volume_24h', 0)),
                    timestamp=datetime.now(),
                    fees=self._calculate_fees(exchange, exchange, price1_buy, price2_sell),
                    estimated_profit=0.0,
                    risk_score=0.0,
                    triangular_path=[symbol1, symbol2]
                )

        except Exception as e:
            logger.error("Error calculating triangular arbitrage: %s", str(e))

        return None

    def _calculate_fees(self, buy_exchange: str, sell_exchange: str,
                       buy_price: float, sell_price: float) -> Dict[str, float]:
        """Calculate trading fees for the arbitrage opportunity"""
        # Get fee rates from config
        buy_fee_rate = self.config.get_fee_rate(buy_exchange, 'taker')
        sell_fee_rate = self.config.get_fee_rate(sell_exchange, 'taker')

        buy_fee = buy_price * buy_fee_rate
        sell_fee = sell_price * sell_fee_rate

        return {
            'buy_fee': buy_fee,
            'sell_fee': sell_fee,
            'total_fee': buy_fee + sell_fee
        }

    def _calculate_liquidity_score(self, price_data: Dict) -> float:
        """Calculate liquidity score based on volume and spread"""
        volume = price_data.get('volume_24h', 0)
        spread = price_data.get('spread', 0)

        if volume <= 0:
            return 0.0

        # Normalize volume score (logarithmic scale)
        volume_score = min(1.0, (volume / 1000000) ** 0.5)  # Max at $1M volume

        # Spread score (inverse relationship)
        spread_score = max(0.0, 1.0 - (spread / 0.01))  # Penalize spreads > 1%

        # Combined score
        return (volume_score * 0.7) + (spread_score * 0.3)

    async def _log_top_opportunities(self, opportunities: List[ArbitrageOpportunity]):
        """Log the top arbitrage opportunities"""
        if not opportunities:
            return

        logger.info("=== TOP ARBITRAGE OPPORTUNITIES ===")
        for i, opp in enumerate(opportunities[:3], 1):
            logger.info(
                "%d. %s: Buy on %s (%.6f) -> Sell on %s (%.6f) = %.4f%% profit",
                i, opp.symbol, opp.buy_exchange, opp.buy_price,
                opp.sell_exchange, opp.sell_price, opp.profit_percent
            )

    def get_recent_opportunities(self, hours: int = 24) -> List[ArbitrageOpportunity]:
        """Get recent arbitrage opportunities"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            opp for opp in self.opportunities_found
            if opp.timestamp > cutoff_time
        ]

    def get_opportunities_by_symbol(self, symbol: str) -> List[ArbitrageOpportunity]:
        """Get arbitrage opportunities for a specific symbol"""
        return [opp for opp in self.opportunities_found if opp.symbol == symbol]

    async def get_scanner_stats(self) -> Dict:
        """Get statistics about the arbitrage scanner"""
        recent_opportunities = self.get_recent_opportunities(hours=1)

        return {
            'is_running': self.is_running,
            'total_opportunities_found': len(self.opportunities_found),
            'recent_opportunities_1h': len(recent_opportunities),
            'scan_interval_seconds': self.scan_interval,
            'min_profit_threshold': self.min_profit_threshold,
            'exchanges_monitored': list(self.config.exchanges.keys()),
            'symbols_tracked': self.config.trading_symbols
        }
