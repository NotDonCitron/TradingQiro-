#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script zum Abrufen der letzten Signale mit User-API-Credentials
Verwendet die Telegram User API (nicht Bot API) für vollständigen Zugriff
"""
import asyncio
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class UserApiSignalRetriever:
    def __init__(self):
        # User API Credentials (nicht Bot Token!)
        self.api_id = 26708757
        self.api_hash = "e58c6204a1478da2b764d5fceff846e5"
        
        # Erstelle Client mit User-Session
        self.client = TelegramClient("user_signal_session", self.api_id, self.api_hash)
        
        # Konfigurierte Gruppen basierend auf dem System
        self.chat_configs = {
            "VIP Signal Group": {"id": -2299206473, "type": "group"},
            "Cryptet Official Channel": {"id": -1001804143400, "type": "channel"}, 
            "PH FUTURES VIP": {"id": -1002773853382, "type": "group"}
        }
        
    async def start(self):
        """Starte den Telegram Client mit User-Session"""
        await self.client.start()
        
        # Prüfe, ob wir eingeloggt sind
        me = await self.client.get_me()
        print(f"✅ Telegram User Client gestartet")
        print(f"   Eingeloggt als: {me.first_name} {me.last_name or ''} (@{me.username or 'kein_username'})")
        print(f"   User ID: {me.id}")
        print(f"   Telefon: {me.phone or 'nicht verfügbar'}")
        
    async def stop(self):
        """Stoppe den Telegram Client"""
        await self.client.disconnect()
        print("✅ Telegram User Client gestoppt")
        
    async def get_chat_info(self, chat_id: int) -> Dict[str, Any]:
        """Hole detaillierte Chat-Informationen"""
        try:
            entity = await self.client.get_entity(chat_id)
            
            # Detaillierte Informationen sammeln
            info = {
                "id": entity.id,
                "title": getattr(entity, "title", "Unknown"),
                "username": getattr(entity, "username", None),
                "type": type(entity).__name__,
                "participants_count": getattr(entity, "participants_count", "Unknown"),
                "access_hash": getattr(entity, "access_hash", None)
            }
            
            # Zusätzliche Infos für Channels
            if hasattr(entity, 'broadcast'):
                info["is_broadcast"] = entity.broadcast
            if hasattr(entity, 'megagroup'):
                info["is_megagroup"] = entity.megagroup
            if hasattr(entity, 'restricted'):
                info["is_restricted"] = entity.restricted
                
            return info
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen der Chat-Info für {chat_id}: {e}")
            return {"id": chat_id, "error": str(e)}
    
    async def get_latest_messages(self, chat_id: int, chat_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Hole die letzten Nachrichten aus einem Chat"""
        try:
            print(f"🔍 Hole Nachrichten aus {chat_name} (ID: {chat_id})...")
            
            entity = await self.client.get_entity(chat_id)
            messages = []
            
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.text and message.text.strip():  # Nur nicht-leere Textnachrichten
                    sender_info = {}
                    if message.sender:
                        sender_info = {
                            "id": message.sender.id,
                            "first_name": getattr(message.sender, "first_name", "Unknown"),
                            "last_name": getattr(message.sender, "last_name", ""),
                            "username": getattr(message.sender, "username", None),
                            "is_bot": getattr(message.sender, "bot", False)
                        }
                    
                    messages.append({
                        "id": message.id,
                        "text": message.text,
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S UTC") if message.date else "Unknown",
                        "sender": sender_info,
                        "chat_title": getattr(entity, "title", chat_name),
                        "reply_to": message.reply_to_msg_id if hasattr(message, 'reply_to_msg_id') else None,
                        "views": getattr(message, "views", None),
                        "forwards": getattr(message, "forwards", None)
                    })
            
            print(f"✅ {len(messages)} Nachrichten aus {chat_name} abgerufen")
            return messages
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen von Nachrichten aus {chat_name}: {e}")
            return []
    
    async def list_dialogs(self, limit: int = 20):
        """Liste die verfügbaren Dialogs auf"""
        print(f"\n📋 VERFÜGBARE DIALOGS (erste {limit}):")
        print("=" * 80)
        
        count = 0
        async for dialog in self.client.iter_dialogs():
            count += 1
            if count > limit:
                break
                
            entity = dialog.entity
            chat_type = self._get_chat_type(entity)
            
            title = getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown'))
            username = getattr(entity, 'username', None)
            user_str = f"@{username}" if username else "No username"
            
            unread = dialog.unread_count
            unread_str = f"({unread} unread)" if unread > 0 else ""
            
            print(f"{count:2d}. ID: {entity.id:>15} | {chat_type:>12} | {title} ({user_str}) {unread_str}")
            
            # Prüfe, ob es einer unserer überwachten Chats ist
            for name, config in self.chat_configs.items():
                if config["id"] == entity.id:
                    print(f"    🎯 >>> ÜBERWACHT als '{name}' <<<")
    
    def _get_chat_type(self, entity):
        """Bestimme den Chat-Typ"""
        if hasattr(entity, 'megagroup') and entity.megagroup:
            return "Megagroup"
        elif hasattr(entity, 'broadcast') and entity.broadcast:
            return "Channel"
        elif hasattr(entity, 'bot') and entity.bot:
            return "Bot"
        elif hasattr(entity, 'first_name'):
            return "User"
        else:
            return "Group"
    
    def format_message(self, msg: Dict, chat_name: str) -> str:
        """Formatiere eine Nachricht für die Ausgabe"""
        text = msg.get("text", "")
        
        # Suche nach Signal-Keywords
        signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN", 
                          "TARGET", "STOP", "LOSS", "PROFIT", "LEVERAGE", "COIN", "$", "USDT", 
                          "BTCUSDT", "ETHUSDT", "🟢", "🔴", "⚪", "↪️", "🔝"]
        is_likely_signal = any(keyword.upper() in text.upper() for keyword in signal_keywords)
        
        emoji = "🎯" if is_likely_signal else "💬"
        
        # Sender Info
        sender = msg.get("sender", {})
        if sender:
            sender_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
            if sender.get('username'):
                sender_info = f"{sender_name} (@{sender['username']})"
            else:
                sender_info = sender_name or "Unknown"
            
            if sender.get('is_bot'):
                sender_info += " [BOT]"
        else:
            sender_info = "Unknown"
        
        # Zusätzliche Infos
        extra_info = []
        if msg.get("views"):
            extra_info.append(f"{msg['views']} views")
        if msg.get("forwards"):
            extra_info.append(f"{msg['forwards']} forwards")
        if msg.get("reply_to"):
            extra_info.append(f"reply to {msg['reply_to']}")
        
        extra_str = f" ({', '.join(extra_info)})" if extra_info else ""
        
        # Kürze sehr lange Nachrichten
        if len(text) > 400:
            text = text[:400] + "\n... (gekürzt)"
        
        return f"""
{emoji} {chat_name} - {msg.get('chat_title', 'Unknown')}
🆔 Message ID: {msg.get('id')}
📅 Datum: {msg.get('date')}
👤 Von: {sender_info} (ID: {sender.get('id', 'Unknown')}){extra_str}
📝 Inhalt:
{'-' * 50}
{text}
{'-' * 50}"""

