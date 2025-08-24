"""
Opportunity Executor Module

Executes arbitrage opportunities and manages trade lifecycle across multiple exchanges
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..core.models import ArbitrageOpportunity
from ..connectors.exchange_apis import ExchangeAPIManager
from ..core.risk_manager import RiskManager
from ..config.arbitrage_config import ArbitrageConfig
from ..utils.arbitrage_cache import ArbitrageCache

logger = logging.getLogger(__name__)


class ExecutionState(Enum):
    """Execution states for arbitrage opportunities"""
    PENDING = "pending"
    EXECUTING = "executing"
    PARTIALLY_FILLED = "partially_filled"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrderType(Enum):
    """Types of orders for arbitrage execution"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


@dataclass
class ExecutionOrder:
    """Represents an individual order in an arbitrage execution"""
    order_id: str
    exchange: str
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    executed_quantity: float = 0.0
    executed_price: Optional[float] = None
    status: str = "pending"
    fees: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None


@dataclass
class ArbitrageExecution:
    """Represents a complete arbitrage execution"""
    execution_id: str
    opportunity: ArbitrageOpportunity
    buy_order: Optional[ExecutionOrder] = None
    sell_order: Optional[ExecutionOrder] = None
    status: ExecutionState = ExecutionState.PENDING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_profit: float = 0.0
    total_fees: float = 0.0
    execution_time_ms: Optional[int] = None
    notes: List[str] = field(default_factory=list)


