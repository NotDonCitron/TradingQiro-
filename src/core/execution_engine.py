"""
Execution Engine Module

Main orchestration engine that coordinates all arbitrage trading components
including scanner, executor, risk manager, and signal systems.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field

from ..core.arbitrage_scanner import ArbitrageScanner
from ..core.opportunity_executor import OpportunityExecutor, ArbitrageExecution
from ..core.risk_manager import RiskManager
from ..core.whale_tracker import WhaleTracker, WhaleAlert
from ..core.premium_signal_aggregator import PremiumSignalAggregator, PremiumSignal
from ..config.arbitrage_config import ArbitrageConfig
from ..utils.arbitrage_cache import ArbitrageCache
from ..core.models import ArbitrageOpportunity

logger = logging.getLogger(__name__)


@dataclass
class EngineStats:
    """Statistics for the execution engine"""
    uptime_seconds: float = 0
    opportunities_found: int = 0
    opportunities_executed: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_profit: float = 0.0
    active_alerts: int = 0
    premium_signals_processed: int = 0
    whale_alerts_processed: int = 0
    last_opportunity_time: Optional[datetime] = None
    last_execution_time: Optional[datetime] = None
    is_running: bool = False


@dataclass
class EngineConfiguration:
    """Configuration for the execution engine"""
    enabled: bool = True
    max_concurrent_scans: int = 5
    opportunity_queue_size: int = 100
    execution_timeout_seconds: int = 30
    stats_update_interval: int = 60
    alert_cooldown_seconds: int = 300
    min_opportunity_age_before_execution: int = 2  # seconds


class ExecutionEngine:
    """
    Main orchestration engine that coordinates all arbitrage trading components.
    This is the central hub that connects scanners, executors, risk managers,
    and signal systems to create a complete trading automation system.
    """

    def __init__(self, config: ArbitrageConfig):
        self.config = config
        self.engine_config = EngineConfiguration()

        # Core components
        self.scanner = ArbitrageScanner(config)
        self.executor = OpportunityExecutor(config)
        self.risk_manager = RiskManager(config)
        self.whale_tracker = WhaleTracker(config)
        self.signal_aggregator = PremiumSignalAggregator(config)
        self.cache = ArbitrageCache()

        # Engine state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.stats = EngineStats()

        # Opportunity management
        self.opportunity_queue: List[ArbitrageOpportunity] = []
        self.processed_opportunities: Set[str] = set()
        self.active_executions: Dict[str, ArbitrageExecution] = {}

        # Alert management
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.last_alert_times: Dict[str, datetime] = {}

        # Callbacks for external integration
        self.opportunity_callbacks: List[callable] = []
        self.execution_callbacks: List[callable] = []
        self.alert_callbacks: List[callable] = []

        logger.info("ExecutionEngine initialized")

    async def start_engine(self):
        """Start the execution engine and all its components"""
        if self.is_running:
            logger.warning("Execution engine is already running")
            return

        self.is_running = True
        self.start_time = datetime.now()
        self.stats.is_running = True

        logger.info("🚀 Starting Execution Engine...")

        try:
            # Start all core components
            startup_tasks = [
                self.scanner.start_scanning(),
                self.executor.start_executor(),
                self.whale_tracker.start_tracking(),
                self.signal_aggregator.start_aggregation(),
                self._start_opportunity_processor(),
                self._start_stats_updater(),
                self._start_monitoring_tasks()
            ]

            # Set up callbacks
            self._setup_component_callbacks()

            # Wait for all components to start
            await asyncio.gather(*startup_tasks, return_exceptions=True)

            logger.info("✅ Execution Engine started successfully")
            logger.info("   • Arbitrage Scanner: Active")
            logger.info("   • Opportunity Executor: Active")
            logger.info("   • Risk Manager: Active")
            logger.info("   • Whale Tracker: Active")
            logger.info("   • Signal Aggregator: Active")

        except Exception as e:
            logger.error("❌ Error starting Execution Engine: %s", str(e))
            self.is_running = False
            raise

    async def stop_engine(self):
        """Stop the execution engine and all components"""
        logger.info("🛑 Stopping Execution Engine...")

        self.is_running = False
        self.stats.is_running = False

        try:
            # Stop all components
            stop_tasks = [
                self.scanner.stop_scanning(),
                self.executor.stop_executor(),
                self.whale_tracker.stop_tracking(),
                self.signal_aggregator.stop_aggregation()
            ]

            await asyncio.gather(*stop_tasks, return_exceptions=True)

            logger.info("✅ Execution Engine stopped successfully")

        except Exception as e:
            logger.error("Error stopping Execution Engine: %s", str(e))

    def _setup_component_callbacks(self):
        """Set up callbacks between components"""

        # Scanner -> Engine: New opportunities
        async def on_opportunity_found(opportunity: ArbitrageOpportunity):
            await self._handle_new_opportunity(opportunity)

        self.scanner.add_opportunity_callback(on_opportunity_found)

        # Executor -> Engine: Execution updates
        def on_execution_update(execution: ArbitrageExecution):
            asyncio.create_task(self._handle_execution_update(execution))

        self.executor.add_execution_callback(on_execution_update)

        # Whale Tracker -> Engine: Whale alerts
        def on_whale_alert(alert: WhaleAlert):
            asyncio.create_task(self._handle_whale_alert(alert))

        self.whale_tracker.add_alert_callback(on_whale_alert)

        # Signal Aggregator -> Engine: Premium signals
        def on_premium_signal(signal: PremiumSignal):
            asyncio.create_task(self._handle_premium_signal(signal))

        self.signal_aggregator.add_signal_callback(on_premium_signal)

    async def _handle_new_opportunity(self, opportunity: ArbitrageOpportunity):
        """Handle a new arbitrage opportunity from the scanner"""
        try:
            # Generate unique opportunity ID
            opportunity_id = f"{opportunity.symbol}_{opportunity.timestamp.timestamp()}"

            # Check if already processed
            if opportunity_id in self.processed_opportunities:
                return

            # Add to processing queue
            self.opportunity_queue.append(opportunity)
            self.processed_opportunities.add(opportunity_id)

            # Update stats
            self.stats.opportunities_found += 1
            self.stats.last_opportunity_time = datetime.now()

            # Log the opportunity
            logger.info(
                "🎯 New arbitrage opportunity: %s | Profit: %.4f%% | Buy: %s@%.6f | Sell: %s@%.6f",
                opportunity.symbol,
                opportunity.profit_percent,
                opportunity.buy_exchange,
                opportunity.buy_price,
                opportunity.sell_exchange,
                opportunity.sell_price
            )

            # Notify external callbacks
            await self._notify_opportunity_callbacks(opportunity)

            # Limit queue size
            if len(self.opportunity_queue) > self.engine_config.opportunity_queue_size:
                self.opportunity_queue = self.opportunity_queue[-self.engine_config.opportunity_queue_size:]

        except Exception as e:
            logger.error("Error handling new opportunity: %s", str(e))

    async def _handle_execution_update(self, execution: ArbitrageExecution):
        """Handle execution updates from the executor"""
        try:
            execution_id = execution.execution_id

            if execution.status == "completed":
                self.stats.successful_executions += 1
                self.stats.total_profit += execution.total_profit
                self.active_executions.pop(execution_id, None)

            elif execution.status == "failed":
                self.stats.failed_executions += 1
                self.active_executions.pop(execution_id, None)

            else:
                # Update active execution
                self.active_executions[execution_id] = execution

            self.stats.opportunities_executed += 1
            self.stats.last_execution_time = datetime.now()

            # Log execution result
            if execution.total_profit > 0:
                logger.info(
                    "💰 Execution completed: %s | Profit: $%.2f | Time: %dms",
                    execution_id,
                    execution.total_profit,
                    execution.execution_time_ms or 0
                )
            else:
                logger.warning(
                    "⚠️  Execution failed: %s | Notes: %s",
                    execution_id,
                    ", ".join(execution.notes)
                )

            # Notify external callbacks
            await self._notify_execution_callbacks(execution)

        except Exception as e:
            logger.error("Error handling execution update: %s", str(e))

    async def _handle_whale_alert(self, alert: WhaleAlert):
        """Handle whale alerts from the whale tracker"""
        try:
            alert_key = f"whale_{alert.symbol}_{alert.alert_type}"

            # Check alert cooldown
            if self._is_alert_on_cooldown(alert_key):
                return

            self.stats.whale_alerts_processed += 1
            self.stats.active_alerts += 1

            # Log whale alert
            logger.warning(
                "🐳 WHALE ALERT: %s | %s | Severity: %s | Impact: %.1f",
                alert.alert_type.upper(),
                alert.symbol,
                alert.severity.upper(),
                alert.market_impact_score
            )

            # Update alert cooldown
            self._set_alert_cooldown(alert_key)

            # Notify external callbacks
            await self._notify_alert_callbacks(alert)

        except Exception as e:
            logger.error("Error handling whale alert: %s", str(e))

    async def _handle_premium_signal(self, signal: PremiumSignal):
        """Handle premium signals from the signal aggregator"""
        try:
            if signal.confidence >= 0.6 and signal.validation_score >= 0.5:
                self.stats.premium_signals_processed += 1

                logger.info(
                    "📡 Premium signal: %s %s | Source: %s | Conf: %.2f | Valid: %.2f",
                    signal.direction,
                    signal.symbol,
                    signal.source,
                    signal.confidence,
                    signal.validation_score
                )

                # Cache the signal for scanner to use
                await self.cache.set_premium_signal(
                    f"signal_{signal.source}_{signal.symbol}_{int(signal.timestamp.timestamp())}",
                    {
                        'symbol': signal.symbol,
                        'direction': signal.direction,
                        'confidence': signal.confidence,
                        'validation_score': signal.validation_score,
                        'timestamp': signal.timestamp.isoformat()
                    }
                )

        except Exception as e:
            logger.error("Error handling premium signal: %s", str(e))

    async def _start_opportunity_processor(self):
        """Start the opportunity processing loop"""
        logger.info("Starting opportunity processor")

        while self.is_running:
            try:
                await self._process_opportunity_queue()
                await asyncio.sleep(1)  # Process every second

            except Exception as e:
                logger.error("Error in opportunity processor: %s", str(e))
                await asyncio.sleep(5)

    async def _process_opportunity_queue(self):
        """Process opportunities in the queue"""
        try:
            if not self.opportunity_queue:
                return

            # Process opportunities (limit to avoid overwhelming executor)
            opportunities_to_process = self.opportunity_queue[:self.engine_config.max_concurrent_scans]
            self.opportunity_queue = self.opportunity_queue[self.engine_config.max_concurrent_scans:]

            for opportunity in opportunities_to_process:
                try:
                    # Check if opportunity is still fresh enough
                    age_seconds = (datetime.now() - opportunity.timestamp).total_seconds()
                    if age_seconds >= self.engine_config.min_opportunity_age_before_execution:
                        # Submit for execution
                        execution = await self.executor.execute_opportunity(opportunity)

                        if execution:
                            self.active_executions[execution.execution_id] = execution
                            logger.info("Submitted opportunity for execution: %s", opportunity.symbol)

                except Exception as e:
                    logger.error("Error processing opportunity %s: %s", opportunity.symbol, str(e))

        except Exception as e:
            logger.error("Error processing opportunity queue: %s", str(e))

    async def _start_stats_updater(self):
        """Start the statistics updater"""
        while self.is_running:
            try:
                await asyncio.sleep(self.engine_config.stats_update_interval)

                # Update uptime
                if self.start_time:
                    self.stats.uptime_seconds = (datetime.now() - self.start_time).total_seconds()

                # Clean up old processed opportunities (keep last 1000)
                if len(self.processed_opportunities) > 1000:
                    # Convert to list, slice, and convert back to set
                    processed_list = list(self.processed_opportunities)
                    self.processed_opportunities = set(processed_list[-500:])

                # Clean up old alert cooldowns
                current_time = datetime.now()
                expired_cooldowns = [
                    key for key, cooldown_time in self.alert_cooldowns.items()
                    if current_time > cooldown_time
                ]
                for key in expired_cooldowns:
                    del self.alert_cooldowns[key]

            except Exception as e:
                logger.error("Error updating stats: %s", str(e))

    async def _start_monitoring_tasks(self):
        """Start monitoring and health check tasks"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Perform health checks
                await self._perform_health_checks()

                # Log system status
                await self._log_system_status()

            except Exception as e:
                logger.error("Error in monitoring tasks: %s", str(e))

    async def _perform_health_checks(self):
        """Perform health checks on all components"""
        try:
            health_issues = []

            # Check scanner
            if not self.scanner.is_running:
                health_issues.append("ArbitrageScanner is not running")

            # Check executor
            if not self.executor.is_running:
                health_issues.append("OpportunityExecutor is not running")

            # Check risk manager (always running)
            # Check whale tracker
            if not self.whale_tracker.is_running:
                health_issues.append("WhaleTracker is not running")

            # Check signal aggregator
            if not self.signal_aggregator.is_running:
                health_issues.append("PremiumSignalAggregator is not running")

            if health_issues:
                logger.warning("Health check issues: %s", ", ".join(health_issues))
            else:
                logger.info("✅ All components healthy")

        except Exception as e:
            logger.error("Error performing health checks: %s", str(e))

    async def _log_system_status(self):
        """Log comprehensive system status"""
        try:
            uptime_hours = self.stats.uptime_seconds / 3600

            logger.info("=" * 80)
            logger.info("📊 EXECUTION ENGINE STATUS")
            logger.info("=" * 80)
            logger.info("Uptime: %.1f hours", uptime_hours)
            logger.info("Opportunities Found: %d", self.stats.opportunities_found)
            logger.info("Opportunities Executed: %d", self.stats.opportunities_executed)
            logger.info("Successful Executions: %d", self.stats.successful_executions)
            logger.info("Failed Executions: %d", self.stats.failed_executions)
            logger.info("Total Profit: $%.2f", self.stats.total_profit)
            logger.info("Success Rate: %.1f%%",
                       (self.stats.successful_executions / max(self.stats.opportunities_executed, 1)) * 100)
            logger.info("Active Executions: %d", len(self.active_executions))
            logger.info("Whale Alerts: %d", self.stats.whale_alerts_processed)
            logger.info("Premium Signals: %d", self.stats.premium_signals_processed)
            logger.info("Queue Size: %d", len(self.opportunity_queue))
            logger.info("=" * 80)

        except Exception as e:
            logger.error("Error logging system status: %s", str(e))

    def _is_alert_on_cooldown(self, alert_key: str) -> bool:
        """Check if an alert is on cooldown"""
        return alert_key in self.alert_cooldowns and datetime.now() < self.alert_cooldowns[alert_key]

    def _set_alert_cooldown(self, alert_key: str):
        """Set cooldown for an alert"""
        cooldown_time = datetime.now() + timedelta(seconds=self.engine_config.alert_cooldown_seconds)
        self.alert_cooldowns[alert_key] = cooldown_time

    # Callback management
    def add_opportunity_callback(self, callback):
        """Add callback for new opportunities"""
        self.opportunity_callbacks.append(callback)

    def add_execution_callback(self, callback):
        """Add callback for execution updates"""
        self.execution_callbacks.append(callback)

    def add_alert_callback(self, callback):
        """Add callback for alerts"""
        self.alert_callbacks.append(callback)

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

    async def _notify_alert_callbacks(self, alert):
        """Notify all alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error("Error in alert callback: %s", str(e))

    # Data access methods
    def get_engine_stats(self) -> EngineStats:
        """Get comprehensive engine statistics"""
        return self.stats

    def get_component_status(self) -> Dict[str, bool]:
        """Get status of all components"""
        return {
            'scanner': self.scanner.is_running,
            'executor': self.executor.is_running,
            'whale_tracker': self.whale_tracker.is_running,
            'signal_aggregator': self.signal_aggregator.is_running,
            'engine': self.is_running
        }

    def get_active_opportunities(self) -> List[ArbitrageOpportunity]:
        """Get currently active opportunities"""
        return self.opportunity_queue.copy()

    def get_active_executions(self) -> List[ArbitrageExecution]:
        """Get currently active executions"""
        return list(self.active_executions.values())

    def cancel_all_executions(self):
        """Cancel all active executions"""
        self.executor.cancel_all_executions()

    def emergency_stop(self):
        """Emergency stop all trading activities"""
        logger.warning("🚨 EMERGENCY STOP ACTIVATED")

        # Cancel all executions
        self.cancel_all_executions()

        # Stop all components
        asyncio.create_task(self.stop_engine())

    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health information"""
        try:
            return {
                'engine_status': self.get_component_status(),
                'engine_stats': {
                    'uptime_seconds': self.stats.uptime_seconds,
                    'opportunities_found': self.stats.opportunities_found,
                    'successful_executions': self.stats.successful_executions,
                    'total_profit': self.stats.total_profit,
                    'active_executions': len(self.active_executions)
                },
                'scanner_stats': self.scanner.get_scanner_stats(),
                'executor_stats': self.executor.get_execution_stats(),
                'whale_stats': self.whale_tracker.get_tracking_stats(),
                'signal_stats': self.signal_aggregator.get_aggregation_stats(),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Error getting system health: %s", str(e))
            return {'error': str(e)}
