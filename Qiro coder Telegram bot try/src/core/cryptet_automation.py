# feat(core): Main Cryptet automation service integrating all components
from __future__ import annotations
import asyncio
import logging
import os
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
            
            logger.info(f"Processing Cryptet link/symbol from Telegram message: {message[:50]}...")
            
            # Check if it's a crypto symbol only (fallback strategy)
            if self.link_handler.is_crypto_symbol(message) and not any(pattern in message.lower() for pattern in ['http', 'cryptet.com']):
                logger.info(f"Detected crypto symbol only: {message}")
                
                # Send immediate notification
                symbol_notification = self.signal_processor.process_symbol_only(message, metadata.get('source_url') or "")
                if symbol_notification:
                    await self._send_signal_message(symbol_notification)
                
                # Try to extract and process signal in background
                asyncio.create_task(self._process_symbol_background(message, metadata))
                return True
            
            # HAUPTÄNDERUNG: Scrape das Signal direkt von der Cryptet-Webseite
            # Verwende extrahierte URLs aus TelethonConnector falls verfügbar
            extracted_urls = metadata.get('extracted_urls', [])
            cryptet_url = None
            
            # Zuerst: Verwende extrahierte Cryptet-URLs
            for url in extracted_urls:
                if 'cryptet.com' in url.lower():
                    cryptet_url = url
                    logger.info(f"Using extracted Cryptet URL: {cryptet_url}")
                    break
            
            # Fallback: Extrahiere URL aus Nachrichtentext
            if not cryptet_url:
                message_entities = metadata.get('entities', [])
                cryptet_url = self.link_handler.extract_cryptet_url(message, message_entities)
            
            if not cryptet_url:
                logger.warning("Could not extract Cryptet URL from message")
                await self._send_error_message(f"Could not extract Cryptet URL from: {message[:50]}...")
                return False
            
            # Scrape das Signal von der Webseite
            logger.info(f"Scraping signal from Cryptet URL: {cryptet_url}")
            signal_data = await self.scraper.scrape_signal(cryptet_url)
            
            if not signal_data:
                logger.warning("Failed to scrape signal data from Cryptet website")
                await self._send_error_message(f"Failed to scrape signal from: {cryptet_url}")
                return False
            
            # Process and format signal für Cornix
            formatted_signal = self._format_cornix_signal(signal_data)
            
            if not formatted_signal:
                logger.error("Failed to format signal for Cornix")
                await self._send_error_message("Failed to format signal for Cornix")
                return False
            
            # Send formatted signal to own group
            await self._send_signal_message(formatted_signal)
            
            # Add to P&L monitoring
            signal_id = await self.pnl_monitor.add_signal_to_monitor(signal_data)
            
            logger.info(f"Successfully processed Cryptet signal: {signal_data.get('symbol', 'unknown')} (ID: {signal_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process Telegram message: {e}")
            await self._send_error_message(f"Error processing Cryptet signal: {str(e)}")
            return False
    
    async def _process_symbol_background(self, symbol_text: str, metadata: Dict[str, Any]) -> None:
        """Process crypto symbol in background to extract full signal details."""
        try:
            logger.info(f"Background processing of symbol: {symbol_text}")
            
            # Generate URL from symbol
            generated_url = self.link_handler.extract_cryptet_url(symbol_text)
            if not generated_url:
                logger.warning(f"Could not generate URL for symbol: {symbol_text}")
                return
            
            # Try to scrape the generated URL
            signal_data = await self.scraper.scrape_signal(generated_url)
            
            if signal_data:
                # Process and format the full signal
                formatted_signal = self.signal_processor.process_signal(signal_data)
                
                if formatted_signal:
                    # Send the complete signal
                    complete_signal = f"""
✅ **SIGNAL UPDATE** ✅

{formatted_signal}

📊 **Note:** This is the complete signal extracted from the Cryptet page."""
                    
                    await self._send_signal_message(complete_signal)
                    
                    # Add to P&L monitoring
                    signal_id = await self.pnl_monitor.add_signal_to_monitor(signal_data)
                    logger.info(f"Background processing successful for {symbol_text} (ID: {signal_id})")
                else:
                    logger.warning(f"Could not format signal from background processing: {symbol_text}")
            else:
                logger.warning(f"Could not scrape signal from generated URL for {symbol_text}: {generated_url}")
                
                # Send fallback message
                fallback_msg = f"""
⚠️ **SIGNAL EXTRACTION INCOMPLETE**

📊 **Symbol:** {symbol_text}
🔗 **Generated URL:** {generated_url}

⚠️ **Issue:** Could not extract full signal details
🔧 **Action:** Please check the signal manually

⚡ **Leverage:** 50x (recommended)
📊 **Source:** Cryptet.com"""
                
                await self._send_signal_message(fallback_msg)
                
        except Exception as e:
            logger.error(f"Failed background processing for symbol {symbol_text}: {e}")
            
            # Send error notification
            error_msg = f"""
❌ **BACKGROUND PROCESSING ERROR**

📊 **Symbol:** {symbol_text}
⚠️ **Error:** {str(e)}

🔧 **Please check this signal manually**"""
            
            await self._send_signal_message(error_msg)
    
    async def _send_signal_message(self, message: str) -> None:
        """Send signal message to own Telegram group."""
        try:
            if self.send_message_callback and self.own_group_chat_id:
                await self.send_message_callback(self.own_group_chat_id, message)
                logger.info("Signal message sent to own group")
            else:
                logger.warning("Cannot send message - callback or chat ID not configured")
                
        except Exception as e:
            logger.error(f"Failed to send signal message: {e}")
    
    async def _send_close_message(self, message: str) -> None:
        """Send close message to own Telegram group."""
        try:
            if self.send_message_callback and self.own_group_chat_id:
                await self.send_message_callback(self.own_group_chat_id, message)
                logger.info("Close message sent to own group")
            else:
                logger.warning("Cannot send close message - callback or chat ID not configured")
                
        except Exception as e:
            logger.error(f"Failed to send close message: {e}")
    
    async def _send_error_message(self, error_text: str) -> None:
        """Send error message to own Telegram group."""
        try:
            # Get current time safely
            try:
                current_time = asyncio.get_running_loop().time()
            except RuntimeError:
                # Fallback to system time if no event loop is running
                from time import time
                current_time = time()

            error_message = f"""
❌ **CRYPTET ERROR**

⚠️ **Error:** {error_text}
🕐 **Time:** {current_time}

Please check the logs for more details.
"""
            
            if self.send_message_callback and self.own_group_chat_id:
                await self.send_message_callback(self.own_group_chat_id, error_message)
                
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
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
        """Format signal data for Cornix compatibility - Cryptet signals usually have only ONE take profit."""
        try:
            symbol = signal_data.get('symbol', 'UNKNOWN')
            direction = signal_data.get('direction', 'UNKNOWN')
            entry_price = signal_data.get('entry_price', 'N/A')
            stop_loss = signal_data.get('stop_loss')
            take_profits = signal_data.get('take_profits', [])
            
            # Direction emoji
            direction_emoji = "🟢" if direction.upper() == "LONG" else "🔴"
            
            # Cornix-kompatibles Format (exakt wie Memory vorgibt)
            formatted_signal = f"{direction_emoji} {direction.title()}\n"
            formatted_signal += f"Name: {symbol}\n"
            formatted_signal += f"Margin mode: Cross (50X)\n\n"
            
            formatted_signal += "↪️ Entry price(USDT):\n"
            formatted_signal += f"{entry_price}\n\n"
            
            # Cryptet hat normalerweise nur EINEN Take Profit
            if take_profits:
                formatted_signal += "Targets(USDT):\n"
                for i, tp in enumerate(take_profits[:1], 1):  # Nur den ersten TP für Cryptet
                    formatted_signal += f"{i}) {tp}\n"
                
                # Für Cryptet: KEIN automatisches "unlimited" hinzufügen (Memory Punkt 5)
                # Nur die tatsächlich vorhandenen Targets weiterleiten
                formatted_signal += "\n"
            
            if stop_loss:
                formatted_signal += f"🛑 Stop Loss: {stop_loss}\n\n"
            
            # Add source info
            formatted_signal += "📊 Source: Cryptet.com (Auto-scraped)\n"
            formatted_signal += "🤖 Auto-forwarded with Cross 50x leverage\n"
            from datetime import datetime
            formatted_signal += f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}"
            
            return formatted_signal
            
        except Exception as e:
            logger.error(f"Failed to format Cornix signal: {e}")
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