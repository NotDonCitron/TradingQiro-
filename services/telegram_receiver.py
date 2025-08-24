#!/usr/bin/env python3
"""
Telegram Receiver Service
Empfängt Telegram-Nachrichten und sendet sie an Redis Queue
"""

import asyncio
import json
import os
import redis.asyncio as redis
from typing import Dict, Any
from telethon import TelegramClient, events
from dotenv import load_dotenv

load_dotenv()

class TelegramReceiverService:
    """Service zum Empfangen von Telegram-Nachrichten."""
    
    def __init__(self):
        self.api_id = int(os.getenv("TELEGRAM_API_ID"))
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.redis_url = os.getenv("REDIS_URL", "redis://trading-bot-redis:6379/0")
        
        # Überwachte Gruppen
        self.monitored_chats = [
            -1002299206473,  # VIP Signal Group
            -1001804143400   # Cryptet Channel
        ]
        
        self.client = None
        self.redis_client = None
        
    async def start(self):
        """Startet den Telegram Receiver Service."""
        print("🚀 Starting Telegram Receiver Service...")
        
        # Redis Verbindung
        self.redis_client = redis.from_url(self.redis_url)
        
        # Session-Pfad für Bot-Token
        session_path = "/app/session_files/telegram_bot_receiver"
        
        # Lösche alte Session falls vorhanden (verhindert User-Session Konflikt)
        import os as file_os
        session_file = f"{session_path}.session"
        if file_os.path.exists(session_file):
            try:
                file_os.remove(session_file)
                print("🗑️ Removed old session file to ensure bot token usage")
            except Exception as e:
                print(f"⚠️ Could not remove session: {e}")
        
        # Telegram Client mit expliziter Bot-Session
        self.client = TelegramClient(session_path, self.api_id, self.api_hash)
        
        # Event Handler registrieren
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            await self.process_message(event)
        
        # Client mit Bot Token starten (ohne User-Session)
        print("🤖 Connecting with Bot Token...")
        await self.client.start(bot_token=self.bot_token)
        print("✅ Telegram Bot Client connected!")
        
        # Überwachte Chats beitreten/prüfen
        for chat_id in self.monitored_chats:
            try:
                entity = await self.client.get_entity(chat_id)
                print(f"✅ Monitoring chat: {entity.title} ({chat_id})")
            except Exception as e:
                print(f"❌ Failed to access chat {chat_id}: {e}")
        
        print("🔄 Service is running and monitoring messages...")
        
        # Dauerhaft laufen lassen
        await self.client.run_until_disconnected()
    
    async def process_message(self, event):
        """Verarbeitet eingehende Telegram-Nachrichten."""
        try:
            chat_id = event.chat_id
            
            # Nur überwachte Chats
            if chat_id not in self.monitored_chats:
                return
            
            message_text = event.message.message
            if not message_text:
                return
            
            # Message-Daten für Redis Queue
            message_data = {
                "text": message_text,
                "chat_id": chat_id,
                "message_id": event.message.id,
                "sender_id": event.message.sender_id,
                "timestamp": event.message.date.isoformat(),
                "source": "telegram_receiver"
            }
            
            # Zur Redis Queue hinzufügen
            await self.redis_client.lpush(
                "telegram_messages", 
                json.dumps(message_data)
            )
            
            print(f"📨 Message queued from {chat_id}: {message_text[:50]}...")
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    async def stop(self):
        """Stoppt den Service."""
        if self.client:
            await self.client.disconnect()
        if self.redis_client:
            await self.redis_client.aclose()

async def main():
    """Hauptfunktion."""
    service = TelegramReceiverService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Telegram Receiver Service...")
        await service.stop()
    except Exception as e:
        print(f"❌ Service error: {e}")
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())