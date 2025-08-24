# feat(core): Cryptet link handler for automatic URL detection and processing
from __future__ import annotations
import re
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from src.connectors.cryptet_scraper import CryptetScraper

logger = logging.getLogger(__name__)

class CryptetLinkHandler:
    """Handle Cryptet links from Telegram messages."""
    
    def __init__(self, scraper: Optional[CryptetScraper] = None):
        self.scraper = scraper or CryptetScraper()
        
        # Cryptet URL patterns
        self.cryptet_patterns = [
            r'https?://(?:www\.)?cryptet\.com/[^\s]+',
            r'cryptet\.com/[^\s]+',
            r'https?://cryptet\.com/[^\s]+',
            r'www\.cryptet\.com/[^\s]+'
        ]
    
    def is_cryptet_link(self, message_text: str) -> bool:
        """Check if message contains a Cryptet link or crypto symbol."""
        if not message_text:
            return False
            
        # Check for direct Cryptet URLs
        for pattern in self.cryptet_patterns:
            if re.search(pattern, message_text, re.IGNORECASE):
                logger.debug(f"Found Cryptet URL in message: {message_text[:100]}...")
                return True
        
        # Check for crypto trading pairs (e.g., BTC/USDT, ETHUSDT)
        if self.is_crypto_symbol(message_text):
            logger.debug(f"Found crypto symbol in message: {message_text[:100]}...")
            return True
                
        return False
    
    def extract_cryptet_url(self, message_text: str, message_entities: list = None) -> Optional[str]:
        """Extract Cryptet URL from message text or entities."""
        if not message_text:
            return None
        
        # First try to extract from Telegram message entities (most reliable)
        if message_entities:
            for entity in message_entities:
                if hasattr(entity, 'url') and entity.url:
                    url = entity.url
                    if 'cryptet.com' in url.lower():
                        logger.info(f"Extracted Cryptet URL from entities: {url}")
                        return url
        
        # Then try to find direct URLs in text
        for pattern in self.cryptet_patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match:
                url = match.group(0)
                
                # Ensure URL has proper protocol
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                # Clean up URL (remove trailing punctuation)
                url = re.sub(r'[.,;!?]+$', '', url)
                
                logger.info(f"Extracted Cryptet URL from text: {url}")
                return url
        
        # If no direct URL found, try to generate from crypto symbol
        if self.is_crypto_symbol(message_text):
            generated_url = self.symbol_to_cryptet_url(message_text)
            if generated_url:
                logger.info(f"Generated Cryptet URL from symbol: {generated_url}")
                return generated_url
                
        return None
    
    def validate_cryptet_url(self, url: str) -> bool:
        """Validate if URL is a proper Cryptet URL."""
        try:
            parsed = urlparse(url)
            
            # Check domain
            if parsed.netloc.lower() not in ['cryptet.com', 'www.cryptet.com']:
                return False
            
            # Check if it has a path (not just the domain)
            if not parsed.path or parsed.path == '/':
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate URL {url}: {e}")
            return False
    
    async def process_cryptet_link(self, message_text: str, message_entities: list = None) -> Optional[Dict[str, Any]]:
        """Process Cryptet link and extract signal data."""
        try:
            # Extract URL (from entities or text)
            url = self.extract_cryptet_url(message_text, message_entities)
            if not url:
                logger.warning("No Cryptet URL found in message")
                return None
            
            # Validate URL
            if not self.validate_cryptet_url(url):
                logger.warning(f"Invalid Cryptet URL: {url}")
                return None
            
            # Scrape signal data
            signal_data = await self.scraper.scrape_signal(url)
            
            if signal_data:
                # Add 50x leverage (if not already set)
                if 'leverage' not in signal_data:
                    signal_data['leverage'] = 50
                
                # Add metadata
                signal_data['source'] = 'cryptet'
                signal_data['original_message'] = message_text
                signal_data['url'] = url
                
                logger.info(f"Successfully processed Cryptet link: {signal_data.get('symbol', 'unknown')}")
                return signal_data
            else:
                logger.warning(f"Failed to extract signal data from {url}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to process Cryptet link: {e}")
            return None
    
    async def check_signal_status(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check the status of a signal on Cryptet."""
        try:
            url = signal_data.get('url')
            if not url:
                logger.warning("No URL found in signal data")
                return {'updated': False}
            
            return await self.scraper.check_pnl_status(url)
            
        except Exception as e:
            logger.error(f"Failed to check signal status: {e}")
            return {'updated': False}
    
    def extract_links_from_message(self, message_text: str) -> list[str]:
        """Extract all Cryptet links from a message."""
        if not message_text:
            return []
            
        urls = []
        for pattern in self.cryptet_patterns:
            matches = re.finditer(pattern, message_text, re.IGNORECASE)
            for match in matches:
                url = match.group(0)
                
                # Ensure URL has proper protocol
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                # Clean up URL
                url = re.sub(r'[.,;!?]+$', '', url)
                
                if self.validate_cryptet_url(url) and url not in urls:
                    urls.append(url)
        
        return urls
    
    def is_crypto_symbol(self, message_text: str) -> bool:
        """Check if message contains a crypto trading symbol."""
        if not message_text:
            return False
        
        # Common crypto symbol patterns
        crypto_patterns = [
            r'^[A-Z0-9]{2,10}[/]?USDT?$',  # BTC/USDT, BTCUSDT, API3/USDT etc.
            r'^[A-Z0-9]{2,10}[/]USDT?$',   # BTC/USDT, ETH/USDT, API3/USDT
            r'^[A-Z0-9]{2,10}USDT?$',      # BTCUSDT, ETHUSDT, API3USDT
        ]
        
        text = message_text.strip().upper()
        
        for pattern in crypto_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def symbol_to_cryptet_url(self, symbol_text: str) -> Optional[str]:
        """Convert crypto symbol to probable Cryptet URL."""
        try:
            if not symbol_text:
                return None
            
            # Clean the symbol
            symbol = symbol_text.strip().upper()
            
            # Normalize symbol format (remove / and convert to lowercase)
            if '/' in symbol:
                base_symbol = symbol.split('/')[0].lower()
            else:
                # Remove USDT suffix if present
                base_symbol = symbol.replace('USDT', '').replace('USDT', '').lower()
            
            # Generate current date-based URL (most recent signals)
            from datetime import datetime
            now = datetime.now()
            
            # Generate multiple URL patterns and return the most likely one
            # Since we don't know the exact timestamp, we'll use a generic approach
            # that the scraper can handle better
            
            # Pattern 1: Most recent signal URL format
            recent_url = f"https://cryptet.com/signals/one/{base_symbol}_usdt/{now.year}/{now.month:02d}/{now.day:02d}"
            
            # Pattern 2: Alternative with different date format
            alt_url = f"https://cryptet.com/signals/{base_symbol}_usdt"
            
            # Log both for debugging
            logger.info(f"Generated primary Cryptet URL for symbol {symbol}: {recent_url}")
            logger.debug(f"Alternative URL: {alt_url}")
            
            # Return the primary URL - the scraper should handle URL variations
            return recent_url
            
        except Exception as e:
            logger.error(f"Failed to generate Cryptet URL for symbol {symbol_text}: {e}")
            return None
    
    async def process_multiple_links(self, message_text: str) -> list[Dict[str, Any]]:
        """Process multiple Cryptet links from a single message."""
        urls = self.extract_links_from_message(message_text)
        
        if not urls:
            return []
        
        signals = []
        for url in urls:
            try:
                signal_data = await self.scraper.scrape_signal(url)
                if signal_data:
                    # Add metadata
                    signal_data['leverage'] = 50
                    signal_data['source'] = 'cryptet'
                    signal_data['original_message'] = message_text
                    signal_data['url'] = url
                    signals.append(signal_data)
                    
            except Exception as e:
                logger.error(f"Failed to process URL {url}: {e}")
                continue
        
        logger.info(f"Processed {len(signals)} signals from {len(urls)} URLs")
        return signals
    
    async def close(self) -> None:
        """Close the scraper."""
        if self.scraper:
            await self.scraper.close()