# feat(core): async task executor for order processing with idempotency and circuit breaker
from __future__ import annotations
import asyncio
import os
import uuid
import re
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import select
from src.core.state_manager import StateManager, Order
from src.connectors.bingx_client import BingXClient
from src.utils.audit_logger import AuditLogger
from src.utils.metrics import MetricsCollector

class CircuitBreaker:
    """Simple circuit breaker to prevent API overload."""
    def __init__(self, failure_threshold: int = 5, timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        import time
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        import time
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class TaskExecutor:
    """Handles async order execution with idempotency and retry logic."""
    
    def __init__(self, state_manager: StateManager, bingx_client: BingXClient, 
                 audit_logger: AuditLogger, metrics: MetricsCollector):
        self.state_manager = state_manager
        self.bingx_client = bingx_client
        self.audit_logger = audit_logger
        self.metrics = metrics
        self.circuit_breaker = CircuitBreaker()
        self.trading_enabled = os.getenv("TRADING_ENABLED", "false").lower() == "true"
        self._processed_signals = set()  # Simple deduplication
        
    async def process_signal(self, message: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Process a trading signal from Telegram and create an order."""
        signal_id = f"{metadata.get('chat_id', 0)}_{metadata.get('message_id', 0)}"
        
        # Deduplication check
        if signal_id in self._processed_signals:
            await self.audit_logger.log("signal_duplicate", {"signal_id": signal_id, "message": message})
            return None
            
        self._processed_signals.add(signal_id)
        
        try:
            # Parse trading signal
            parsed_signal = self._parse_signal(message)
            if not parsed_signal:
                await self.audit_logger.log("signal_parse_failed", {"message": message, "signal_id": signal_id})
                self.metrics.increment_counter("signals_parse_failed_total")
                return None
            
            # Create order in database
            order_id = await self._create_order(parsed_signal, metadata)
            await self.audit_logger.log("order_created", {"order_id": order_id, "signal": parsed_signal})
            self.metrics.increment_counter("orders_created_total")
            
            # Execute order if trading is enabled
            if self.trading_enabled and self.circuit_breaker.can_execute():
                await self._execute_order(order_id)
            else:
                await self.audit_logger.log("order_not_executed", {
                    "order_id": order_id, 
                    "trading_enabled": self.trading_enabled,
                    "circuit_breaker_open": not self.circuit_breaker.can_execute()
                })
            
            return order_id
            
        except Exception as e:
            await self.audit_logger.log("signal_processing_error", {
                "signal_id": signal_id, 
                "message": message, 
                "error": str(e)
            })
            self.metrics.increment_counter("signals_processing_errors_total")
            return None
    
    def _parse_signal(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse trading signal from message text."""
        try:
            # Verschiedene Signal-Formate unterstützen
            parsed = self._parse_advanced_signal(message) or self._parse_simple_signal(message)
            return parsed
        except Exception as e:
            return None
    
    def _parse_simple_signal(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse simple format: 'BUY BTCUSDT 0.1' or 'SELL ETHUSDT 0.5'"""
        pattern = r'(BUY|SELL)\s+([A-Z]+USDT)\s+([\d.]+)'
        match = re.search(pattern, message.upper())
        
        if not match:
            return None
            
        side, symbol, quantity_str = match.groups()
        
        try:
            quantity = Decimal(quantity_str)
            if quantity <= 0:
                return None
                
            return {
                "side": side,
                "symbol": symbol,
                "quantity": quantity,
                "order_type": "MARKET"
            }
        except (ValueError, Exception):
            return None
    
    def _parse_advanced_signal(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse advanced signal formats with Entry/Stop Loss/Take Profit"""
        text = message.upper().replace('#', '')
        
        # Erkenne Trading-Richtung
        side = None
        if any(word in text for word in ['LONG', 'BUY', 'KAUFEN']):
            side = 'BUY'
        elif any(word in text for word in ['SHORT', 'SELL', 'VERKAUFEN']):
            side = 'SELL'
        
        if not side:
            return None
        
        # Erkenne Symbol (verschiedene Formate)
        symbol_patterns = [
            r'([A-Z]{2,10})/USDT',
            r'([A-Z]{2,10})USDT',
            r'#([A-Z]{2,10}USDT)'
        ]
        
        symbol = None
        for pattern in symbol_patterns:
            match = re.search(pattern, text)
            if match:
                symbol = match.group(1)
                if not symbol.endswith('USDT'):
                    symbol += 'USDT'
                break
        
        if not symbol:
            return None
        
        # Erkenne Entry-Preis
        entry_price = None
        entry_patterns = [
            r'ENTRY[:\s]*([\d.,]+)(?:\s*-\s*([\d.,]+))?',
            r'EINSTIEG[:\s]*([\d.,]+)(?:\s*-\s*([\d.,]+))?',
            r'📍\s*ENTRY[:\s]*([\d.,]+)(?:\s*-\s*([\d.,]+))?'
        ]
        
        for pattern in entry_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    # Verwende den ersten Preis oder Durchschnitt bei Range
                    price1 = float(match.group(1).replace(',', ''))
                    price2 = match.group(2)
                    if price2:
                        price2 = float(price2.replace(',', ''))
                        entry_price = (price1 + price2) / 2
                    else:
                        entry_price = price1
                    break
                except (ValueError, AttributeError):
                    continue
        
        # Erkenne Stop Loss
        stop_loss = None
        sl_patterns = [
            r'STOP\s*LOSS[:\s]*([\d.,]+)',
            r'SL[:\s]*([\d.,]+)',
            r'⛔[\s]*([\d.,]+)',
            r'⛔\s*STOP\s*LOSS[:\s]*([\d.,]+)'
        ]
        
        for pattern in sl_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    stop_loss = float(match.group(1).replace(',', ''))
                    break
                except ValueError:
                    continue
        
        # Erkenne Take Profit Levels
        take_profits = []
        tp_patterns = [
            r'(?:TARGET|TP|TAKE\s*PROFIT|🎯)\s*\d*[:\s]*([\d.,]+)',
            r'🎯\s*TARGET\s*\d*[:\s]*([\d.,]+)'
        ]
        
        for pattern in tp_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    tp_price = float(match.group(1).replace(',', ''))
                    if tp_price not in take_profits:
                        take_profits.append(tp_price)
                except ValueError:
                    continue
        
        # Erkenne Leverage
        leverage = 1
        leverage_patterns = [
            r'(?:LEVERAGE|LEV)[:\s]*([\d]+)X?',
            r'([\d]+)X',
            r'CROSS\s+([\d]+)X?',
            r'⚡\s*CROSS\s+([\d]+)X?'
        ]
        
        for pattern in leverage_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    leverage = int(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Standard-Quantity basierend auf Entry-Preis berechnen
        quantity = 0.001  # Default Mindestmenge
        if entry_price and entry_price > 0:
            # Kleine feste USD-Position (z.B. $10)
            quantity = round(10.0 / entry_price, 6)
        
        # Validierung
        if not all([side, symbol]):
            return None
        
        signal_data = {
            "side": side,
            "symbol": symbol,
            "quantity": Decimal(str(quantity)),
            "order_type": "MARKET",
            "leverage": leverage
        }
        
        # Zusätzliche Daten hinzufügen wenn verfügbar
        if entry_price:
            signal_data["entry_price"] = entry_price
        if stop_loss:
            signal_data["stop_loss"] = stop_loss
        if take_profits:
            signal_data["take_profits"] = take_profits
        
        return signal_data
    
    async def _create_order(self, signal: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Create order in database with PENDING status."""
        order_id = str(uuid.uuid4())
        
        async with self.state_manager.Session() as session:
            order = Order(
                id=order_id,
                symbol=signal["symbol"],
                side=signal["side"],
                quantity=signal["quantity"],
                status="PENDING",
                metadata={**metadata, "signal": signal}
            )
            session.add(order)
            await session.commit()
            
        return order_id
    
    async def _execute_order(self, order_id: str) -> None:
        """Execute order on BingX with idempotency."""
        try:
            async with self.state_manager.Session() as session:
                order = await session.get(Order, order_id)
                if not order:
                    raise ValueError(f"Order {order_id} not found")
                
                # Check if already submitted to avoid double execution
                if order.status != "PENDING":
                    await self.audit_logger.log("order_already_processed", {
                        "order_id": order_id, 
                        "current_status": order.status
                    })
                    return
                
                # Submit to exchange with Cross margin
                result = await self.bingx_client.create_order(
                    symbol=order.symbol,
                    side=order.side.lower(),
                    order_type="MARKET",
                    quantity=float(order.quantity),
                    leverage=50,  # Default leverage
                    margin_mode="cross"  # Always use Cross margin
                )
                
                if result["status"] == "ok":
                    broker_order_id = result["data"].get("orderId")
                    await self.state_manager.set_order_status(order_id, "SUBMITTED", broker_order_id)
                    self.circuit_breaker.record_success()
                    self.metrics.increment_counter("orders_submitted_total")
                    await self.audit_logger.log("order_submitted", {
                        "order_id": order_id,
                        "broker_order_id": broker_order_id
                    })
                else:
                    await self.state_manager.set_order_status(order_id, "FAILED")
                    self.circuit_breaker.record_failure()
                    self.metrics.increment_counter("orders_failed_total")
                    await self.audit_logger.log("order_submission_failed", {
                        "order_id": order_id,
                        "error": result["data"]
                    })
                    
        except Exception as e:
            self.circuit_breaker.record_failure()
            self.metrics.increment_counter("orders_failed_total")
            await self.audit_logger.log("order_execution_error", {
                "order_id": order_id,
                "error": str(e)
            })
            try:
                await self.state_manager.set_order_status(order_id, "ERROR")
            except Exception:
                pass  # Don't fail on status update failure