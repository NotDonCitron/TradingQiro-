# feat(core): Main Cryptet automation service integrating all components
from __future__ import annotations
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable

from src.connectors.cryptet_scraper import CryptetScraper
from src.core.cryptet_link_handler import CryptetLinkHandler
from src.core.cryptet_signal_parser import CryptetSignalProcessor
from src.core.cryptet_pnl_monitor import CryptetPnLMonitor

logger = logging.getLogger(__name__)

class CryptetAutomation:
    """Main automation service for Cryptet signals."""
    
    def __init__(self, send_message_callback: Optional[Callable[[str, str], Awaitable[None]]] = None):
        # Initialize components
        self.scraper = CryptetScraper(
            cookies_file=os.getenv("CRYPTET_COOKIES_FILE", "cookies.txt"),
            headless=os.getenv("CRYPTET_HEADLESS", "true").lower() == "true"
        )
        self.link_handler = CryptetLinkHandler(self.scraper)
        self.signal_processor = CryptetSignalProcessor()
        self.pnl_monitor = CryptetPnLMonitor(self.scraper)
        
        # Telegram configuration
        self.own_group_chat_id = os.getenv("OWN_GROUP_CHAT_ID")
        self.send_message_callback = send_message_callback
        
        # Set up P&L monitor callback
        self.pnl_monitor.set_close_callback(self._send_close_message)
        
        # Status
        self.is_initialized = False
        self.is_running = False
    
    async def initialize(self) -> bool:
        """Initialize the Cryptet automation system."""
        try:
            logger.info("Initializing Cryptet automation system...")
            
            # Check configuration
            if not self.own_group_chat_id:
                logger.error("OWN_GROUP_CHAT_ID not configured")
                return False
            
            # Initialize browser
            browser_success = await self.scraper.initialize_browser()
            if not browser_success:
                logger.error("Failed to initialize browser")
                return False
            
            # Start P&L monitoring
            await self.pnl_monitor.start_monitoring()
            
            self.is_initialized = True
            self.is_running = True
            
            logger.info("Cryptet automation system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Cryptet automation: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the Cryptet automation system."""
        try:
            logger.info("Shutting down Cryptet automation system...")
            
            self.is_running = False
            
            # Stop P&L monitoring
            await self.pnl_monitor.stop_monitoring()
            
            # Close scraper
            await self.scraper.close()
            
            logger.info("Cryptet automation system shut down")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def process_telegram_message(self, message: str, metadata: Dict[str, Any]) -> bool:
        """Process incoming Telegram message for Cryptet links."""
        try:
            if not self.is_running:
                logger.warning("Cryptet automation not running")
                return False
            
            # Check if message contains Cryptet link or symbol
            if not self.link_handler.is_cryptet_link(message):
                return False
            
            # Check if it's a crypto symbol only (fallback strategy)
            if self.link_handler.is_crypto_symbol(message) and not any(pattern in message.lower() for pattern in ['http', 'cryptet.com']):
                
                # Für Symbol-only: Sende direkte Notification
                symbol_notification = self.signal_processor.process_symbol_only(message, metadata.get('source_url') or "")
                if symbol_notification:
                    await self._send_signal_message(symbol_notification)
                
                return True
            
            # HAUPTÄNDERUNG: Scrape das Signal direkt von der Cryptet-Webseite
            # Verwende extrahierte URLs aus TelethonConnector falls verfügbar
            extracted_urls = metadata.get('extracted_urls', [])
            cryptet_url = None
            
            # Zuerst: Verwende extrahierte Cryptet-URLs
            for url in extracted_urls:
                if 'cryptet.com' in url.lower():
                    cryptet_url = url
                    break
            
            # Fallback: Extrahiere URL aus Nachrichtentext
            if not cryptet_url:
                message_entities = metadata.get('entities', [])
                cryptet_url = self.link_handler.extract_cryptet_url(message, message_entities)
            
            if not cryptet_url:
                return False
            
            # Scrape das Signal von der Webseite
            signal_data = await self.scraper.scrape_signal(cryptet_url)
            
            if not signal_data:
                return False
            
            # Process and format signal für Cornix
            formatted_signal = self._format_cornix_signal(signal_data)
            
            if not formatted_signal:
                return False
            
            # Send formatted signal to own group
            await self._send_signal_message(formatted_signal)
            
            # Add to P&L monitoring
            signal_id = await self.pnl_monitor.add_signal_to_monitor(signal_data)
            
            return True
            
        except Exception as e:
            return False

    
    async def _send_signal_message(self, message: str) -> None:
        """Send signal message to own Telegram group."""
        try:
            if self.send_message_callback and self.own_group_chat_id:
                await self.send_message_callback(self.own_group_chat_id, message)
        except Exception:
            pass
    
    async def _send_close_message(self, message: str) -> None:
        """Send close message to own Telegram group."""
        try:
            if self.send_message_callback and self.own_group_chat_id:
                await self.send_message_callback(self.own_group_chat_id, message)
        except Exception:
            pass

    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the automation system."""
        return {
            'initialized': self.is_initialized,
            'running': self.is_running,
            'active_signals': self.pnl_monitor.get_active_signals_count(),
            'own_group_configured': bool(self.own_group_chat_id),
            'callback_configured': bool(self.send_message_callback)
        }
    
    def get_active_signals(self) -> Dict[str, Dict[str, Any]]:
        """Get information about actively monitored signals."""
        return self.pnl_monitor.get_active_signals_info()
    
    async def manual_close_signal(self, signal_id: str, reason: str = "manual") -> bool:
        """Manually close a monitored signal."""
        return await self.pnl_monitor.manual_close_signal(signal_id, reason)
    
    def _format_cornix_signal(self, signal_data: Dict[str, Any]) -> Optional[str]:
        """Format signal data for Cornix compatibility - clean production format."""
        try:
            symbol = signal_data.get('symbol', 'UNKNOWN')
            direction = signal_data.get('direction', 'UNKNOWN')
            entry_price = signal_data.get('entry_price', 'N/A')
            take_profits = signal_data.get('take_profits', [])
            
            # Direction emoji
            direction_emoji = "🟢" if direction.upper() == "LONG" else "🔴"
            
            # Cornix-kompatibles Format (saubere Production-Version)
            formatted_signal = f"{direction_emoji} {direction.title()}\n"
            formatted_signal += f"Name: {symbol}\n"
            formatted_signal += f"Margin mode: Cross (50X)\n\n"
            
            formatted_signal += "↪️ Entry price(USDT):\n"
            formatted_signal += f"{entry_price}\n\n"
            
            # Nur echte Take Profits, kein Debug-Text
            if take_profits:
                formatted_signal += "Targets(USDT):\n"
                for i, tp in enumerate(take_profits[:1], 1):  # Nur den ersten TP für Cryptet
                    formatted_signal += f"{i}) {tp}\n"
            
            return formatted_signal
            
        except Exception:
            return None
    
    def set_send_message_callback(self, callback: Callable[[str, str], Awaitable[None]]) -> None:
        """Set the callback function for sending messages."""
        self.send_message_callback = callback
        
    async def test_cryptet_link(self, url: str) -> Optional[Dict[str, Any]]:
        """Test processing a Cryptet link (for debugging)."""
        try:
            logger.info(f"Testing Cryptet link: {url}")
            
            if not self.link_handler.validate_cryptet_url(url):
                logger.error(f"Invalid Cryptet URL: {url}")
                return None
            
            # Process the link
            signal_data = await self.scraper.scrape_signal(url)
            
            if signal_data:
                logger.info(f"Successfully scraped test signal: {signal_data}")
                return signal_data
            else:
                logger.warning("No signal data found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to test Cryptet link: {e}")
            return None