async def main():
    retriever = UserApiSignalRetriever()
    
    try:
        print("🚀 STARTE TELEGRAM USER API CLIENT...")
        print("=" * 80)
        
        await retriever.start()
        
        # Liste verfügbare Dialogs auf
        await retriever.list_dialogs(limit=30)
        
        print(f"\n\n📋 CHAT-INFORMATIONEN FÜR ÜBERWACHTE GRUPPEN:")
        print("=" * 80)
        
        # Hole detaillierte Infos für überwachte Chats
        for chat_name, config in retriever.chat_configs.items():
            chat_id = config["id"]
            print(f"\n>>> {chat_name} (ID: {chat_id}) <<<")
            
            chat_info = await retriever.get_chat_info(chat_id)
            if "error" not in chat_info:
                print(f"✅ Chat-Info:")
                print(f"   Titel: {chat_info.get('title', 'Unknown')}")
                print(f"   Typ: {chat_info.get('type', 'unknown')}")
                print(f"   Username: @{chat_info.get('username', 'N/A')}")
                print(f"   Teilnehmer: {chat_info.get('participants_count', 'Unknown')}")
                print(f"   Is Broadcast: {chat_info.get('is_broadcast', 'N/A')}")
                print(f"   Is Megagroup: {chat_info.get('is_megagroup', 'N/A')}")
            else:
                print(f"❌ Fehler: {chat_info.get('error')}")
        
        print(f"\n\n🎯 HOLE LETZTE SIGNALE AUS ÜBERWACHTEN GRUPPEN:")
        print("=" * 80)
        
        all_messages = []
        
        # Hole Nachrichten aus allen konfigurierten Chats
        for chat_name, config in retriever.chat_configs.items():
            chat_id = config["id"]
            print(f"\n>>> {chat_name} <<<")
            
            messages = await retriever.get_latest_messages(chat_id, chat_name, limit=5)
            
            if messages:
                print(f"🎯 LETZTE {len(messages)} NACHRICHTEN aus {chat_name}:")
                print("-" * 60)
                
                for i, msg in enumerate(messages, 1):
                    print(retriever.format_message(msg, chat_name))
                    all_messages.append(msg)
                    
                    if i < len(messages):
                        print("\n" + "="*50 + "\n")
            else:
                print(f"❌ Keine Nachrichten aus {chat_name} abgerufen")
            
            print("\n" + "="*80 + "\n")
        
        # Zusammenfassung und Analyse
        print(f"📊 ZUSAMMENFASSUNG:")
        print(f"   Gesamte abgerufene Nachrichten: {len(all_messages)}")
        print(f"   Überwachte Chats: {len(retriever.chat_configs)}")
        
        # Analysiere auf Signal-Keywords
        signal_count = 0
        for msg in all_messages:
            signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN"]
            text = msg.get("text", "")
            if any(keyword.upper() in text.upper() for keyword in signal_keywords):
                signal_count += 1
        
        print(f"   Wahrscheinliche Trading-Signale: {signal_count}")
        
        # Zeige die neuesten Signale nach Datum sortiert
        if all_messages:
            print(f"\n🕐 DIE 3 NEUESTEN NACHRICHTEN (CHRONOLOGISCH):")
            print("-" * 60)
            
            # Sortiere nach Datum
            sorted_messages = sorted(all_messages, key=lambda x: x.get("date", ""), reverse=True)
            
            for i, msg in enumerate(sorted_messages[:3], 1):
                chat_name = "Unknown"
                for name, config in retriever.chat_configs.items():
                    if msg.get("chat_title", "").lower() in name.lower() or str(config["id"]) in str(msg.get("id", "")):
                        chat_name = name
                        break
                
                print(f"\n#{i} - {retriever.format_message(msg, chat_name)}")
        
    except Exception as e:
        print(f"❌ Fehler beim Ausführen des Scripts: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await retriever.stop()

if __name__ == "__main__":
    print("🔑 Verwende Telegram User API (nicht Bot API)")
    print("   API ID: 26708757")
    print("   API Hash: e58c6204a1478da2b764d5fceff846e5")
    print("   Session: user_signal_session")
    print()
    
    asyncio.run(main())