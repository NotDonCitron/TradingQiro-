# feat(connector): async Telethon connector for Telegram signals
from __future__ import annotations
import os
from typing import Callable, Optional, Awaitable, Any
try:
    from telethon import TelegramClient, events
except ImportError:
    TelegramClient = None

class TelethonConnector:
    """Minimaler Telethon-Wrapper für das Empfangen & Senden von Nachrichten."""
    def __init__(self) -> None:
        if TelegramClient is None:
            raise ImportError("Telethon ist nicht installiert. Bitte 'pip install telethon' ausführen.")
        
        # Use API credentials from environment
        api_id_str = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        
        # Bot token for authentication
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        # Get monitored chats from environment (comma-separated list)
        monitored_chats_str = os.getenv("MONITORED_CHAT_IDS", "")
        self.monitored_chats = []
        if monitored_chats_str:
            try:
                self.monitored_chats = [int(chat_id.strip()) for chat_id in monitored_chats_str.split(",") if chat_id.strip()]
            except ValueError:
                print(f"Warning: Invalid MONITORED_CHAT_IDS format: {monitored_chats_str}")

        if not (api_id_str and api_hash):
            raise RuntimeError("TELEGRAM_API_ID und TELEGRAM_API_HASH müssen gesetzt sein.")
        
        # Use the successful user session
        self.client = TelegramClient("user_telegram_session", int(api_id_str), api_hash)
        self._handler: Optional[Callable[[str, dict], Awaitable[None]]] = None

    async def start(self) -> None:
        # Start with user session (no bot token needed)
        await self.client.start()
        
        # Get client info to confirm login
        try:
            me = await self.client.get_me()
            is_bot = getattr(me, 'bot', False)
            client_type = "Bot" if is_bot else "User"
            print(f"✅ Telegram {client_type} Client gestartet")
            print(f"   Name: {me.first_name} {me.last_name or ''}")
            print(f"   Username: @{me.username or 'kein_username'}")
            print(f"   ID: {me.id}")
            if not is_bot:
                print(f"   Telefon: {me.phone or 'nicht verfügbar'}")
        except Exception as e:
            print(f"⚠️ Fehler beim Abrufen der Client-Info: {e}")
        
        if self._handler:
            if self.monitored_chats:
                # Monitor specific chats only
                print(f"📡 Überwache {len(self.monitored_chats)} Chats: {self.monitored_chats}")
                self.client.add_event_handler(self._on_message, events.NewMessage(chats=self.monitored_chats))
            else:
                # Monitor all chats (fallback)
                print("⚠️ Warnung: Keine MONITORED_CHAT_IDS konfiguriert, überwache ALLE Chats")
                self.client.add_event_handler(self._on_message, events.NewMessage())

    async def stop(self) -> None:
        await self.client.disconnect()

    def register_message_handler(self, callback: Callable[[str, dict], Awaitable[None]]) -> None:
        self._handler = callback

    async def _on_message(self, event: Any) -> None:
        if not self._handler:
            return
        
        msg = event.raw_text or ""
        
        # Extract URLs from message entities (important for Cryptet links)
        extracted_urls = []
        if hasattr(event.message, 'entities') and event.message.entities:
            for entity in event.message.entities:
                # Check for URL entities
                if hasattr(entity, '__class__') and 'Url' in entity.__class__.__name__:
                    # Extract URL from message text
                    start = getattr(entity, 'offset', 0)
                    length = getattr(entity, 'length', 0)
                    if start >= 0 and length > 0 and start + length <= len(msg):
                        url = msg[start:start + length]
                        if url and 'cryptet.com' in url.lower():
                            extracted_urls.append(url)
                            print(f"🔗 Cryptet-URL aus Entity extrahiert: {url}")
        
        # If we found Cryptet URLs in entities but the message text doesn't contain them,
        # use the first extracted URL as the message
        final_message = msg
        if extracted_urls and not any('cryptet.com' in msg.lower() for url in extracted_urls):
            final_message = extracted_urls[0]  # Use the first Cryptet URL
            print(f"📝 Nachricht erweitert: '{msg}' -> '{final_message}'")
        
        meta = {
            "chat_id": getattr(event.chat, "id", None), 
            "message_id": getattr(event.message, "id", None),
            "extracted_urls": extracted_urls,
            "original_text": msg
        }
        
        await self._handler(final_message, meta)
    
    async def send_message(self, chat_id: int, message: str) -> None:
        """Send a message to a Telegram chat/group/channel."""
        try:
            # Try to get the entity first
            entity = await self.client.get_entity(chat_id)
            await self.client.send_message(entity, message)
        except Exception as e:
            # Fallback: try sending directly with the chat_id
            try:
                await self.client.send_message(chat_id, message)
            except Exception as e2:
                raise RuntimeError(f"Failed to send message to {chat_id}: {e}. Also failed fallback: {e2}")