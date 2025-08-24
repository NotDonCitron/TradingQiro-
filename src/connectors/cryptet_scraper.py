# feat(connector): Cryptet web scraper with browser automation and cookie authentication
from __future__ import annotations
import asyncio
import os
import time
import logging
from typing import Dict, Any, Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re

from src.utils.cookie_parser import CookieParser

logger = logging.getLogger(__name__)

class CryptetScraper:
    """Web scraper for Cryptet signals with cookie-based authentication."""
    
    def __init__(self, cookies_file: str = "cookies.txt", headless: bool = True):
        self.cookies_file = cookies_file
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.cookie_parser = CookieParser(cookies_file)
        self.wait_timeout = 10
        
    async def initialize_browser(self) -> bool:
        """Initialize Chrome browser with cookies."""
        try:
            # Chrome options
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Load cookies
            await self.load_cookies()
            
            logger.info("Browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            return False
    
    async def load_cookies(self) -> None:
        """Load cookies from file and apply to browser."""
        try:
            if not self.driver:
                return
                
            # Navigate to Cryptet first
            self.driver.get("https://cryptet.com")
            await asyncio.sleep(2)
            
            # Get cookies for cryptet.com
            cookies = self.cookie_parser.get_cryptet_cookies()
            
            if not cookies:
                logger.warning("No cookies found for cryptet.com")
                return
            
            # Add cookies to browser
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                    logger.debug(f"Added cookie: {cookie['name']}")
                except Exception as e:
                    logger.warning(f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}")
            
            # Refresh page to apply cookies
            self.driver.refresh()
            await asyncio.sleep(2)
            
            logger.info(f"Loaded {len(cookies)} cookies for cryptet.com")
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
    
    async def scrape_signal(self, cryptet_url: str) -> Optional[Dict[str, Any]]:
        """Scrape signal data from Cryptet URL."""
        try:
            if not self.driver:
                await self.initialize_browser()
            
            logger.info(f"Scraping signal from: {cryptet_url}")
            
            # Try the URL as provided first
            success = await self.try_scrape_url(cryptet_url)
            if success:
                return success
            
            # If URL doesn't work, try to find the most recent signal for the symbol
            if '/signals/one/' in cryptet_url and not cryptet_url.endswith(('0000', '0001', '0002', '0003', '0004', '0005', '0006', '0007', '0008', '0009')):
                logger.info("Trying to find most recent signal for this symbol...")
                recent_signal = await self.find_recent_signal(cryptet_url)
                if recent_signal:
                    return recent_signal
            
            logger.warning("No signal data found on page")
            return None
                
        except Exception as e:
            logger.error(f"Failed to scrape signal: {e}")
            return None
    
    async def try_scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Try to scrape a specific URL with timeout."""
        try:
            # Navigate to signal page
            if not self.driver:
                logger.error("Driver not initialized")
                return None
            
            logger.debug(f"Navigating to: {url}")
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)  # 30 seconds timeout
            
            try:
                self.driver.get(url)
            except Exception as e:
                logger.warning(f"Page load timeout or error for {url}: {e}")
                return None
            
            # Wait for page to load with shorter timeout
            await asyncio.sleep(2)
            
            # Check if page loaded successfully (not 404 or empty)
            try:
                page_title = self.driver.title.lower() if self.driver.title else ""
                if '404' in page_title or 'not found' in page_title or not page_title:
                    logger.warning(f"Page not found or empty: {url}")
                    return None
                
                # Additional check: see if page source is available
                if not self.driver.page_source or len(self.driver.page_source) < 100:
                    logger.warning(f"Page source too small or empty for {url}")
                    return None
                    
            except Exception as e:
                logger.warning(f"Could not check page status for {url}: {e}")
                return None
            
            # Extract signal data with timeout
            try:
                signal_data = await asyncio.wait_for(
                    self.extract_signal_data(),
                    timeout=20.0  # 20 seconds timeout for extraction
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout extracting signal data from {url}")
                return None
            
            if signal_data:
                # Add metadata
                signal_data['leverage'] = 50
                signal_data['source'] = 'cryptet'
                signal_data['url'] = url
                signal_data['timestamp'] = int(time.time())
                
                logger.info(f"Successfully scraped signal: {signal_data.get('symbol', 'unknown')}")
                return signal_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to scrape URL {url}: {e}")
            return None
    
    async def find_recent_signal(self, base_url: str) -> Optional[Dict[str, Any]]:
        """Try to find the most recent signal for a symbol by trying different time patterns."""
        try:
            # Extract symbol and date from URL
            import re
            match = re.search(r'/signals/one/([^/]+)/(\d{4})/(\d{2})/(\d{2})', base_url)
            if not match:
                return None
            
            symbol, year, month, day = match.groups()
            
            # Try different hour patterns for today (most recent signals)
            current_hour = int(time.time() // 3600) % 24
            
            # Try last few hours in reverse order (most recent first)
            for hour_offset in range(0, 24):
                test_hour = (current_hour - hour_offset) % 24
                
                # Try different minute patterns
                for minute in ['00', '15', '30', '45']:  # Common signal times
                    test_url = f"https://cryptet.com/signals/one/{symbol}/{year}/{month}/{day}/{test_hour:02d}{minute}"
                    
                    result = await self.try_scrape_url(test_url)
                    if result:
                        logger.info(f"Found recent signal at: {test_url}")
                        return result
            
            logger.warning(f"No recent signals found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to find recent signal: {e}")
            return None
    
    async def extract_signal_data(self) -> Optional[Dict[str, Any]]:
        """Extract signal data from current page."""
        try:
            # Get page source
            if not self.driver:
                logger.error("Driver not initialized")
                return None
                
            html = self.driver.page_source if self.driver.page_source else ""
            soup = BeautifulSoup(html, 'html.parser')
            
            # Initialize signal data
            signal_data = {}
            
            # Extract symbol
            symbol = await self.extract_symbol(soup)
            if symbol:
                signal_data['symbol'] = symbol
            
            # Extract direction (LONG/SHORT)
            direction = await self.extract_direction(soup)
            if direction:
                signal_data['direction'] = direction
            
            # Extract entry price
            entry_price = await self.extract_entry_price(soup)
            if entry_price:
                signal_data['entry_price'] = entry_price
            
            # Extract stop loss
            stop_loss = await self.extract_stop_loss(soup)
            if stop_loss:
                signal_data['stop_loss'] = stop_loss
            
            # Extract take profits
            take_profits = await self.extract_take_profits(soup)
            if take_profits:
                signal_data['take_profits'] = take_profits
            
            # Validate required fields
            required_fields = ['symbol', 'direction', 'entry_price']
            if all(field in signal_data for field in required_fields):
                return signal_data
            else:
                missing = [field for field in required_fields if field not in signal_data]
                logger.warning(f"Missing required fields: {missing}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to extract signal data: {e}")
            return None
    
    async def extract_symbol(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract trading symbol from page."""
        try:
            # Common selectors for symbol
            selectors = [
                '.symbol', '.pair', '.trading-pair', 
                '[class*="symbol"]', '[class*="pair"]',
                'h1', 'h2', '.title'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    # Look for crypto pair pattern (e.g., BTC/USDT, BTCUSDT)
                    match = re.search(r'([A-Z]{2,10})[/]?USDT?', text.upper())
                    if match:
                        symbol = match.group(1) + 'USDT'
                        logger.debug(f"Found symbol: {symbol}")
                        return symbol
            
            # Fallback: search in page text
            page_text = soup.get_text()
            match = re.search(r'([A-Z]{2,10})[/]?USDT?', page_text.upper())
            if match:
                symbol = match.group(1) + 'USDT'
                logger.debug(f"Found symbol in text: {symbol}")
                return symbol
                
            logger.warning("Symbol not found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract symbol: {e}")
            return None
    
    async def extract_direction(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract trade direction (LONG/SHORT) from page."""
        try:
            page_text = soup.get_text().upper()
            
            # Look for direction indicators (English and German)
            if any(word in page_text for word in ['LONG', 'BUY', 'KAUFEN', '🟢']):
                return 'LONG'
            elif any(word in page_text for word in ['SHORT', 'SELL', 'VERKAUFEN', '🔴']):
                return 'SHORT'
            
            # Check for specific elements (English and German)
            direction_elements = soup.find_all(text=re.compile(r'(LONG|SHORT|BUY|SELL|KAUFEN|VERKAUFEN)', re.I))
            if direction_elements:
                direction_text = str(direction_elements[0]).upper()
                if any(word in direction_text for word in ['LONG', 'BUY', 'KAUFEN']):
                    return 'LONG'
                elif any(word in direction_text for word in ['SHORT', 'SELL', 'VERKAUFEN']):
                    return 'SHORT'
            
            logger.warning("Direction not found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract direction: {e}")
            return None
    
    async def extract_entry_price(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract entry price from page."""
        try:
            # Look for price patterns (English and German)
            price_patterns = [
                r'entry[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'price[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'buy[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'kaufen[:\s]*bei[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'kaufen[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'einstieg[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'\$([0-9,]+\.?[0-9]*)'
            ]
            
            page_text = soup.get_text()
            
            for pattern in price_patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    price = match.group(1).replace(',', '')
                    try:
                        float(price)
                        logger.debug(f"Found entry price: {price}")
                        return price
                    except ValueError:
                        continue
            
            logger.warning("Entry price not found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract entry price: {e}")
            return None
    
    async def extract_stop_loss(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract stop loss from page."""
        try:
            # Look for stop loss patterns (English and German)
            sl_patterns = [
                r'stop[:\s]*loss[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'sl[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'stop[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'stopp[:\s]*loss[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'stop[:\s]*verlust[:\s]*\$?([0-9,]+\.?[0-9]*)'
            ]
            
            page_text = soup.get_text()
            
            for pattern in sl_patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    price = match.group(1).replace(',', '')
                    try:
                        float(price)
                        logger.debug(f"Found stop loss: {price}")
                        return price
                    except ValueError:
                        continue
            
            logger.warning("Stop loss not found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract stop loss: {e}")
            return None
    
    async def extract_take_profits(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract take profit levels from page - Cryptet usually has only ONE take profit."""
        try:
            # Cryptet-spezifische Take Profit Patterns (meist nur EINER)
            tp_patterns = [
                # Cryptet spezifische Muster
                r'Take\s+Profit\*?[:\s]*([0-9,]+\.?[0-9]*)',
                r'take\s+profit\*?[:\s]*([0-9,]+\.?[0-9]*)',
                # Standard patterns
                r'take[:\s]*profit[*\s]*\d*[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'tp[:\s]*\d*[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'target[:\s]*\d*[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'gewinn[:\s]*mitnahme[:\s]*\d*[:\s]*\$?([0-9,]+\.?[0-9]*)',
                r'ziel[:\s]*\d*[:\s]*\$?([0-9,]+\.?[0-9]*)',
            ]
            
            page_text = soup.get_text()
            take_profits = []
            
            # Get entry price and stop loss to exclude them
            entry_price = await self.extract_entry_price(soup)
            stop_loss = await self.extract_stop_loss(soup)
            excluded_values = []
            if entry_price:
                excluded_values.append(entry_price.replace(',', ''))
            if stop_loss:
                excluded_values.append(stop_loss.replace(',', ''))
            
            logger.debug(f"Excluding entry price and stop loss: {excluded_values}")
            
            # Standard pattern matching für Cryptet
            for pattern in tp_patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    price = match.group(1).replace(',', '')
                    try:
                        price_float = float(price)
                        # Cryptet: Nur sinnvolle Preise und nicht Entry/Stop Loss
                        if 0.001 <= price_float <= 1000000 and price not in excluded_values:
                            if price not in take_profits:
                                take_profits.append(price)
                                logger.debug(f"Found take profit: {price} (pattern: {pattern})")
                                # Für Cryptet: Stoppe nach dem ersten gefundenen TP
                                break
                    except ValueError:
                        continue
                
                # Wenn wir bereits einen TP gefunden haben, stoppe hier
                if take_profits:
                    break
            
            # Spezielle Behandlung für Cryptet-Format: "Take Profit*" gefolgt von Zahl in nächster Zeile
            if not take_profits:
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if 'take profit' in line.lower() and '*' in line:
                        # Schaue in den nächsten Zeilen nach Zahlen
                        for j in range(i+1, min(i+4, len(lines))):
                            next_line = lines[j].strip()
                            # Prüfe ob diese Zeile eine Preis-Zahl enthält
                            if re.match(r'^[0-9,]+\.?[0-9]*$', next_line):
                                clean_number = next_line.replace(',', '')
                                try:
                                    number_float = float(clean_number)
                                    if 0.001 <= number_float <= 1000000 and clean_number not in excluded_values:
                                        if clean_number not in take_profits:
                                            take_profits.append(clean_number)
                                            logger.debug(f"Found take profit from Cryptet format: {clean_number}")
                                            break  # Nur einen TP für Cryptet
                                except ValueError:
                                    continue
                        
                        # Wenn wir einen TP gefunden haben, stoppe die Suche
                        if take_profits:
                            break
            
            # Zusätzliche Suche in Zeilen mit "profit" (aber Entry/Stop Loss ausschließen)
            if not take_profits:
                lines = page_text.split('\n')  # Re-initialize lines for this section
                for line in lines:
                    lower_line = line.lower()
                    if ('profit' in lower_line and 
                        'entry' not in lower_line and 
                        'stop' not in lower_line and
                        'loss' not in lower_line and
                        'kaufen' not in lower_line):
                        # Extrahiere Zahlen aus dieser Zeile
                        number_matches = re.findall(r'\b([0-9,]{2,}\.?[0-9]*)\b', line)
                        for number in number_matches:
                            clean_number = number.replace(',', '')
                            try:
                                number_float = float(clean_number)
                                if 0.001 <= number_float <= 1000000 and clean_number not in excluded_values:
                                    if clean_number not in take_profits:
                                        take_profits.append(clean_number)
                                        logger.debug(f"Found take profit from profit line: {clean_number}")
                                        break  # Nur einen TP für Cryptet
                            except ValueError:
                                continue
                        
                        # Wenn wir einen TP gefunden haben, stoppe
                        if take_profits:
                            break
            
            if take_profits:
                # Für Cryptet: Normalerweise nur EINER, aber sicherheitshalber limitieren
                take_profits = take_profits[:1]  # Nur den ersten TP verwenden
                logger.info(f"Extracted {len(take_profits)} take profit level for Cryptet: {take_profits}")
                return take_profits
            else:
                logger.warning("No take profits found (normal for some Cryptet signals)")
                return None
            
        except Exception as e:
            logger.error(f"Failed to extract take profits: {e}")
            return None
    
    async def check_pnl_status(self, cryptet_url: str) -> Dict[str, Any]:
        """Check if P&L has been updated on Cryptet page."""
        try:
            if not self.driver:
                await self.initialize_browser()
            
            if not self.driver:
                logger.error("Failed to initialize driver")
                return {'updated': False}

            # Navigate to signal page
            self.driver.get(cryptet_url)
            await asyncio.sleep(3)
            
            # Get page source
            html = self.driver.page_source if self.driver.page_source else ""
            soup = BeautifulSoup(html, 'html.parser')
            page_text = soup.get_text()
            
            # Look for P&L indicators
            pnl_patterns = [
                r'profit[:\s]*([+-]?\d+\.?\d*)%',
                r'loss[:\s]*([+-]?\d+\.?\d*)%',
                r'pnl[:\s]*([+-]?\d+\.?\d*)%',
                r'([+-]\d+\.?\d*)%'
            ]
            
            for pattern in pnl_patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    percentage = match.group(1)
                    try:
                        pnl_value = float(percentage)
                        result = 'profit' if pnl_value > 0 else 'loss'
                        
                        logger.info(f"Found P&L update: {percentage}% ({result})")
                        
                        return {
                            'updated': True,
                            'result': result,
                            'percentage': percentage
                        }
                    except ValueError:
                        continue
            
            # Check for closed/finished indicators
            closed_keywords = ['closed', 'finished', 'completed', 'ended']
            for keyword in closed_keywords:
                if keyword.lower() in page_text.lower():
                    logger.info("Signal appears to be closed")
                    return {
                        'updated': True,
                        'result': 'closed',
                        'percentage': '0'
                    }
            
            return {'updated': False}
            
        except Exception as e:
            logger.error(f"Failed to check P&L status: {e}")
            return {'updated': False}
    
    async def close(self) -> None:
        """Close the browser driver."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Failed to close browser: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass