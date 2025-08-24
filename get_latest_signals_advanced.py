#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verbessertes Script zum Abrufen der letzten Signale aus VIP-Gruppe und Cryptet-Kanal
Verwendet die bestehende trading_bot_session
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError, ChatAdminRequiredError, PeerIdInvalidError
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class AdvancedSignalRetriever:
    def __init__(self):
        # Telegram API Konfiguration
        api_id_str = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not (api_id_str and api_hash):
            raise RuntimeError("TELEGRAM_API_ID und TELEGRAM_API_HASH müssen in der .env Datei gesetzt sein.")
        
        # Verwende die gleiche Session-Datei wie das Hauptsystem
        self.client = TelegramClient("trading_bot_session", int(api_id_str), api_hash)
        
        # Gruppe IDs basierend auf der Systemkonfiguration
        self.vip_group_id = -2299206473  # Normal signal group  
        self.cryptet_channel_id = -1001804143400  # Official @cryptet_com channel
        self.own_group_id = -1002773853382  # PH FUTURES VIP group
        
        # Alle zu überwachenden Chats
        self.chat_configs = {
            "VIP Signal Group": {"id": -2299206473, "type": "group"},
            "Cryptet Official Channel": {"id": -1001804143400, "type": "channel"},
            "PH FUTURES VIP": {"id": -1002773853382, "type": "group"}
        }
        
    async def start(self):
        """Starte den Telegram Client"""
        await self.client.start(bot_token=self.bot_token)
        print("✅ Telegram Client gestartet (verwendet bestehende Session)")
        
    async def stop(self):
        """Stoppe den Telegram Client"""
        await self.client.disconnect()
        print("✅ Telegram Client gestoppt")
        
    async def get_latest_messages_safe(self, chat_id: int, chat_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Sichere Methode zum Abrufen der letzten Nachrichten"""
        try:
            print(f"🔍 Versuche Zugriff auf {chat_name} (ID: {chat_id})...")
            
            # Versuche verschiedene Methoden, um auf den Chat zuzugreifen
            entity = None
            
            # Methode 1: Direkt über die ID
            try:
                entity = await self.client.get_entity(chat_id)
                print(f"✅ Direkter Zugriff auf {chat_name} erfolgreich")
            except Exception as e1:
                print(f"⚠️  Direkter Zugriff fehlgeschlagen: {e1}")
                
                # Methode 2: Über get_dialogs suchen
                try:
                    async for dialog in self.client.iter_dialogs():
                        if dialog.entity.id == chat_id:
                            entity = dialog.entity
                            print(f"✅ Gefunden über Dialogs: {chat_name}")
                            break
                except Exception as e2:
                    print(f"⚠️  Dialog-Suche fehlgeschlagen: {e2}")
            
            if not entity:
                print(f"❌ Kann nicht auf {chat_name} zugreifen - Bot ist möglicherweise nicht Mitglied")
                return []
            
            # Hole die letzten Nachrichten
            messages = []
            count = 0
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.text and message.text.strip():  # Nur nicht-leere Textnachrichten
                    count += 1
                    messages.append({
                        "id": message.id,
                        "text": message.text,
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S UTC") if message.date else "Unknown",
                        "sender_id": getattr(message.sender, "id", "Unknown") if message.sender else "Unknown",
                        "sender_username": getattr(message.sender, "username", None) if message.sender else None,
                        "chat_title": getattr(entity, "title", chat_name)
                    })
            
            print(f"✅ {len(messages)} Nachrichten aus {chat_name} abgerufen")
            return messages
            
        except ChannelPrivateError:
            print(f"❌ {chat_name} ist privat - Bot hat keinen Zugriff")
        except ChatAdminRequiredError:
            print(f"❌ Admin-Rechte erforderlich für {chat_name}")
        except PeerIdInvalidError:
            print(f"❌ Ungültige Chat-ID für {chat_name}")
        except Exception as e:
            print(f"❌ Unerwarteter Fehler bei {chat_name}: {e}")
        
        return []
    
    async def list_available_chats(self):
        """Liste alle verfügbaren Chats auf"""
        print("\n📋 VERFÜGBARE CHATS:")
        print("=" * 60)
        
        try:
            count = 0
            async for dialog in self.client.iter_dialogs():
                count += 1
                if count > 20:  # Begrenze auf die ersten 20
                    break
                    
                chat_type = "Unknown"
                if hasattr(dialog.entity, 'megagroup') and dialog.entity.megagroup:
                    chat_type = "Megagroup"
                elif hasattr(dialog.entity, 'broadcast') and dialog.entity.broadcast:
                    chat_type = "Channel"
                elif hasattr(dialog.entity, 'bot') and dialog.entity.bot:
                    chat_type = "Bot"
                else:
                    chat_type = "Group/Chat"
                
                title = getattr(dialog.entity, 'title', 'Unknown')
                username = getattr(dialog.entity, 'username', None)
                user_str = f"@{username}" if username else "No username"
                
                print(f"{count:2d}. ID: {dialog.entity.id:>15} | {chat_type:>10} | {title} ({user_str})")
                
                # Prüfe, ob es einer unserer überwachten Chats ist
                for name, config in self.chat_configs.items():
                    if config["id"] == dialog.entity.id:
                        print(f"    🎯 >>> ÜBERWACHT als '{name}' <<<")
                        
        except Exception as e:
            print(f"❌ Fehler beim Auflisten der Chats: {e}")
    
    def format_signal_message(self, message: Dict[str, Any], chat_name: str) -> str:
        """Formatiere eine Signal-Nachricht für die Ausgabe"""
        text = message["text"]
        
        # Suche nach Signal-Keywords
        signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN"]
        is_likely_signal = any(keyword.upper() in text.upper() for keyword in signal_keywords)
        
        # Emoji je nach Signal-Wahrscheinlichkeit
        emoji = "🎯" if is_likely_signal else "💬"
        
        # Kürze sehr lange Nachrichten
        if len(text) > 400:
            text = text[:400] + "\n... (gekürzt)"
            
        sender_info = f"👤 Sender: {message['sender_id']}"
        if message.get('sender_username'):
            sender_info += f" (@{message['sender_username']})"
            
        return f"""
{emoji} {chat_name} - {message['chat_title']}
🆔 Message ID: {message["id"]}
📅 Datum: {message["date"]}
{sender_info}
📝 Inhalt:
{'-' * 50}
{text}
{'-' * 50}"""

async def main():
    retriever = AdvancedSignalRetriever()
    
    try:
        await retriever.start()
        
        # Liste verfügbare Chats auf
        await retriever.list_available_chats()
        
        print(f"\n\n🔍 HOLE LETZTE SIGNALE AUS KONFIGURIERTEN CHATS...")
        print("=" * 80)
        
        all_messages = []
        
        # Durchlaufe alle konfigurierten Chats
        for chat_name, config in retriever.chat_configs.items():
            print(f"\n>>> {chat_name} (ID: {config['id']}) <<<")
            messages = await retriever.get_latest_messages_safe(
                config['id'], 
                chat_name, 
                limit=3  # Nur die letzten 3 Nachrichten pro Chat
            )
            
            if messages:
                print(f"🎯 SIGNALE aus {chat_name}:")
                for i, message in enumerate(messages, 1):
                    print(retriever.format_signal_message(message, chat_name))
                    all_messages.append(message)
                    
                    if i < len(messages):
                        print("\n" + "="*50 + "\n")
            else:
                print(f"❌ Keine Nachrichten aus {chat_name} abgerufen")
            
            print("\n" + "="*80 + "\n")
        
        # Zusammenfassung
        print(f"\n📊 ZUSAMMENFASSUNG:")
        print(f"   Gesamte abgerufene Nachrichten: {len(all_messages)}")
        print(f"   Überwachte Chats: {len(retriever.chat_configs)}")
        
        # Analysiere Nachrichten auf Signal-Keywords
        signal_count = 0
        for msg in all_messages:
            signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN"]
            if any(keyword.upper() in msg["text"].upper() for keyword in signal_keywords):
                signal_count += 1
        
        print(f"   Wahrscheinliche Trading-Signale: {signal_count}")
        
        if len(all_messages) == 0:
            print(f"\n⚠️  HINWEIS:")
            print(f"   Falls keine Nachrichten abgerufen wurden, prüfen Sie:")
            print(f"   1. Bot ist in allen Gruppen/Kanälen als Mitglied hinzugefügt")
            print(f"   2. Bot hat die nötigen Berechtigungen")
            print(f"   3. Chat-IDs sind korrekt")
        
    except Exception as e:
        print(f"❌ Fehler beim Ausführen des Scripts: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await retriever.stop()

if __name__ == "__main__":
    asyncio.run(main())