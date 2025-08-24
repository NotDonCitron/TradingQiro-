# feat(core): P&L monitor for automatic signal closing when Cryptet shows profit/loss
from __future__ import annotations
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
import time

from src.connectors.cryptet_scraper import CryptetScraper
from src.core.cryptet_signal_parser import CryptetSignalProcessor

logger = logging.getLogger(__name__)

class CryptetPnLMonitor:
    """Monitor Cryptet signals for P&L updates and auto-close them."""
    
    def __init__(self, 
                 scraper: Optional[CryptetScraper] = None,
                 close_callback: Optional[Callable[[str], Awaitable[None]]] = None):
        self.scraper = scraper or CryptetScraper()
        self.signal_processor = CryptetSignalProcessor()
        self.close_callback = close_callback
        
        # Active signals being monitored
        self.active_signals: Dict[str, Dict[str, Any]] = {}
        
        # Monitor settings
        self.check_interval = 300  # 5 minutes
        self.max_duration = timedelta(hours=6)  # Max 6 hours monitoring
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self) -> None:
        """Start the P&L monitoring service."""
        if self.is_running:
            logger.warning("P&L monitor is already running")
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("P&L monitor started")
    
    async def stop_monitoring(self) -> None:
        """Stop the P&L monitoring service."""
        self.is_running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("P&L monitor stopped")
    
    async def add_signal_to_monitor(self, signal_data: Dict[str, Any]) -> str:
        """Add a signal to P&L monitoring."""
        try:
            # Generate unique signal ID
            signal_id = self._generate_signal_id(signal_data)
            
            # Prepare monitoring data
            monitor_data = {
                'signal_id': signal_id,
                'signal_data': signal_data.copy(),
                'start_time': datetime.now(),
                'url': signal_data.get('url'),
                'symbol': signal_data.get('symbol', 'UNKNOWN'),
                'direction': signal_data.get('direction', 'UNKNOWN'),
                'last_check': datetime.now(),
                'check_count': 0,
                'status': 'monitoring'
            }
            
            # Add to active signals
            self.active_signals[signal_id] = monitor_data
            
            logger.info(f"Added signal {signal_id} ({monitor_data['symbol']}) to P&L monitoring")
            return signal_id
            
        except Exception as e:
            logger.error(f"Failed to add signal to monitoring: {e}")
            return ""
    
    async def remove_signal_from_monitor(self, signal_id: str) -> bool:
        """Remove a signal from monitoring."""
        if signal_id in self.active_signals:
            signal_data = self.active_signals[signal_id]
            del self.active_signals[signal_id]
            logger.info(f"Removed signal {signal_id} ({signal_data.get('symbol', 'UNKNOWN')}) from monitoring")
            return True
        
        return False
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        logger.info("P&L monitoring loop started")
        
        while self.is_running:
            try:
                # Check all active signals
                signals_to_remove = []
                
                for signal_id, monitor_data in self.active_signals.items():
                    try:
                        should_close = await self._check_signal(signal_id, monitor_data)
                        if should_close:
                            signals_to_remove.append(signal_id)
                            
                    except Exception as e:
                        logger.error(f"Error checking signal {signal_id}: {e}")
                        # Don't remove on error, try again next time
                
                # Remove closed signals
                for signal_id in signals_to_remove:
                    await self.remove_signal_from_monitor(signal_id)
                
                # Log status
                if self.active_signals:
                    logger.info(f"Monitoring {len(self.active_signals)} active signals")
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("P&L monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _check_signal(self, signal_id: str, monitor_data: Dict[str, Any]) -> bool:
        """Check a single signal for P&L updates."""
        try:
            # Update check info
            monitor_data['last_check'] = datetime.now()
            monitor_data['check_count'] += 1
            
            # Check if max duration exceeded
            if datetime.now() - monitor_data['start_time'] > self.max_duration:
                logger.info(f"Signal {signal_id} exceeded max monitoring duration")
                await self._close_signal_timeout(signal_id, monitor_data)
                return True
            
            # Check P&L status on Cryptet
            url = monitor_data.get('url')
            if not url:
                logger.warning(f"No URL for signal {signal_id}")
                return True
            
            pnl_status = await self.scraper.check_pnl_status(url)
            
            if pnl_status.get('updated', False):
                logger.info(f"P&L updated for signal {signal_id}: {pnl_status}")
                await self._close_signal_pnl(signal_id, monitor_data, pnl_status)
                return True
            
            # Log periodic status
            if monitor_data['check_count'] % 12 == 0:  # Every hour (12 * 5 min)
                duration = datetime.now() - monitor_data['start_time']
                logger.info(f"Signal {signal_id} ({monitor_data['symbol']}) - monitoring for {duration}")
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check signal {signal_id}: {e}")
            return False
    
    async def _close_signal_pnl(self, signal_id: str, monitor_data: Dict[str, Any], pnl_status: Dict[str, Any]) -> None:
        """Close signal due to P&L update."""
        try:
            signal_data = monitor_data['signal_data']
            
            # Format close message
            close_message = self.signal_processor.process_signal_close(signal_data, pnl_status)
            
            # Send close message via callback
            if self.close_callback:
                await self.close_callback(close_message)
            
            # Log closure
            duration = datetime.now() - monitor_data['start_time']
            logger.info(f"Signal {signal_id} closed due to P&L update after {duration}: {pnl_status}")
            
        except Exception as e:
            logger.error(f"Failed to close signal {signal_id} due to P&L: {e}")
    
    async def _close_signal_timeout(self, signal_id: str, monitor_data: Dict[str, Any]) -> None:
        """Close signal due to timeout."""
        try:
            signal_data = monitor_data['signal_data']
            
            # Create timeout status
            timeout_status = {
                'updated': True,
                'result': 'timeout',
                'percentage': '0'
            }
            
            # Format close message
            close_message = self.signal_processor.process_signal_close(signal_data, timeout_status)
            close_message += "\n⏰ **Reason:** Maximum monitoring time exceeded (6h)"
            
            # Send close message via callback
            if self.close_callback:
                await self.close_callback(close_message)
            
            # Log timeout
            duration = datetime.now() - monitor_data['start_time']
            logger.info(f"Signal {signal_id} closed due to timeout after {duration}")
            
        except Exception as e:
            logger.error(f"Failed to close signal {signal_id} due to timeout: {e}")
    
    def _generate_signal_id(self, signal_data: Dict[str, Any]) -> str:
        """Generate unique signal ID."""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        direction = signal_data.get('direction', 'UNKNOWN')
        timestamp = str(int(time.time()))
        
        return f"{symbol}_{direction}_{timestamp}"
    
    def get_active_signals_count(self) -> int:
        """Get count of actively monitored signals."""
        return len(self.active_signals)
    
    def get_active_signals_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all active signals."""
        info = {}
        
        for signal_id, monitor_data in self.active_signals.items():
            duration = datetime.now() - monitor_data['start_time']
            info[signal_id] = {
                'symbol': monitor_data.get('symbol', 'UNKNOWN'),
                'direction': monitor_data.get('direction', 'UNKNOWN'),
                'duration': str(duration),
                'check_count': monitor_data.get('check_count', 0),
                'status': monitor_data.get('status', 'unknown')
            }
        
        return info
    
    async def manual_close_signal(self, signal_id: str, reason: str = "manual") -> bool:
        """Manually close a monitored signal."""
        if signal_id not in self.active_signals:
            return False
        
        try:
            monitor_data = self.active_signals[signal_id]
            signal_data = monitor_data['signal_data']
            
            # Create manual close status
            manual_status = {
                'updated': True,
                'result': 'manual',
                'percentage': '0'
            }
            
            # Format close message
            close_message = self.signal_processor.process_signal_close(signal_data, manual_status)
            close_message += f"\n👤 **Reason:** Manual close ({reason})"
            
            # Send close message via callback
            if self.close_callback:
                await self.close_callback(close_message)
            
            # Remove from monitoring
            await self.remove_signal_from_monitor(signal_id)
            
            logger.info(f"Manually closed signal {signal_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to manually close signal {signal_id}: {e}")
            return False
    
    def set_close_callback(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Set the callback function for sending close messages."""
        self.close_callback = callback
    
    async def close(self) -> None:
        """Close the P&L monitor and cleanup resources."""
        await self.stop_monitoring()
        
        if self.scraper:
            await self.scraper.close()