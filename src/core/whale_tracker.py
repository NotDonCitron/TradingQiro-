"""
Whale Tracker Module

Monitors whale wallet activities and large transactions across exchanges
to identify potential market-moving events and trading opportunities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass

from ..connectors.exchange_apis import ExchangeAPIManager
from ..utils.arbitrage_cache import ArbitrageCache
from ..config.arbitrage_config import ArbitrageConfig

logger = logging.getLogger(__name__)


@dataclass
class WhaleTransaction:
    """Data class representing a whale transaction"""
    address: str
    symbol: str
    amount: float
    transaction_type: str  # 'buy', 'sell', 'transfer'
    exchange: str
    timestamp: datetime
    usd_value: float
    wallet_type: str  # 'whale', 'exchange', 'dex_pool'
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class WhaleAlert:
    """Data class representing a whale alert"""
    alert_type: str  # 'large_buy', 'large_sell', 'whale_movement', 'accumulation'
    symbol: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    timestamp: datetime
    transactions: List[WhaleTransaction]
    market_impact_score: float


class WhaleTracker:
    """
    Monitors whale wallet activities and large transactions to identify
    potential market-moving events and trading signals.
    """

    def __init__(self, config: ArbitrageConfig):
        self.config = config
        self.exchange_manager = ExchangeAPIManager(config)
        self.cache = ArbitrageCache()
        self.is_running = False

        # Whale tracking settings
        whale_config = config.whale_tracking or {}
        self.min_transaction_usd = whale_config.get('min_transaction_usd', 100000)
        self.whale_addresses: Set[str] = set(whale_config.get('whale_addresses', []))
        self.tracking_exchanges = whale_config.get('tracking_exchanges', [])
        self.alert_thresholds = whale_config.get('alert_thresholds', {})

        # Tracking state
        self.recent_transactions: List[WhaleTransaction] = []
        self.active_alerts: List[WhaleAlert] = []
        self.whale_portfolio: Dict[str, Dict[str, float]] = {}  # address -> symbol -> amount

        # Callbacks
        self.alert_callbacks: List[Callable[[WhaleAlert], None]] = []
        self.transaction_callbacks: List[Callable[[WhaleTransaction], None]] = []

        logger.info("WhaleTracker initialized with threshold: $%.0f",
                   self.min_transaction_usd)

    async def start_tracking(self):
        """Start whale tracking monitoring"""
        if self.is_running:
            logger.warning("Whale tracker is already running")
            return

        self.is_running = True
        logger.info("Starting whale tracking...")

        try:
            # Start monitoring tasks
            tasks = [
                self._monitor_exchange_transactions(),
                self._analyze_whale_patterns(),
                self._cleanup_old_data()
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error("Error in whale tracking: %s", str(e))
            self.is_running = False

    async def stop_tracking(self):
        """Stop whale tracking"""
        logger.info("Stopping whale tracking...")
        self.is_running = False

    async def _monitor_exchange_transactions(self):
        """Monitor large transactions across exchanges"""
        logger.info("Monitoring large transactions across exchanges")

        while self.is_running:
            try:
                for exchange_name in self.tracking_exchanges:
                    try:
                        await self._scan_exchange_transactions(exchange_name)
                    except Exception as e:
                        logger.error("Error scanning transactions for %s: %s", exchange_name, str(e))

                await asyncio.sleep(5)  # Scan every 5 seconds

            except Exception as e:
                logger.error("Error in exchange transaction monitoring: %s", str(e))
                await asyncio.sleep(10)

    async def _scan_exchange_transactions(self, exchange_name: str):
        """Scan transactions for a specific exchange"""
        try:
            # This would typically connect to exchange WebSocket feeds
            # For now, we'll simulate transaction monitoring

            # Get recent trades (placeholder implementation)
            recent_trades = await self._get_recent_trades(exchange_name)

            for trade in recent_trades:
                await self._process_potential_whale_transaction(trade, exchange_name)

        except Exception as e:
            logger.error("Error scanning transactions for %s: %s", exchange_name, str(e))

    async def _get_recent_trades(self, exchange_name: str) -> List[Dict[str, Any]]:
        """Get recent trades from an exchange (placeholder)"""
        # In a real implementation, this would:
        # 1. Connect to exchange WebSocket trade streams
        # 2. Monitor transaction APIs
        # 3. Use blockchain explorers for wallet tracking
        # 4. Monitor DEX transactions

        # For now, return empty list
        return []

    async def _process_potential_whale_transaction(self, trade: Dict[str, Any], exchange_name: str):
        """Process a potential whale transaction"""
        try:
            usd_value = trade.get('usd_value', 0)
            amount = trade.get('amount', 0)
            symbol = trade.get('symbol', '')

            # Check if transaction meets whale threshold
            if usd_value >= self.min_transaction_usd:
                whale_transaction = WhaleTransaction(
                    address=trade.get('address', 'unknown'),
                    symbol=symbol,
                    amount=amount,
                    transaction_type=trade.get('side', 'unknown'),
                    exchange=exchange_name,
                    timestamp=datetime.now(),
                    usd_value=usd_value,
                    wallet_type=self._classify_wallet(trade.get('address', '')),
                    confidence=self._calculate_transaction_confidence(trade),
                    metadata=trade
                )

                await self._handle_whale_transaction(whale_transaction)

        except Exception as e:
            logger.error("Error processing whale transaction: %s", str(e))

    def _classify_wallet(self, address: str) -> str:
        """Classify wallet type based on address"""
        if address in self.whale_addresses:
            return 'whale'

        # Check for known exchange addresses
        exchange_addresses = {
            'binance': ['0x1234567890abcdef'],  # Placeholder
            'coinbase': ['0x0987654321fedcba'],  # Placeholder
        }

        for exchange, addresses in exchange_addresses.items():
            if address in addresses:
                return 'exchange'

        return 'unknown'

    def _calculate_transaction_confidence(self, trade: Dict[str, Any]) -> float:
        """Calculate confidence score for transaction classification"""
        confidence = 0.5  # Base confidence

        # Factors that increase confidence:
        if trade.get('usd_value', 0) > 1000000:  # Over $1M
            confidence += 0.2

        if trade.get('address') in self.whale_addresses:
            confidence += 0.3

        if trade.get('liquidity_score', 0) > 0.8:
            confidence += 0.1

        return min(confidence, 1.0)

    async def _handle_whale_transaction(self, transaction: WhaleTransaction):
        """Handle a detected whale transaction"""
        try:
            # Add to recent transactions
            self.recent_transactions.append(transaction)

            # Keep only recent transactions (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.recent_transactions = [
                tx for tx in self.recent_transactions
                if tx.timestamp > cutoff_time
            ]

            # Update whale portfolio
            self._update_whale_portfolio(transaction)

            # Cache the transaction
            await self.cache.set_whale_transaction(
                transaction.address,
                {
                    'address': transaction.address,
                    'symbol': transaction.symbol,
                    'amount': transaction.amount,
                    'transaction_type': transaction.transaction_type,
                    'exchange': transaction.exchange,
                    'timestamp': transaction.timestamp.isoformat(),
                    'usd_value': transaction.usd_value,
                    'wallet_type': transaction.wallet_type,
                    'confidence': transaction.confidence
                }
            )

            # Check for alert conditions
            alert = await self._check_alert_conditions(transaction)
            if alert:
                await self._trigger_alert(alert)

            # Notify callbacks
            await self._notify_transaction_callbacks(transaction)

            logger.info(
                "Whale transaction detected: %s %s %.4f (%s) on %s ($%.0f)",
                transaction.transaction_type.upper(),
                transaction.symbol,
                transaction.amount,
                transaction.address[:8],
                transaction.exchange,
                transaction.usd_value
            )

        except Exception as e:
            logger.error("Error handling whale transaction: %s", str(e))

    def _update_whale_portfolio(self, transaction: WhaleTransaction):
        """Update whale portfolio tracking"""
        try:
            if transaction.address not in self.whale_portfolio:
                self.whale_portfolio[transaction.address] = {}

            current_amount = self.whale_portfolio[transaction.address].get(transaction.symbol, 0)

            if transaction.transaction_type == 'buy':
                current_amount += transaction.amount
            elif transaction.transaction_type == 'sell':
                current_amount -= transaction.amount

            self.whale_portfolio[transaction.address][transaction.symbol] = max(0, current_amount)

        except Exception as e:
            logger.error("Error updating whale portfolio: %s", str(e))

    async def _check_alert_conditions(self, transaction: WhaleTransaction) -> Optional[WhaleAlert]:
        """Check if transaction meets alert conditions"""
        try:
            alert_type = None
            severity = 'low'
            description = ""

            # Check transaction thresholds
            large_buy_threshold = self.alert_thresholds.get('large_buy', 500000)
            large_sell_threshold = self.alert_thresholds.get('large_sell', 500000)
            whale_movement_threshold = self.alert_thresholds.get('whale_movement', 1000000)

            if transaction.transaction_type == 'buy' and transaction.usd_value >= large_buy_threshold:
                alert_type = 'large_buy'
                description = f"Large buy order: ${transaction.usd_value:,.0f} of {transaction.symbol}"
                severity = 'high' if transaction.usd_value >= whale_movement_threshold else 'medium'

            elif transaction.transaction_type == 'sell' and transaction.usd_value >= large_sell_threshold:
                alert_type = 'large_sell'
                description = f"Large sell order: ${transaction.usd_value:,.0f} of {transaction.symbol}"
                severity = 'high' if transaction.usd_value >= whale_movement_threshold else 'medium'

            if transaction.wallet_type == 'whale' and transaction.usd_value >= whale_movement_threshold:
                alert_type = 'whale_movement'
                description = f"Whale movement detected: ${transaction.usd_value:,.0f} of {transaction.symbol}"
                severity = 'critical'

            if alert_type:
                alert = WhaleAlert(
                    alert_type=alert_type,
                    symbol=transaction.symbol,
                    severity=severity,
                    description=description,
                    timestamp=datetime.now(),
                    transactions=[transaction],
                    market_impact_score=self._calculate_market_impact(transaction)
                )
                return alert

        except Exception as e:
            logger.error("Error checking alert conditions: %s", str(e))

        return None

    def _calculate_market_impact(self, transaction: WhaleTransaction) -> float:
        """Calculate market impact score for a transaction"""
        try:
            # Base impact on transaction size relative to market
            impact = 0.0

            if transaction.usd_value >= 10000000:  # $10M+
                impact = 0.9
            elif transaction.usd_value >= 5000000:  # $5M+
                impact = 0.7
            elif transaction.usd_value >= 1000000:  # $1M+
                impact = 0.5
            elif transaction.usd_value >= 500000:   # $500K+
                impact = 0.3
            else:
                impact = 0.1

            # Increase impact for known whale addresses
            if transaction.wallet_type == 'whale':
                impact *= 1.5

            # Increase impact for volatile symbols
            if transaction.symbol in ['DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT']:
                impact *= 1.3

            return min(impact, 1.0)

        except Exception:
            return 0.5  # Medium impact if calculation fails

    async def _trigger_alert(self, alert: WhaleAlert):
        """Trigger a whale alert"""
        try:
            self.active_alerts.append(alert)

            # Keep only recent alerts (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.active_alerts = [
                a for a in self.active_alerts
                if a.timestamp > cutoff_time
            ]

            logger.warning(
                "🚨 WHALE ALERT: %s - %s (%s) - Impact: %.1f",
                alert.alert_type.upper(),
                alert.symbol,
                alert.severity.upper(),
                alert.market_impact_score
            )

            # Notify callbacks
            await self._notify_alert_callbacks(alert)

        except Exception as e:
            logger.error("Error triggering alert: %s", str(e))

    async def _analyze_whale_patterns(self):
        """Analyze patterns in whale behavior"""
        logger.info("Analyzing whale patterns")

        while self.is_running:
            try:
                await self._detect_accumulation_patterns()
                await self._detect_distribution_patterns()
                await self._detect_whale_clustering()

                await asyncio.sleep(60)  # Analyze every minute

            except Exception as e:
                logger.error("Error in whale pattern analysis: %s", str(e))
                await asyncio.sleep(60)

    async def _detect_accumulation_patterns(self):
        """Detect accumulation patterns (whales buying over time)"""
        try:
            # Look for patterns in recent transactions
            recent_whale_buys = [
                tx for tx in self.recent_transactions
                if tx.transaction_type == 'buy'
                and tx.wallet_type == 'whale'
                and tx.timestamp > datetime.now() - timedelta(hours=4)
            ]

            if len(recent_whale_buys) >= 3:
                # Group by symbol
                symbol_buys = {}
                for tx in recent_whale_buys:
                    if tx.symbol not in symbol_buys:
                        symbol_buys[tx.symbol] = []
                    symbol_buys[tx.symbol].append(tx)

                for symbol, buys in symbol_buys.items():
                    if len(buys) >= 3:
                        total_value = sum(tx.usd_value for tx in buys)
                        logger.info(
                            "Accumulation pattern detected: %d whale buys of %s ($%.0f total)",
                            len(buys), symbol, total_value
                        )

        except Exception as e:
            logger.error("Error detecting accumulation patterns: %s", str(e))

    async def _detect_distribution_patterns(self):
        """Detect distribution patterns (whales selling over time)"""
        try:
            # Look for patterns in recent transactions
            recent_whale_sells = [
                tx for tx in self.recent_transactions
                if tx.transaction_type == 'sell'
                and tx.wallet_type == 'whale'
                and tx.timestamp > datetime.now() - timedelta(hours=4)
            ]

            if len(recent_whale_sells) >= 3:
                # Group by symbol
                symbol_sells = {}
                for tx in recent_whale_sells:
                    if tx.symbol not in symbol_sells:
                        symbol_sells[tx.symbol] = []
                    symbol_sells[tx.symbol].append(tx)

                for symbol, sells in symbol_sells.items():
                    if len(sells) >= 3:
                        total_value = sum(tx.usd_value for tx in sells)
                        logger.info(
                            "Distribution pattern detected: %d whale sells of %s ($%.0f total)",
                            len(sells), symbol, total_value
                        )

        except Exception as e:
            logger.error("Error detecting distribution patterns: %s", str(e))

    async def _detect_whale_clustering(self):
        """Detect clustering of whale activity on specific symbols"""
        try:
            # Look for multiple whales trading the same symbol
            recent_whale_activity = [
                tx for tx in self.recent_transactions
                if tx.wallet_type == 'whale'
                and tx.timestamp > datetime.now() - timedelta(hours=2)
            ]

            symbol_activity = {}
            for tx in recent_whale_activity:
                if tx.symbol not in symbol_activity:
                    symbol_activity[tx.symbol] = []
                symbol_activity[tx.symbol].append(tx)

            for symbol, activities in symbol_activity.items():
                unique_whales = len(set(tx.address for tx in activities))
                if unique_whales >= 3:
                    logger.info(
                        "Whale clustering detected: %d whales active on %s",
                        unique_whales, symbol
                    )

        except Exception as e:
            logger.error("Error detecting whale clustering: %s", str(e))

    async def _cleanup_old_data(self):
        """Clean up old transaction data"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Clean every hour

                # Clean old transactions (older than 7 days)
                cutoff_time = datetime.now() - timedelta(days=7)
                self.recent_transactions = [
                    tx for tx in self.recent_transactions
                    if tx.timestamp > cutoff_time
                ]

                # Clean old alerts
                self.active_alerts = [
                    alert for alert in self.active_alerts
                    if alert.timestamp > cutoff_time
                ]

            except Exception as e:
                logger.error("Error in cleanup: %s", str(e))

    # Callback management
    def add_alert_callback(self, callback: Callable[[WhaleAlert], None]):
        """Add callback for whale alerts"""
        self.alert_callbacks.append(callback)

    def add_transaction_callback(self, callback: Callable[[WhaleTransaction], None]):
        """Add callback for whale transactions"""
        self.transaction_callbacks.append(callback)

    async def _notify_alert_callbacks(self, alert: WhaleAlert):
        """Notify all alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error("Error in alert callback: %s", str(e))

    async def _notify_transaction_callbacks(self, transaction: WhaleTransaction):
        """Notify all transaction callbacks"""
        for callback in self.transaction_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(transaction)
                else:
                    callback(transaction)
            except Exception as e:
                logger.error("Error in transaction callback: %s", str(e))

    # Data access methods
    def get_recent_transactions(self, hours: int = 24) -> List[WhaleTransaction]:
        """Get recent whale transactions"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [tx for tx in self.recent_transactions if tx.timestamp > cutoff_time]

    def get_active_alerts(self) -> List[WhaleAlert]:
        """Get currently active alerts"""
        return self.active_alerts.copy()

    def get_whale_portfolio(self, address: str) -> Dict[str, float]:
        """Get portfolio for a specific whale address"""
        return self.whale_portfolio.get(address, {}).copy()

    def get_top_whales_by_volume(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top whales by transaction volume"""
        whale_volumes = {}

        for tx in self.recent_transactions:
            if tx.timestamp > datetime.now() - timedelta(hours=24):
                if tx.address not in whale_volumes:
                    whale_volumes[tx.address] = 0
                whale_volumes[tx.address] += tx.usd_value

        # Sort by volume and return top whales
        sorted_whales = sorted(
            whale_volumes.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {
                'address': address,
                'total_volume_24h': volume,
                'wallet_type': self._classify_wallet(address)
            }
            for address, volume in sorted_whales[:limit]
        ]

    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get whale tracking statistics"""
        recent_txns = self.get_recent_transactions(hours=1)

        return {
            'is_running': self.is_running,
            'total_transactions_24h': len(self.get_recent_transactions(hours=24)),
            'transactions_last_hour': len(recent_txns),
            'active_alerts': len(self.active_alerts),
            'tracked_whales': len(self.whale_addresses),
            'monitored_exchanges': self.tracking_exchanges,
            'min_transaction_threshold': self.min_transaction_usd
        }
