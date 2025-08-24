# feat(utils): Cookie parser for Netscape format to Selenium format conversion
from __future__ import annotations
import os
import time
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CookieParser:
    """Convert Netscape cookie format to Selenium-compatible format."""
    
    def __init__(self, cookies_file: str = "cookies.txt"):
        self.cookies_file = cookies_file
        
    def parse_netscape_cookies(self) -> List[Dict[str, Any]]:
        """Parse Netscape cookie file and convert to Selenium format."""
        cookies = []
        
        if not os.path.exists(self.cookies_file):
            logger.warning(f"Cookie file {self.cookies_file} not found")
            return cookies
            
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                        
                    # Parse cookie line
                    parts = line.split('\t')
                    if len(parts) >= 6:
                        domain = parts[0]
                        flag = parts[1] == 'TRUE'
                        path = parts[2]
                        secure = parts[3] == 'TRUE'
                        expiry = parts[4]
                        name = parts[5]
                        value = parts[6] if len(parts) > 6 else ""
                        
                        # Convert to Selenium format
                        cookie = {
                            'name': name,
                            'value': value,
                            'domain': domain,
                            'path': path,
                            'secure': secure
                        }
                        
                        # Add expiry if it's not 0 or empty
                        if expiry and expiry != '0':
                            try:
                                cookie['expiry'] = int(expiry)
                            except ValueError:
                                logger.warning(f"Invalid expiry time for cookie {name}: {expiry}")
                        
                        cookies.append(cookie)
                        logger.debug(f"Parsed cookie: {name} for domain {domain}")
                        
        except Exception as e:
            logger.error(f"Error parsing cookie file: {e}")
            
        logger.info(f"Parsed {len(cookies)} cookies from {self.cookies_file}")
        return cookies
    
    def filter_cookies_for_domain(self, cookies: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
        """Filter cookies for a specific domain."""
        filtered = []
        
        for cookie in cookies:
            cookie_domain = cookie.get('domain', '')
            
            # Check if cookie domain matches
            if (cookie_domain == domain or 
                cookie_domain.startswith('.') and domain.endswith(cookie_domain[1:]) or
                domain == cookie_domain.lstrip('.')):
                filtered.append(cookie)
                
        logger.info(f"Filtered {len(filtered)} cookies for domain {domain}")
        return filtered
    
    def get_cryptet_cookies(self) -> List[Dict[str, Any]]:
        """Get cookies specifically for cryptet.com domain."""
        all_cookies = self.parse_netscape_cookies()
        return self.filter_cookies_for_domain(all_cookies, "cryptet.com")