"""
Data models for the arbitrage trading system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class ArbitrageOpportunity:
    """Data class representing an arbitrage opportunity"""
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    profit_percent: float
    volume: float
    timestamp: datetime
    fees: Dict[str, float]
    estimated_profit: float
    risk_score: float
    triangular_path: Optional[List[str]] = None


@dataclass
class PriceData:
    """Data class for exchange price information"""
    exchange: str
    symbol: str
    bid_price: float
    ask_price: float
    volume_24h: float
    last_update: datetime
    spread: float
    liquidity_score: float


@dataclass
class ExchangeConnection:
    """Exchange connection information"""
    exchange_name: str
    connection_state: 'ConnectionState'
    last_update: datetime
    reconnect_attempts: int
    error_message: Optional[str] = None


@dataclass
class PriceUpdate:
    """Real-time price update data"""
    exchange: str
    symbol: str
    bid_price: float
    ask_price: float
    last_price: float
    volume_24h: float
    timestamp: datetime
    update_type: str  # 'snapshot', 'update', 'trade'
