# feat(core): Cryptet signal parser and Telegram formatter with 50x leverage
from __future__ import annotations
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class CryptetSignalFormatter:
    """Format Cryptet signals for Telegram."""
    
    def __init__(self):
        self.default_leverage = 50
    
    def format_for_telegram(self, signal_data: Dict[str, Any]) -> str:
        """Format signal data for Telegram message."""
        try:
            # Get direction emoji
            direction = signal_data.get('direction', '').upper()
            direction_emoji = self.get_direction_emoji(direction)
            
            # Get basic signal info
            symbol = signal_data.get('symbol', 'UNKNOWN')
            entry_price = signal_data.get('entry_price', 'N/A')
            stop_loss = signal_data.get('stop_loss', 'N/A')
            leverage = signal_data.get('leverage', self.default_leverage)
            
            # Start building the message
            formatted_signal = f"""
🤖 **CRYPTET SIGNAL** 🤖

{direction_emoji} **{direction}** {symbol}
💰 **Entry:** {entry_price}
"""
            
            # Add take profits if available
            take_profits = signal_data.get('take_profits', [])
            if take_profits:
                formatted_signal += "🎯 **Take Profits:**\n"
                for i, tp in enumerate(take_profits, 1):
                    formatted_signal += f"   {i}) {tp}\n"
            else:
                formatted_signal += "🎯 **Take Profits:** Not specified\n"
            
            # Add stop loss
            if stop_loss != 'N/A':
                formatted_signal += f"🛑 **Stop Loss:** {stop_loss}\n"
            else:
                formatted_signal += "🛑 **Stop Loss:** Not specified\n"
            
            # Add leverage with Cross margin
            formatted_signal += f"⚡ **Leverage:** Cross {leverage}x\n\n"
            
            # Add metadata
            formatted_signal += "📊 **Source:** Cryptet.com\n"
            formatted_signal += "🔄 **Auto-forwarded with 50x leverage**\n"
            formatted_signal += "⏰ **Will close automatically when P&L updates**\n\n"
            
            # Add timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_signal += f"🕐 **Time:** {timestamp}"
            
            return formatted_signal
            
        except Exception as e:
            logger.error(f"Failed to format signal: {e}")
            return self.format_error_message(signal_data)
    
    def get_direction_emoji(self, direction: str) -> str:
        """Get emoji for trade direction."""
        if direction.upper() == 'LONG':
            return "🟢"
        elif direction.upper() == 'SHORT':
            return "🔴"
        else:
            return "⚪"
    
    def format_error_message(self, signal_data: Dict[str, Any]) -> str:
        """Format error message when signal formatting fails."""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        url = signal_data.get('url', 'N/A')
        
        return f"""
❌ **SIGNAL PARSING ERROR**

📊 **Symbol:** {symbol}
🔗 **URL:** {url}
⚠️ **Error:** Could not parse signal data properly

Please check the signal manually.
"""
    
    def format_close_message(self, signal_data: Dict[str, Any], pnl_status: Dict[str, Any]) -> str:
        """Format signal close message."""
        try:
            symbol = signal_data.get('symbol', 'UNKNOWN')
            direction = signal_data.get('direction', '').upper()
            result = pnl_status.get('result', 'unknown')
            percentage = pnl_status.get('percentage', '0')
            
            # Get result emoji
            if result == 'profit':
                result_emoji = "✅"
                result_text = "PROFIT"
            elif result == 'loss':
                result_emoji = "❌"
                result_text = "LOSS"
            else:
                result_emoji = "🔄"
                result_text = "CLOSED"
            
            close_message = f"""
{result_emoji} **SIGNAL CLOSED** {result_emoji}

📊 **Symbol:** {symbol}
{self.get_direction_emoji(direction)} **Direction:** {direction}
📈 **Result:** {result_text}
💹 **P&L:** {percentage}%

🤖 **Auto-closed by Cryptet monitor**
📊 **Source:** Cryptet.com

🕐 **Closed at:** {datetime.now().strftime("%H:%M:%S")}
"""
            
            return close_message
            
        except Exception as e:
            logger.error(f"Failed to format close message: {e}")
            return "❌ **Signal closed** (formatting error)"
    
    def validate_signal_data(self, signal_data: Dict[str, Any]) -> bool:
        """Validate that signal data has required fields."""
        required_fields = ['symbol', 'direction', 'entry_price']
        
        for field in required_fields:
            if field not in signal_data or not signal_data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        return True
    
    def add_leverage_to_signal(self, signal_data: Dict[str, Any], leverage: int = 50) -> Dict[str, Any]:
        """Add or update leverage in signal data."""
        signal_data['leverage'] = leverage
        return signal_data
    
    def parse_raw_signal(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Parse raw signal text (fallback method)."""
        try:
            # This is a fallback method in case web scraping fails
            import re
            
            signal_data = {}
            
            # Extract symbol
            symbol_match = re.search(r'([A-Z]{2,10})[/]?USDT?', raw_text.upper())
            if symbol_match:
                signal_data['symbol'] = symbol_match.group(1) + 'USDT'
            
            # Extract direction
            if re.search(r'\b(LONG|BUY)\b', raw_text, re.IGNORECASE):
                signal_data['direction'] = 'LONG'
            elif re.search(r'\b(SHORT|SELL)\b', raw_text, re.IGNORECASE):
                signal_data['direction'] = 'SHORT'
            
            # Extract entry price
            entry_match = re.search(r'entry[:\s]*\$?([0-9,]+\.?[0-9]*)', raw_text, re.IGNORECASE)
            if entry_match:
                signal_data['entry_price'] = entry_match.group(1).replace(',', '')
            
            # Extract stop loss
            sl_match = re.search(r'stop[:\s]*loss[:\s]*\$?([0-9,]+\.?[0-9]*)', raw_text, re.IGNORECASE)
            if sl_match:
                signal_data['stop_loss'] = sl_match.group(1).replace(',', '')
            
            # Extract take profits
            tp_matches = re.finditer(r'(?:tp|target)[:\s]*\d*[:\s]*\$?([0-9,]+\.?[0-9]*)', raw_text, re.IGNORECASE)
            take_profits = []
            for match in tp_matches:
                price = match.group(1).replace(',', '')
                if price not in take_profits:
                    take_profits.append(price)
            
            if take_profits:
                signal_data['take_profits'] = take_profits
            
            # Add default leverage
            signal_data['leverage'] = 50
            signal_data['source'] = 'cryptet_manual_parse'
            
            return signal_data if self.validate_signal_data(signal_data) else None
            
        except Exception as e:
            logger.error(f"Failed to parse raw signal: {e}")
            return None


class CryptetSignalProcessor:
    """Process and format Cryptet signals."""
    
    def __init__(self):
        self.formatter = CryptetSignalFormatter()
    
    def process_signal(self, signal_data: Dict[str, Any]) -> Optional[str]:
        """Process signal data and return formatted Telegram message."""
        try:
            # Validate signal data
            if not self.formatter.validate_signal_data(signal_data):
                logger.error("Invalid signal data")
                return None
            
            # Ensure 50x leverage
            signal_data = self.formatter.add_leverage_to_signal(signal_data, 50)
            
            # Format for Telegram
            formatted_message = self.formatter.format_for_telegram(signal_data)
            
            logger.info(f"Successfully processed signal: {signal_data.get('symbol', 'unknown')}")
            return formatted_message
            
        except Exception as e:
            logger.error(f"Failed to process signal: {e}")
            return None
    
    def process_symbol_only(self, symbol_text: str, source_url: str = None) -> Optional[str]:
        """Process crypto symbol when only symbol is available (fallback method)."""
        try:
            logger.info(f"Processing symbol-only signal: {symbol_text}")
            
            # Create minimal signal data
            signal_data = {
                'symbol': symbol_text.upper().replace('/', ''),
                'direction': 'UNKNOWN',  # We don't know the direction
                'entry_price': 'Market Price',
                'leverage': 50,
                'source': 'cryptet_symbol',
                'url': source_url or 'N/A',
                'timestamp': int(time.time())
            }
            
            # Use a special formatter for symbol-only signals
            formatted_signal = f"""
🤖 **CRYPTET SYMBOL DETECTED** 🤖

📊 **Symbol:** {signal_data['symbol']}
⚠️ **Signal Details:** Scraping in progress...

⚡ **Action Required:**
1. 🌐 Opening Cryptet page
2. 📊 Extracting signal details
3. 📤 Sending formatted signal

🔗 **Source URL:** {signal_data['url']}
⚡ **Leverage:** Cross 50x (auto-applied)
📊 **Source:** Cryptet.com

⏰ **Time:** {datetime.now().strftime("%H:%M:%S")}

💡 **Note:** Complete signal details will follow automatically!"""
            
            logger.info(f"Generated symbol-only signal for: {symbol_text}")
            return formatted_signal
            
        except Exception as e:
            logger.error(f"Failed to process symbol-only signal: {e}")
            return None
    
    def process_signal_close(self, signal_data: Dict[str, Any], pnl_status: Dict[str, Any]) -> str:
        """Process signal close and return formatted message."""
        try:
            return self.formatter.format_close_message(signal_data, pnl_status)
        except Exception as e:
            logger.error(f"Failed to process signal close: {e}")
            return "❌ **Signal closed** (processing error)"