# feat(core): reconciliation job for order status sync with exchange
from __future__ import annotations
import asyncio
from typing import List
from sqlalchemy import select, and_
from src.core.state_manager import StateManager, Order, Position
from src.connectors.bingx_client import BingXClient
from src.utils.audit_logger import AuditLogger
from src.utils.metrics import MetricsCollector
from decimal import Decimal

class ReconciliationJob:
    """Background job to reconcile order status with exchange."""
    
    def __init__(self, state_manager: StateManager, bingx_client: BingXClient,
                 audit_logger: AuditLogger, metrics: MetricsCollector):
        self.state_manager = state_manager
        self.bingx_client = bingx_client
        self.audit_logger = audit_logger
        self.metrics = metrics
        self.running = False
        self.interval = 30  # seconds
        
    async def start(self) -> None:
        """Start the reconciliation job."""
        if self.running:
            return
            
        self.running = True
        await self.audit_logger.log("reconciliation_job_started", {})
        
        while self.running:
            try:
                await self._reconcile_orders()
                await self._update_positions()
                self.metrics.increment_counter("reconciliation_cycles_total")
            except Exception as e:
                await self.audit_logger.log("reconciliation_error", {"error": str(e)})
                self.metrics.increment_counter("reconciliation_errors_total")
            
            await asyncio.sleep(self.interval)
    
    async def stop(self) -> None:
        """Stop the reconciliation job."""
        self.running = False
        await self.audit_logger.log("reconciliation_job_stopped", {})
    
    async def _reconcile_orders(self) -> None:
        """Reconcile orders that need status updates."""
        # Get orders that are SUBMITTED but not yet finalized
        async with self.state_manager.Session() as session:
            result = await session.execute(
                select(Order).where(
                    and_(
                        Order.status == "SUBMITTED",
                        Order.broker_order_id.is_not(None)
                    )
                )
            )
            orders = result.scalars().all()
            
            for order in orders:
                await self._reconcile_single_order(order)
    
    async def _reconcile_single_order(self, order: Order) -> None:
        """Reconcile a single order with the exchange."""
        try:
            if not order.broker_order_id:
                return
                
            # Get order status from exchange
            result = await self.bingx_client.get_order(order.symbol, order.broker_order_id)
            
            if result["status"] != "ok":
                await self.audit_logger.log("reconciliation_exchange_error", {
                    "order_id": order.id,
                    "broker_order_id": order.broker_order_id,
                    "error": result["data"]
                })
                return
            
            exchange_order = result["data"]
            exchange_status = exchange_order.get("status", "").upper()
            
            # Map exchange status to our internal status
            new_status = self._map_exchange_status(exchange_status)
            if new_status and new_status != order.status:
                # Update order status and filled quantity
                filled_qty = Decimal(str(exchange_order.get("executedQty", "0")))
                
                async with self.state_manager.Session() as session:
                    db_order = await session.get(Order, order.id)
                    if db_order:
                        db_order.status = new_status
                        db_order.filled_quantity = filled_qty
                        await session.commit()
                        
                        await self.audit_logger.log("order_status_reconciled", {
                            "order_id": order.id,
                            "old_status": order.status,
                            "new_status": new_status,
                            "filled_quantity": str(filled_qty)
                        })
                        
                        self.metrics.increment_counter("orders_reconciled_total")
                        
                        # Update position if order is filled
                        if new_status == "FILLED":
                            await self._update_position_for_order(db_order)
                            
        except Exception as e:
            await self.audit_logger.log("order_reconciliation_error", {
                "order_id": order.id,
                "broker_order_id": order.broker_order_id,
                "error": str(e)
            })
    
    def _map_exchange_status(self, exchange_status: str) -> str:
        """Map BingX order status to internal status."""
        status_mapping = {
            "NEW": "SUBMITTED",
            "PARTIALLY_FILLED": "PARTIALLY_FILLED",
            "FILLED": "FILLED",
            "CANCELED": "CANCELLED",
            "REJECTED": "REJECTED",
            "EXPIRED": "EXPIRED"
        }
        return status_mapping.get(exchange_status, "UNKNOWN")
    
    async def _update_position_for_order(self, order: Order) -> None:
        """Update position based on filled order."""
        try:
            async with self.state_manager.Session() as session:
                # Get existing position or create new one
                result = await session.execute(
                    select(Position).where(Position.symbol == order.symbol)
                )
                position = result.scalar_one_or_none()
                
                if not position:
                    position = Position(symbol=order.symbol)
                    session.add(position)
                
                # Calculate new position
                quantity_change = order.filled_quantity
                if order.side == "SELL":
                    quantity_change = -quantity_change
                
                old_size = position.size
                new_size = old_size + quantity_change
                
                # Update average price (simplified calculation)
                if new_size != 0 and order.price:
                    total_cost = old_size * position.avg_price + quantity_change * order.price
                    position.avg_price = abs(total_cost / new_size)
                elif new_size == 0:
                    position.avg_price = Decimal("0")
                
                position.size = new_size
                await session.commit()
                
                await self.audit_logger.log("position_updated", {
                    "symbol": order.symbol,
                    "order_id": order.id,
                    "old_size": str(old_size),
                    "new_size": str(new_size),
                    "avg_price": str(position.avg_price)
                })
                
        except Exception as e:
            await self.audit_logger.log("position_update_error", {
                "order_id": order.id,
                "symbol": order.symbol,
                "error": str(e)
            })
    
    async def _update_positions(self) -> None:
        """Update position metrics for monitoring."""
        try:
            async with self.state_manager.Session() as session:
                result = await session.execute(select(Position))
                positions = result.scalars().all()
                
                for position in positions:
                    self.metrics.set_gauge(
                        "position_size",
                        float(position.size),
                        {"symbol": position.symbol}
                    )
                    self.metrics.set_gauge(
                        "position_avg_price",
                        float(position.avg_price),
                        {"symbol": position.symbol}
                    )
                    
        except Exception as e:
            await self.audit_logger.log("position_metrics_update_error", {"error": str(e)})