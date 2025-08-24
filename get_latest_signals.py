#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script zum Abrufen der letzten Signale aus VIP-Gruppe und Cryptet-Kanal
"""
import asyncio
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from telethon import TelegramClient
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class SignalRetriever:
    def __init__(self):
        # Telegram API Konfiguration
        api_id_str = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not (api_id_str and api_hash):
            raise RuntimeError("TELEGRAM_API_ID und TELEGRAM_API_HASH müssen in der .env Datei gesetzt sein.")
        
        self.client = TelegramClient("signal_retriever_session", int(api_id_str), api_hash)
        
        # Gruppe IDs basierend auf der Systemkonfiguration
        self.vip_group_id = -2299206473  # Normal signal group
        self.cryptet_channel_id = -1001804143400  # Official @cryptet_com channel
        
    async def start(self):
        """Starte den Telegram Client"""
        await self.client.start(bot_token=self.bot_token)
        print("✅ Telegram Client gestartet")
        
    async def stop(self):
        """Stoppe den Telegram Client"""
        await self.client.disconnect()
        print("✅ Telegram Client gestoppt")
        
    async def get_latest_messages(self, chat_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Hole die letzten Nachrichten aus einem Chat"""
        try:
            entity = await self.client.get_entity(chat_id)
            messages = []
            
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.text:  # Nur Textnachrichten
                    messages.append({
                        "id": message.id,
                        "text": message.text,
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S UTC") if message.date else "Unknown",
                        "sender_id": getattr(message.sender, "id", "Unknown") if message.sender else "Unknown"
                    })
            
            return messages
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen von Nachrichten aus Chat {chat_id}: {e}")
            return []
    
    async def get_chat_info(self, chat_id: int) -> Dict[str, Any]:
        """Hole Informationen über einen Chat"""
        try:
            entity = await self.client.get_entity(chat_id)
            return {
                "id": entity.id,
                "title": getattr(entity, "title", "Unknown"),
                "username": getattr(entity, "username", None),
                "participants_count": getattr(entity, "participants_count", "Unknown")
            }
        except Exception as e:
            print(f"❌ Fehler beim Abrufen von Chat-Informationen für {chat_id}: {e}")
            return {"id": chat_id, "error": str(e)}
    
    def format_signal_message(self, message: Dict[str, Any], chat_name: str) -> str:
        """Formatiere eine Signal-Nachricht für die Ausgabe"""
        text = message["text"]
        # Kürze sehr lange Nachrichten
        if len(text) > 300:
            text = text[:300] + "..."
            
        return f"""
📊 {chat_name}
🆔 Message ID: {message["id"]}
📅 Datum: {message["date"]}
👤 Sender: {message["sender_id"]}
📝 Inhalt:
{text}
{'='*50}"""

async def main():
    retriever = SignalRetriever()
    
    try:
        await retriever.start()
        
        print("🔍 Hole Chat-Informationen...")
        
        # Hole Chat-Informationen
        vip_info = await retriever.get_chat_info(retriever.vip_group_id)
        cryptet_info = await retriever.get_chat_info(retriever.cryptet_channel_id)
        
        print(f"\n📋 VIP-Gruppe Info:")
        print(f"   ID: {vip_info.get('id')}")
        print(f"   Titel: {vip_info.get('title', 'Unknown')}")
        print(f"   Username: @{vip_info.get('username', 'N/A')}")
        print(f"   Teilnehmer: {vip_info.get('participants_count', 'Unknown')}")
        
        print(f"\n📋 Cryptet-Kanal Info:")
        print(f"   ID: {cryptet_info.get('id')}")
        print(f"   Titel: {cryptet_info.get('title', 'Unknown')}")
        print(f"   Username: @{cryptet_info.get('username', 'N/A')}")
        print(f"   Teilnehmer: {cryptet_info.get('participants_count', 'Unknown')}")
        
        print("\n🔍 Hole die letzten 5 Nachrichten aus beiden Gruppen...")
        
        # Hole die letzten Nachrichten
        vip_messages = await retriever.get_latest_messages(retriever.vip_group_id, limit=5)
        cryptet_messages = await retriever.get_latest_messages(retriever.cryptet_channel_id, limit=5)
        
        print(f"\n🎯 LETZTE SIGNALE AUS VIP-GRUPPE ({vip_info.get('title', 'Unknown')}):")
        print("=" * 80)
        
        if vip_messages:
            for i, message in enumerate(vip_messages, 1):
                print(f"\n#{i} - {retriever.format_signal_message(message, 'VIP-Gruppe')}")
        else:
            print("❌ Keine Nachrichten in der VIP-Gruppe gefunden oder Zugriff verweigert")
        
        print(f"\n\n🔥 LETZTE SIGNALE AUS CRYPTET-KANAL ({cryptet_info.get('title', 'Unknown')}):")
        print("=" * 80)
        
        if cryptet_messages:
            for i, message in enumerate(cryptet_messages, 1):
                print(f"\n#{i} - {retriever.format_signal_message(message, 'Cryptet-Kanal')}")
        else:
            print("❌ Keine Nachrichten im Cryptet-Kanal gefunden oder Zugriff verweigert")
        
        # Zusammenfassung
        print(f"\n\n📊 ZUSAMMENFASSUNG:")
        print(f"   VIP-Gruppe: {len(vip_messages)} Nachrichten abgerufen")
        print(f"   Cryptet-Kanal: {len(cryptet_messages)} Nachrichten abgerufen")
        print(f"   Gesamte Nachrichten: {len(vip_messages) + len(cryptet_messages)}")
        
    except Exception as e:
        print(f"❌ Fehler beim Ausführen des Scripts: {e}")
        
    finally:
        await retriever.stop()

if __name__ == "__main__":
    asyncio.run(main())