class OpportunityExecutor:
    """
    Executes arbitrage opportunities by placing orders on multiple exchanges
    and managing the complete trade lifecycle.
    """

    def __init__(self, config: ArbitrageConfig):
        self.config = config
        self.exchange_manager = ExchangeAPIManager(config)
        self.risk_manager = RiskManager(config)
        self.cache = ArbitrageCache()
        self.is_running = False

        # Execution settings
        self.max_execution_time = 30.0  # seconds
        self.min_profit_threshold = config.min_profit_threshold_percent
        self.max_concurrent_executions = 3

        # Execution tracking
        self.active_executions: Dict[str, ArbitrageExecution] = {}
        self.completed_executions: List[ArbitrageExecution] = []
        self.failed_executions: List[ArbitrageExecution] = []

        # Callbacks
        self.execution_callbacks: List[Callable[[ArbitrageExecution], None]] = []

        logger.info("OpportunityExecutor initialized with max concurrent: %d",
                   self.max_concurrent_executions)

    async def start_executor(self):
        """Start the opportunity executor"""
        if self.is_running:
            logger.warning("Opportunity executor is already running")
            return

        self.is_running = True
        logger.info("Starting opportunity executor...")

        try:
            # Start execution monitoring tasks
            tasks = [
                self._monitor_active_executions(),
                self._cleanup_expired_executions(),
                self._log_execution_stats()
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error("Error in opportunity executor: %s", str(e))
            self.is_running = False

    async def stop_executor(self):
        """Stop the opportunity executor"""
        logger.info("Stopping opportunity executor...")
        self.is_running = False

        # Cancel all active executions
        for execution in self.active_executions.values():
            await self._cancel_execution(execution)

    async def execute_opportunity(self, opportunity: ArbitrageOpportunity) -> Optional[ArbitrageExecution]:
        """
        Execute an arbitrage opportunity

        Returns the execution object if execution was started, None if rejected
        """
        try:
            # Pre-execution validation
            if not await self._validate_opportunity(opportunity):
                return None

            # Check concurrency limits
            if len(self.active_executions) >= self.max_concurrent_executions:
                logger.warning("Max concurrent executions reached, rejecting opportunity")
                return None

            # Create execution object
            execution_id = f"arb_{opportunity.symbol}_{int(datetime.now().timestamp())}"
            execution = ArbitrageExecution(
                execution_id=execution_id,
                opportunity=opportunity
            )

            # Start execution
            self.active_executions[execution_id] = execution
            logger.info("Starting execution %s for %s", execution_id, opportunity.symbol)

            # Execute the arbitrage trade
            await self._execute_arbitrage_trade(execution)

            return execution

        except Exception as e:
            logger.error("Error executing opportunity: %s", str(e))
            return None

    async def _validate_opportunity(self, opportunity: ArbitrageOpportunity) -> bool:
        """Validate opportunity before execution"""
        try:
            # Check if opportunity is still valid
            if opportunity.timestamp < datetime.now() - timedelta(seconds=self.config.max_opportunity_age_seconds):
                logger.warning("Opportunity expired: %s", opportunity.symbol)
                return False

            # Check risk limits
            risk_check = self.risk_manager.can_execute_opportunity(opportunity)
            if not risk_check['can_execute']:
                logger.warning("Risk check failed for %s: %s",
                             opportunity.symbol, risk_check['reasons'])
                return False

            # Update opportunity with risk score
            opportunity.risk_score = risk_check['risk_score']

            # Check profit threshold
            if opportunity.profit_percent < self.min_profit_threshold:
                logger.warning("Profit below threshold: %.4f%% < %.4f%%",
                             opportunity.profit_percent, self.min_profit_threshold)
                return False

            # Check if we have sufficient balance (placeholder)
            if not await self._check_sufficient_balance(opportunity):
                logger.warning("Insufficient balance for %s", opportunity.symbol)
                return False

            return True

        except Exception as e:
            logger.error("Error validating opportunity: %s", str(e))
            return False

    async def _check_sufficient_balance(self, opportunity: ArbitrageOpportunity) -> bool:
        """Check if we have sufficient balance for the trade (placeholder)"""
        # In a real implementation, this would check actual balances
        # For now, assume we have sufficient balance
        return True

    async def _execute_arbitrage_trade(self, execution: ArbitrageExecution):
        """Execute the arbitrage trade on both exchanges"""
        try:
            opportunity = execution.opportunity
            execution.status = ExecutionState.EXECUTING

            # Step 1: Place buy order on lower price exchange
            buy_order = await self._place_buy_order(opportunity)
            if buy_order:
                execution.buy_order = buy_order

                # Step 2: Place sell order on higher price exchange
                sell_order = await self._place_sell_order(opportunity)
                if sell_order:
                    execution.sell_order = sell_order

                    # Step 3: Monitor execution progress
                    await self._monitor_execution_progress(execution)
                else:
                    # Cancel buy order if sell order failed
                    await self._cancel_order(buy_order)
                    execution.status = ExecutionState.FAILED
                    execution.notes.append("Failed to place sell order")
            else:
                execution.status = ExecutionState.FAILED
                execution.notes.append("Failed to place buy order")

        except Exception as e:
            logger.error("Error executing arbitrage trade: %s", str(e))
            execution.status = ExecutionState.FAILED
            execution.notes.append(f"Execution error: {str(e)}")

        finally:
            # Update execution completion
            execution.end_time = datetime.now()
            if execution.start_time and execution.end_time:
                execution.execution_time_ms = int(
                    (execution.end_time - execution.start_time).total_seconds() * 1000
                )

            # Move to completed or failed list
            if execution.status in [ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED]:
                execution_id = execution.execution_id
                if execution.status == ExecutionState.COMPLETED:
                    self.completed_executions.append(execution)
                else:
                    self.failed_executions.append(execution)

                # Remove from active
                if execution_id in self.active_executions:
                    del self.active_executions[execution_id]

            # Notify callbacks
            await self._notify_execution_callbacks(execution)

    async def _place_buy_order(self, opportunity: ArbitrageOpportunity) -> Optional[ExecutionOrder]:
        """Place buy order on the exchange with lower price"""
        try:
            # Calculate buy parameters
            buy_exchange = opportunity.buy_exchange
            symbol = opportunity.symbol
            buy_price = opportunity.buy_price

            # Estimate quantity based on available balance and volume
            quantity = min(
                opportunity.volume * 0.1,  # Use 10% of available volume
                1000.0  # Max position size
            )

            # Create order object
            order = ExecutionOrder(
                order_id=f"buy_{symbol}_{int(datetime.now().timestamp())}",
                exchange=buy_exchange,
                symbol=symbol,
                side="buy",
                order_type=OrderType.LIMIT if buy_price > 0 else OrderType.MARKET,
                quantity=quantity,
                price=buy_price if buy_price > 0 else None
            )

            # In a real implementation, this would place the actual order
            # For now, simulate successful order placement
            order.status = "filled"
            order.executed_quantity = quantity
            order.executed_price = buy_price
            order.fees = quantity * buy_price * self.config.get_fee_rate(buy_exchange, 'taker')

            logger.info("Buy order placed: %s %s %.4f @ %.6f on %s",
                       order.side.upper(), symbol, quantity, buy_price, buy_exchange)

            return order

        except Exception as e:
            logger.error("Error placing buy order: %s", str(e))
            return None

    async def _place_sell_order(self, opportunity: ArbitrageOpportunity) -> Optional[ExecutionOrder]:
        """Place sell order on the exchange with higher price"""
        try:
            # Calculate sell parameters
            sell_exchange = opportunity.sell_exchange
            symbol = opportunity.symbol
            sell_price = opportunity.sell_price

            # Use same quantity as buy order
            quantity = opportunity.volume * 0.1

            # Create order object
            order = ExecutionOrder(
                order_id=f"sell_{symbol}_{int(datetime.now().timestamp())}",
                exchange=sell_exchange,
                symbol=symbol,
                side="sell",
                order_type=OrderType.LIMIT if sell_price > 0 else OrderType.MARKET,
                quantity=quantity,
                price=sell_price if sell_price > 0 else None
            )

            # In a real implementation, this would place the actual order
            # For now, simulate successful order placement
            order.status = "filled"
            order.executed_quantity = quantity
            order.executed_price = sell_price
            order.fees = quantity * sell_price * self.config.get_fee_rate(sell_exchange, 'taker')

            logger.info("Sell order placed: %s %s %.4f @ %.6f on %s",
                       order.side.upper(), symbol, quantity, sell_price, sell_exchange)

            return order

        except Exception as e:
            logger.error("Error placing sell order: %s", str(e))
            return None

    async def _monitor_execution_progress(self, execution: ArbitrageExecution):
        """Monitor the progress of an arbitrage execution"""
        try:
            start_time = datetime.now()

            while datetime.now() - start_time < timedelta(seconds=self.max_execution_time):
                # Check if both orders are filled
                if (execution.buy_order and execution.buy_order.status == "filled" and
                    execution.sell_order and execution.sell_order.status == "filled"):

                    # Calculate profit
                    await self._calculate_execution_profit(execution)
                    execution.status = ExecutionState.COMPLETED

                    logger.info("Arbitrage execution completed: %s, profit: $%.2f",
                              execution.execution_id, execution.total_profit)
                    break

                # Check for partial fills or failures
                elif ((execution.buy_order and execution.buy_order.status == "failed") or
                      (execution.sell_order and execution.sell_order.status == "failed")):

                    execution.status = ExecutionState.FAILED
                    execution.notes.append("Order execution failed")
                    break

                await asyncio.sleep(0.1)  # Check every 100ms

            else:
                # Execution timed out
                execution.status = ExecutionState.EXPIRED
                execution.notes.append("Execution timed out")

                # Cancel any pending orders
                if execution.buy_order and execution.buy_order.status == "pending":
                    await self._cancel_order(execution.buy_order)
                if execution.sell_order and execution.sell_order.status == "pending":
                    await self._cancel_order(execution.sell_order)

        except Exception as e:
            logger.error("Error monitoring execution: %s", str(e))
            execution.status = ExecutionState.FAILED
            execution.notes.append(f"Monitoring error: {str(e)}")

    async def _calculate_execution_profit(self, execution: ArbitrageExecution):
        """Calculate the profit from a completed arbitrage execution"""
        try:
            if not execution.buy_order or not execution.sell_order:
                return

            buy_order = execution.buy_order
            sell_order = execution.sell_order

            # Calculate revenue from sell order
            sell_revenue = sell_order.executed_quantity * (sell_order.executed_price or 0)

            # Calculate cost from buy order
            buy_cost = buy_order.executed_quantity * (buy_order.executed_price or 0)

            # Calculate total fees
            total_fees = buy_order.fees + sell_order.fees

            # Calculate profit
            gross_profit = sell_revenue - buy_cost
            net_profit = gross_profit - total_fees

            execution.total_profit = net_profit
            execution.total_fees = total_fees

            # Update risk manager with actual profit
            self.risk_manager.record_position_close(
                execution.opportunity.symbol,
                net_profit,
                success=net_profit > 0
            )

        except Exception as e:
            logger.error("Error calculating execution profit: %s", str(e))

    async def _cancel_order(self, order: ExecutionOrder):
        """Cancel an order (placeholder)"""
        try:
            order.status = "cancelled"
            logger.info("Order cancelled: %s on %s", order.order_id, order.exchange)
        except Exception as e:
            logger.error("Error cancelling order: %s", str(e))

    async def _cancel_execution(self, execution: ArbitrageExecution):
        """Cancel an entire arbitrage execution"""
        try:
            execution.status = ExecutionState.CANCELLED
            execution.notes.append("Execution cancelled")

            # Cancel any pending orders
            if execution.buy_order and execution.buy_order.status == "pending":
                await self._cancel_order(execution.buy_order)
            if execution.sell_order and execution.sell_order.status == "pending":
                await self._cancel_order(execution.sell_order)

        except Exception as e:
            logger.error("Error cancelling execution: %s", str(e))

    async def _monitor_active_executions(self):
        """Monitor active executions for timeouts"""
        while self.is_running:
            try:
                current_time = datetime.now()

                for execution_id, execution in list(self.active_executions.items()):
                    if current_time - execution.start_time > timedelta(seconds=self.max_execution_time):
                        logger.warning("Execution timeout: %s", execution_id)
                        await self._cancel_execution(execution)

                await asyncio.sleep(1)

            except Exception as e:
                logger.error("Error monitoring active executions: %s", str(e))

    async def _cleanup_expired_executions(self):
        """Clean up old completed and failed executions"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Clean every 5 minutes
                current_time = datetime.now()

                # Keep only recent executions (last 24 hours)
                cutoff_time = current_time - timedelta(hours=24)

                self.completed_executions = [
                    exec for exec in self.completed_executions
                    if exec.start_time > cutoff_time
                ]

                self.failed_executions = [
                    exec for exec in self.failed_executions
                    if exec.start_time > cutoff_time
                ]

            except Exception as e:
                logger.error("Error cleaning up executions: %s", str(e))

    async def _log_execution_stats(self):
        """Log execution statistics periodically"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Log every 5 minutes

                stats = self.get_execution_stats()
                logger.info("Execution stats - Active: %d, Completed: %d, Failed: %d, Success Rate: %.1f%%",
                          stats['active_executions'],
                          stats['completed_executions'],
                          stats['failed_executions'],
                          stats['success_rate'])

            except Exception as e:
                logger.error("Error logging execution stats: %s", str(e))

    # Callback management
    def add_execution_callback(self, callback: Callable[[ArbitrageExecution], None]):
        """Add callback for execution events"""
        self.execution_callbacks.append(callback)

    async def _notify_execution_callbacks(self, execution: ArbitrageExecution):
        """Notify all execution callbacks"""
        for callback in self.execution_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(execution)
                else:
                    callback(execution)
            except Exception as e:
                logger.error("Error in execution callback: %s", str(e))

    # Data access methods
    def get_active_executions(self) -> List[ArbitrageExecution]:
        """Get all active executions"""
        return list(self.active_executions.values())

    def get_completed_executions(self, hours: int = 24) -> List[ArbitrageExecution]:
        """Get completed executions from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [exec for exec in self.completed_executions if exec.start_time > cutoff_time]

    def get_failed_executions(self, hours: int = 24) -> List[ArbitrageExecution]:
        """Get failed executions from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [exec for exec in self.failed_executions if exec.start_time > cutoff_time]

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        recent_completed = self.get_completed_executions(hours=24)
        recent_failed = self.get_failed_executions(hours=24)

        total_recent = len(recent_completed) + len(recent_failed)
        success_rate = (len(recent_completed) / total_recent * 100) if total_recent > 0 else 0

        total_profit = sum(exec.total_profit for exec in recent_completed)
        avg_execution_time = 0
        if recent_completed:
            valid_times = [exec.execution_time_ms for exec in recent_completed if exec.execution_time_ms]
            if valid_times:
                avg_execution_time = sum(valid_times) / len(valid_times)

        return {
            'active_executions': len(self.active_executions),
            'completed_executions': len(self.completed_executions),
            'failed_executions': len(self.failed_executions),
            'recent_completed_24h': len(recent_completed),
            'recent_failed_24h': len(recent_failed),
            'success_rate': success_rate,
            'total_profit_24h': total_profit,
            'avg_execution_time_ms': avg_execution_time,
            'is_running': self.is_running
        }

    def get_execution_by_id(self, execution_id: str) -> Optional[ArbitrageExecution]:
        """Get execution by ID"""
        return self.active_executions.get(execution_id)

    def cancel_all_executions(self):
        """Cancel all active executions"""
        for execution in self.active_executions.values():
            asyncio.create_task(self._cancel_execution(execution))
