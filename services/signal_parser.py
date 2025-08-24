#!/usr/bin/env python3
"""
Signal Parser Service
Processed Telegram-Nachrichten aus Redis Queue und erkennt Signale
"""

import asyncio
import json
import os
import re
import redis.asyncio as redis
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class SignalParserService:
    """Service zum Parsen von Telegram-Signalen."""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://trading-bot-redis:6379/0")
        self.redis_client = None
        
        # Signal-Erkennungspattern (übernommen aus bestehender Implementierung)
        self.signal_pattern = re.compile(
            r'🟢\s*(Long|Short)\s*\n'
            r'Name:\s*([A-Z0-9]+/[A-Z]+)\s*\n'
            r'Margin\s+mode:\s*Cross\s*\(([0-9.]+)X\)\s*\n'
            r'.*?'
            r'Entry\s+price\(USDT\):\s*\n'
            r'([0-9.]+)\s*\n'
            r'.*?'
            r'Targets\(USDT\):\s*\n'
            r'((?:\d+\)\s*[0-9.]+(?:\s*\n|\s+))+)',
            re.DOTALL | re.IGNORECASE
        )
    
    async def start(self):
        """Startet den Signal Parser Service."""
        print("🔍 Starting Signal Parser Service...")
        
        # Redis Verbindung
        self.redis_client = redis.from_url(self.redis_url)
        print("✅ Connected to Redis")
        
        # Hauptverarbeitungsloop
        while True:
            try:
                # Message aus Queue holen (blocking)
                message_data = await self.redis_client.brpop("telegram_messages", timeout=1)
                
                if message_data:
                    # Parse JSON
                    message_json = json.loads(message_data[1])
                    await self.process_message(message_json)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Parser error: {e}")
                await asyncio.sleep(1)
    
    async def process_message(self, message_data: Dict[str, Any]):
        """Verarbeitet eine Nachricht und prüft auf Signale."""
        try:
            text = message_data.get("text", "")
            chat_id = message_data.get("chat_id")
            
            print(f"🔍 Processing message from {chat_id}: {text[:50]}...")
            
            # Signal-Prüfung
            if self.is_signal(text):
                # Signal erkannt - parse Details
                if self.is_trading_update(text):
                    # Trading Update - direkt weiterleiten
                    signal_data = {
                        "type": "trading_update",
                        "original_text": text,
                        "formatted_text": text,
                        "source_chat_id": chat_id,
                        "metadata": message_data
                    }
                else:
                    # Vollständiges Signal - parsen
                    parsed_signal = self.parse_signal(text)
                    if parsed_signal:
                        formatted_text = self.format_signal(parsed_signal)
                        signal_data = {
                            "type": "full_signal",
                            "original_text": text,
                            "formatted_text": formatted_text,
                            "parsed_data": parsed_signal,
                            "source_chat_id": chat_id,
                            "metadata": message_data
                        }
                    else:
                        return  # Parsing fehlgeschlagen
                
                # Signal zur Forwarder Queue hinzufügen
                await self.redis_client.lpush(
                    "parsed_signals",
                    json.dumps(signal_data)
                )
                
                print(f"✅ Signal parsed and queued: {signal_data['type']}")
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def is_signal(self, message: str) -> bool:
        """Prüft ob eine Nachricht ein Signal enthält."""
        # Vollständige Trading-Signale
        full_signal_indicators = [
            "🟢 Long" in message or "🟢 Short" in message,
            "Name:" in message,
            "Margin mode:" in message,
            "Entry price(USDT):" in message,
            "Targets(USDT):" in message
        ]
        
        # Trading-Updates
        trading_update_indicators = [
            ("💸" in message and "/USDT" in message),
            ("Target #" in message and "Done" in message),
            ("Current profit:" in message and "%" in message),
            ("/USDT" in message and any(kw in message.upper() for kw in ["LONG", "SHORT", "BUY", "SELL"])),
            bool(re.search(r'[A-Z0-9]{2,8}/USDT', message))
        ]
        
        return all(full_signal_indicators) or any(trading_update_indicators)
    
    def is_trading_update(self, message: str) -> bool:
        """Prüft ob es sich um ein Trading-Update handelt."""
        return ("💸" in message and "/USDT" in message) or ("Target #" in message and "Done" in message)
    
    def parse_signal(self, message: str) -> Optional[Dict[str, Any]]:
        """Parst ein Signal aus der Nachricht."""
        lines = message.split('\n')
        
        direction = None
        symbol = None
        leverage = None
        entry_price = None
        targets = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if '🟢 Long' in line:
                direction = 'LONG'
            elif '🟢 Short' in line or '🔴 Short' in line:
                direction = 'SHORT'
            elif line.startswith('Name:'):
                symbol_match = re.search(r'Name:\s*([A-Z0-9]+/[A-Z]+)', line)
                if symbol_match:
                    symbol = symbol_match.group(1)
            elif 'Margin mode:' in line and 'Cross' in line:
                leverage_match = re.search(r'\(([0-9.]+)X\)', line)
                if leverage_match:
                    leverage = float(leverage_match.group(1))
            elif 'Entry price(USDT):' in line:
                if i + 1 < len(lines):
                    price_line = lines[i + 1].strip()
                    try:
                        entry_price = float(price_line)
                    except ValueError:
                        pass
            elif 'Targets(USDT):' in line:
                j = i + 1
                while j < len(lines):
                    target_line = lines[j].strip()
                    target_match = re.search(r'\d+\)\s*([0-9.]+)', target_line)
                    if target_match:
                        targets.append(float(target_match.group(1)))
                        j += 1
                    else:
                        break
            
            i += 1
        
        if direction and symbol and entry_price:
            return {
                "direction": direction,
                "symbol": symbol,
                "leverage": leverage or 1.0,
                "entry_price": entry_price,
                "targets": targets
            }
        
        return None
    
    def format_signal(self, signal_data: Dict[str, Any]) -> str:
        """Formatiert ein geparste Signal für die Weiterleitung."""
        direction_emoji = "🟢" if signal_data["direction"] == "LONG" else "🔴"
        
        formatted = f"""{direction_emoji} {signal_data["direction"]}
Name: {signal_data["symbol"]}
Margin mode: Cross ({signal_data["leverage"]:.1f}X)

↪️ Entry price(USDT):
{signal_data["entry_price"]}

Targets(USDT):"""
        
        for i, target in enumerate(signal_data["targets"], 1):
            formatted += f"\n{i}) {target}"
        
        return formatted
    
    async def stop(self):
        """Stoppt den Service."""
        if self.redis_client:
            await self.redis_client.close()

async def main():
    """Hauptfunktion."""
    service = SignalParserService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Signal Parser Service...")
        await service.stop()
    except Exception as e:
        print(f"❌ Service error: {e}")
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())