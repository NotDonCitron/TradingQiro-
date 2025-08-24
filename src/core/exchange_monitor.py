"""
Exchange Monitor Module

Real-time price monitoring across multiple exchanges with WebSocket support
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from ..connectors.exchange_apis import ExchangeAPIManager
from ..config.arbitrage_config import ArbitrageConfig
from ..core.models import PriceUpdate, ExchangeConnection, ConnectionState

logger = logging.getLogger(__name__)


class ExchangeMonitor:
    """
    Monitors real-time price data from multiple exchanges using WebSocket connections
    and REST API fallbacks.
    """

    def __init__(self, config: ArbitrageConfig):
        self.config = config
        self.exchange_manager = ExchangeAPIManager(config)
        self.is_running = False

        # Price data storage
        self.price_data: Dict[str, Dict[str, PriceUpdate]] = {}  # exchange -> symbol -> price
        self.connections: Dict[str, ExchangeConnection] = {}

        # Callbacks
        self.price_update_callbacks: List[Callable[[PriceUpdate], None]] = []
        self.connection_callbacks: List[Callable[[str, ConnectionState], None]] = []

        # Monitoring settings
        self.update_interval = 1.0  # seconds between REST API updates
        self.reconnect_delay = 5.0  # seconds between reconnection attempts
        self.max_reconnect_attempts = 5

        logger.info("ExchangeMonitor initialized for %d exchanges", len(config.get_enabled_exchanges()))

    async def start_monitoring(self):
        """Start monitoring all configured exchanges"""
        if self.is_running:
            logger.warning("Exchange monitor is already running")
            return

        self.is_running = True
        logger.info("Starting exchange monitoring...")

        try:
            # Initialize connections
            await self._initialize_connections()

            # Start monitoring tasks
            tasks = [
                self._monitor_exchange(exchange_name)
                for exchange_name in self.config.get_enabled_exchanges()
            ]

            # Add REST API fallback task
            tasks.append(self._rest_api_fallback())

            # Run all monitoring tasks
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error("Error in exchange monitoring: %s", str(e))
            self.is_running = False

    async def stop_monitoring(self):
        """Stop all monitoring activities"""
        logger.info("Stopping exchange monitoring...")
        self.is_running = False

        # Close all connections
        for exchange_name in self.connections.keys():
            await self._close_connection(exchange_name)

    async def _initialize_connections(self):
        """Initialize connection tracking for all exchanges"""
        for exchange_name in self.config.get_enabled_exchanges():
            self.connections[exchange_name] = ExchangeConnection(
                exchange_name=exchange_name,
                connection_state=ConnectionState.DISCONNECTED,
                last_update=datetime.now(),
                reconnect_attempts=0
            )
            self.price_data[exchange_name] = {}

    async def _monitor_exchange(self, exchange_name: str):
        """Monitor a specific exchange for price updates"""
        logger.info("Starting monitoring for exchange: %s", exchange_name)

        while self.is_running:
            try:
                # Try WebSocket connection first
                await self._websocket_monitoring(exchange_name)

                # If WebSocket fails, the method will return and we'll try again
                await asyncio.sleep(self.reconnect_delay)

            except Exception as e:
                logger.error("Error monitoring %s: %s", exchange_name, str(e))

                # Update connection state
                if exchange_name in self.connections:
                    self.connections[exchange_name].connection_state = ConnectionState.ERROR
                    self.connections[exchange_name].error_message = str(e)

                # Notify callbacks
                await self._notify_connection_callbacks(exchange_name, ConnectionState.ERROR)

                await asyncio.sleep(self.reconnect_delay)

    async def _websocket_monitoring(self, exchange_name: str):
        """Monitor exchange using WebSocket connection"""
        try:
            # Update connection state
            self.connections[exchange_name].connection_state = ConnectionState.CONNECTING
            await self._notify_connection_callbacks(exchange_name, ConnectionState.CONNECTING)

            # Get WebSocket connection (placeholder - would implement actual WebSocket logic)
            ws_connection = await self._establish_websocket_connection(exchange_name)

            if ws_connection:
                self.connections[exchange_name].connection_state = ConnectionState.CONNECTED
                self.connections[exchange_name].reconnect_attempts = 0
                await self._notify_connection_callbacks(exchange_name, ConnectionState.CONNECTED)

                # Monitor WebSocket messages
                await self._handle_websocket_messages(exchange_name, ws_connection)
            else:
                raise Exception("Failed to establish WebSocket connection")

        except Exception as e:
            logger.error("WebSocket monitoring failed for %s: %s", exchange_name, str(e))
            raise e

    async def _establish_websocket_connection(self, exchange_name: str):
        """Establish WebSocket connection to exchange (placeholder implementation)"""
        # This would implement actual WebSocket connection logic for each exchange
        # For now, we'll simulate the connection establishment

        try:
            # Check if exchange supports WebSocket
            if not self._exchange_supports_websocket(exchange_name):
                logger.info("Exchange %s does not support WebSocket, using REST API", exchange_name)
                return None

            # Simulate connection establishment
            await asyncio.sleep(0.1)  # Simulate connection time

            # In a real implementation, this would:
            # 1. Create WebSocket connection URL
            # 2. Establish connection with proper authentication
            # 3. Subscribe to relevant price feeds
            # 4. Return connection object

            logger.info("WebSocket connection established for %s", exchange_name)
            return {"mock_connection": True, "exchange": exchange_name}

        except Exception as e:
            logger.error("Failed to establish WebSocket for %s: %s", exchange_name, str(e))
            return None

    async def _handle_websocket_messages(self, exchange_name: str, connection):
        """Handle incoming WebSocket messages"""
        try:
            # In a real implementation, this would listen for WebSocket messages
            # and parse price updates from the exchange's format

            # For simulation, we'll periodically fetch updates
            symbols = self.config.trading_symbols

            while self.is_running and connection:
                try:
                    for symbol in symbols:
                        # Simulate receiving price update from WebSocket
                        await self._process_price_update(exchange_name, symbol, "websocket")

                    await asyncio.sleep(0.1)  # Small delay between symbol updates

                except Exception as e:
                    logger.error("Error processing WebSocket message for %s: %s", exchange_name, str(e))
                    break

        except Exception as e:
            logger.error("WebSocket message handling failed for %s: %s", exchange_name, str(e))

        finally:
            # Connection lost, update state
            self.connections[exchange_name].connection_state = ConnectionState.DISCONNECTED
            await self._notify_connection_callbacks(exchange_name, ConnectionState.DISCONNECTED)

    async def _rest_api_fallback(self):
        """Provide REST API fallback for exchanges without WebSocket or when WebSocket fails"""
        logger.info("Starting REST API fallback monitoring")

        while self.is_running:
            try:
                for exchange_name in self.config.get_enabled_exchanges():
                    connection = self.connections.get(exchange_name)

                    # Only use REST API if WebSocket is not connected
                    if connection and connection.connection_state != ConnectionState.CONNECTED:
                        await self._rest_api_update(exchange_name)

                await asyncio.sleep(self.update_interval)

            except Exception as e:
                logger.error("Error in REST API fallback: %s", str(e))
                await asyncio.sleep(self.update_interval)

    async def _rest_api_update(self, exchange_name: str):
        """Update price data using REST API"""
        try:
            symbols = self.config.trading_symbols

            for symbol in symbols:
                await self._process_price_update(exchange_name, symbol, "rest")

        except Exception as e:
            logger.error("REST API update failed for %s: %s", exchange_name, str(e))

    async def _process_price_update(self, exchange_name: str, symbol: str, source: str):
        """Process a price update from any source"""
        try:
            # Get price data from exchange
            price_data = await self.exchange_manager.get_price_data(exchange_name, symbol)

            if not price_data:
                return

            # Create price update object
            price_update = PriceUpdate(
                exchange=exchange_name,
                symbol=symbol,
                bid_price=price_data.get('bid', 0),
                ask_price=price_data.get('ask', 0),
                last_price=price_data.get('last', 0),
                volume_24h=price_data.get('volume_24h', 0),
                timestamp=datetime.now(),
                update_type=source
            )

            # Store price data
            if exchange_name not in self.price_data:
                self.price_data[exchange_name] = {}
            self.price_data[exchange_name][symbol] = price_update

            # Update connection info
            if exchange_name in self.connections:
                self.connections[exchange_name].last_update = datetime.now()

            # Notify callbacks
            await self._notify_price_callbacks(price_update)

        except Exception as e:
            logger.error("Error processing price update for %s %s: %s",
                        exchange_name, symbol, str(e))

    async def _close_connection(self, exchange_name: str):
        """Close connection for a specific exchange"""
        try:
            if exchange_name in self.connections:
                self.connections[exchange_name].connection_state = ConnectionState.DISCONNECTED
                await self._notify_connection_callbacks(exchange_name, ConnectionState.DISCONNECTED)

            logger.info("Closed connection for %s", exchange_name)

        except Exception as e:
            logger.error("Error closing connection for %s: %s", exchange_name, str(e))

    def _exchange_supports_websocket(self, exchange_name: str) -> bool:
        """Check if exchange supports WebSocket connections"""
        # In a real implementation, this would check exchange capabilities
        websocket_supported = {
            'binance': True,
            'coinbase': True,
            'kraken': True,
            'bingx': False  # Example: BingX might not support WebSocket in our implementation
        }

        return websocket_supported.get(exchange_name.lower(), False)

    # Callback management
    def add_price_callback(self, callback: Callable[[PriceUpdate], None]):
        """Add callback for price updates"""
        self.price_update_callbacks.append(callback)

    def add_connection_callback(self, callback: Callable[[str, ConnectionState], None]):
        """Add callback for connection state changes"""
        self.connection_callbacks.append(callback)

    async def _notify_price_callbacks(self, price_update: PriceUpdate):
        """Notify all price update callbacks"""
        for callback in self.price_update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(price_update)
                else:
                    callback(price_update)
            except Exception as e:
                logger.error("Error in price callback: %s", str(e))

    async def _notify_connection_callbacks(self, exchange_name: str, state: ConnectionState):
        """Notify all connection callbacks"""
        for callback in self.connection_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(exchange_name, state)
                else:
                    callback(exchange_name, state)
            except Exception as e:
                logger.error("Error in connection callback: %s", str(e))

    # Data access methods
    def get_price_data(self, exchange_name: str, symbol: str) -> Optional[PriceUpdate]:
        """Get latest price data for a symbol on an exchange"""
        return self.price_data.get(exchange_name, {}).get(symbol)

    def get_all_price_data(self, symbol: str) -> Dict[str, PriceUpdate]:
        """Get price data for a symbol across all exchanges"""
        result = {}
        for exchange_name, exchange_data in self.price_data.items():
            if symbol in exchange_data:
                result[exchange_name] = exchange_data[symbol]
        return result

    def get_exchange_connection_state(self, exchange_name: str) -> Optional[ConnectionState]:
        """Get connection state for an exchange"""
        connection = self.connections.get(exchange_name)
        return connection.connection_state if connection else None

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        total_symbols = len(self.config.trading_symbols)
        total_exchanges = len(self.config.get_enabled_exchanges())

        connected_exchanges = sum(
            1 for conn in self.connections.values()
            if conn.connection_state == ConnectionState.CONNECTED
        )

        return {
            'is_running': self.is_running,
            'total_exchanges': total_exchanges,
            'connected_exchanges': connected_exchanges,
            'total_symbols': total_symbols,
            'update_interval': self.update_interval,
            'exchanges': {
                name: {
                    'state': conn.connection_state.value,
                    'last_update': conn.last_update.isoformat(),
                    'reconnect_attempts': conn.reconnect_attempts,
                    'error_message': conn.error_message
                }
                for name, conn in self.connections.items()
            }
        }

    def get_price_spread(self, symbol: str) -> Dict[str, float]:
        """Get bid-ask spread for a symbol across all exchanges"""
        spreads = {}
        price_data = self.get_all_price_data(symbol)

        for exchange_name, price_update in price_data.items():
            if price_update.bid_price > 0 and price_update.ask_price > 0:
                spread = ((price_update.ask_price - price_update.bid_price) / price_update.ask_price) * 100
                spreads[exchange_name] = spread

        return spreads

    def get_best_prices(self, symbol: str) -> Dict[str, Any]:
        """Get best bid and ask prices across all exchanges"""
        price_data = self.get_all_price_data(symbol)

        if not price_data:
            return {}

        best_bid = max(
            (price for price in price_data.values() if price.bid_price > 0),
            key=lambda x: x.bid_price,
            default=None
        )

        best_ask = min(
            (price for price in price_data.values() if price.ask_price > 0),
            key=lambda x: x.ask_price,
            default=None
        )

        return {
            'best_bid': {
                'exchange': best_bid.exchange if best_bid else None,
                'price': best_bid.bid_price if best_bid else 0,
                'timestamp': best_bid.timestamp.isoformat() if best_bid else None
            },
            'best_ask': {
                'exchange': best_ask.exchange if best_ask else None,
                'price': best_ask.ask_price if best_ask else 0,
                'timestamp': best_ask.timestamp.isoformat() if best_ask else None
            }
        }
