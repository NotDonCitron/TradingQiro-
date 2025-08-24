#!/usr/bin/env python3
"""
Signal Forwarder Service
Sendet geparste Signale über Telegram Bot API weiter
"""

import asyncio
import json
import os
import aiohttp
import redis.asyncio as redis
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class SignalForwarderService:
    """Service zum Weiterleiten von Signalen über Telegram Bot API."""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.target_group_id = os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382")
        self.redis_url = os.getenv("REDIS_URL", "redis://trading-bot-redis:6379/0")
        
        self.redis_client = None
        self.session = None
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be set")
    
    async def start(self):
        """Startet den Signal Forwarder Service."""
        print("📤 Starting Signal Forwarder Service...")
        
        # Redis Verbindung
        self.redis_client = redis.from_url(self.redis_url)
        print("✅ Connected to Redis")
        
        # HTTP Session für Telegram Bot API
        self.session = aiohttp.ClientSession()
        print("✅ HTTP Session initialized")
        
        # Bot-Info abrufen
        await self.test_bot_connection()
        
        # Hauptverarbeitungsloop
        while True:
            try:
                # Signal aus Queue holen (blocking)
                signal_data = await self.redis_client.brpop("parsed_signals", timeout=1)
                
                if signal_data:
                    # Parse JSON
                    signal_json = json.loads(signal_data[1])
                    await self.forward_signal(signal_json)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Forwarder error: {e}")
                await asyncio.sleep(1)
    
    async def test_bot_connection(self):
        """Testet die Verbindung zum Telegram Bot."""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    bot_info = data["result"]
                    print(f"✅ Bot connected: @{bot_info['username']} ({bot_info['first_name']})")
                else:
                    print(f"❌ Bot connection failed: {response.status}")
        except Exception as e:
            print(f"❌ Bot test error: {e}")
    
    async def forward_signal(self, signal_data: Dict[str, Any]):
        """Leitet ein geparste Signal weiter."""
        try:
            text = signal_data.get("formatted_text", "")
            signal_type = signal_data.get("type", "unknown")
            source_chat_id = signal_data.get("source_chat_id")
            
            print(f"📤 Forwarding {signal_type} from {source_chat_id}...")
            
            # Signal über Bot API senden
            success = await self.send_telegram_message(self.target_group_id, text)
            
            if success:
                print(f"✅ Signal forwarded successfully!")
                
                # Erfolg in Redis loggen (optional)
                log_data = {
                    "action": "signal_forwarded",
                    "type": signal_type,
                    "source_chat_id": source_chat_id,
                    "target_chat_id": self.target_group_id,
                    "timestamp": signal_data.get("metadata", {}).get("timestamp"),
                    "success": True
                }
                await self.redis_client.lpush("forwarding_logs", json.dumps(log_data))
            else:
                print(f"❌ Signal forwarding failed!")
                
        except Exception as e:
            print(f"❌ Error forwarding signal: {e}")
    
    async def send_telegram_message(self, chat_id: str, text: str) -> bool:
        """Sendet eine Nachricht über Telegram Bot API."""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Telegram API error ({response.status}): {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Send message error: {e}")
            return False
    
    async def stop(self):
        """Stoppt den Service."""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.close()

async def main():
    """Hauptfunktion."""
    service = SignalForwarderService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Signal Forwarder Service...")
        await service.stop()
    except Exception as e:
        print(f"❌ Service error: {e}")
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())