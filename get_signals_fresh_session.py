#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frisches Script zum Abrufen der letzten Signale mit korrekter Telefonnummer
Erstellt eine neue Session für +4915217955921
"""
import asyncio
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

class FreshSessionSignalRetriever:
    def __init__(self):
        # API Credentials
        self.api_id = 26708757
        self.api_hash = "e58c6204a1478da2b764d5fceff846e5"
        
        # Korrekte Telefonnummer
        self.phone_number = "+4915217955921"
        
        # Neue Session erstellen
        self.session_name = "fresh_signal_session"
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Überwachte Gruppen
        self.chat_configs = {
            "VIP Signal Group": {"id": -2299206473, "type": "group"},
            "Cryptet Official Channel": {"id": -1001804143400, "type": "channel"}, 
            "PH FUTURES VIP": {"id": -1002773853382, "type": "group"}
        }
        
    async def start_with_phone(self):
        """Starte Client mit Telefonnummer"""
        print(f"🔑 Starte Telegram Client mit Telefonnummer: {self.phone_number}")
        
        await self.client.start(phone=self.phone_number)
        
        # Prüfe ob wir eingeloggt sind
        try:
            me = await self.client.get_me()
            print(f"✅ Erfolgreich eingeloggt!")
            print(f"   Name: {me.first_name} {me.last_name or ''}")
            print(f"   Username: @{me.username or 'kein_username'}")
            print(f"   User ID: {me.id}")
            print(f"   Telefon: {me.phone}")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Abrufen der User-Info: {e}")
            return False
    
    async def get_chat_info(self, chat_id: int) -> Dict[str, Any]:
        """Hole Chat-Informationen"""
        try:
            entity = await self.client.get_entity(chat_id)
            return {
                "id": entity.id,
                "title": getattr(entity, "title", "Unknown"),
                "username": getattr(entity, "username", None),
                "type": type(entity).__name__,
                "participants_count": getattr(entity, "participants_count", "Unknown"),
                "access_hash": getattr(entity, "access_hash", None)
            }
        except Exception as e:
            return {"id": chat_id, "error": str(e)}
    
    async def get_latest_messages(self, chat_id: int, chat_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Hole die letzten Nachrichten aus einem Chat"""
        try:
            print(f"🔍 Hole Nachrichten aus {chat_name} (ID: {chat_id})...")
            
            entity = await self.client.get_entity(chat_id)
            messages = []
            
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.text and message.text.strip():
                    sender_info = {}
                    if message.sender:
                        sender_info = {
                            "id": message.sender.id,
                            "first_name": getattr(message.sender, "first_name", "Unknown"),
                            "username": getattr(message.sender, "username", None),
                            "is_bot": getattr(message.sender, "bot", False)
                        }
                    
                    messages.append({
                        "id": message.id,
                        "text": message.text,
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S UTC") if message.date else "Unknown",
                        "sender": sender_info,
                        "chat_title": getattr(entity, "title", chat_name)
                    })
            
            print(f"✅ {len(messages)} Nachrichten aus {chat_name} abgerufen")
            return messages
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen von Nachrichten aus {chat_name}: {e}")
            return []
    
    def format_message(self, msg: Dict, chat_name: str) -> str:
        """Formatiere eine Nachricht für die Ausgabe"""
        text = msg.get("text", "")
        
        # Suche nach Signal-Keywords
        signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN", 
                          "TARGET", "STOP", "LOSS", "PROFIT", "LEVERAGE", "🟢", "🔴", "↪️", "🔝"]
        is_likely_signal = any(keyword.upper() in text.upper() for keyword in signal_keywords)
        
        emoji = "🎯" if is_likely_signal else "💬"
        
        # Sender Info
        sender = msg.get("sender", {})
        if sender:
            sender_name = sender.get("first_name", "Unknown")
            if sender.get("username"):
                sender_info = f"{sender_name} (@{sender['username']})"
            else:
                sender_info = sender_name
        else:
            sender_info = "Unknown"
        
        # Kürze sehr lange Nachrichten
        if len(text) > 300:
            text = text[:300] + "\n... (gekürzt)"
        
        return f"""
{emoji} {chat_name} - {msg.get('chat_title', 'Unknown')}
🆔 Message ID: {msg.get('id')}
📅 Datum: {msg.get('date')}
👤 Von: {sender_info} (ID: {sender.get('id', 'Unknown')})
📝 Inhalt:
{'-' * 50}
{text}
{'-' * 50}"""

    async def run_retrieval(self):
        """Führe den kompletten Abruf aus"""
        print("🚀 STARTE SIGNAL-ABRUF MIT FRISCHER SESSION")
        print("=" * 60)
        print(f"📱 Telefonnummer: {self.phone_number}")
        print(f"🔑 API ID: {self.api_id}")
        print(f"📁 Session: {self.session_name}")
        
        try:
            # 1. Starte Client
            success = await self.start_with_phone()
            if not success:
                print("❌ Login fehlgeschlagen")
                return
            
            # 2. Teste Chat-Zugriff und hole Nachrichten
            print(f"\n📋 CHAT-INFORMATIONEN UND NACHRICHTEN:")
            print("=" * 60)
            
            all_messages = []
            
            for chat_name, config in self.chat_configs.items():
                chat_id = config["id"]
                print(f"\n>>> {chat_name} (ID: {chat_id}) <<<")
                
                # Chat-Info
                chat_info = await self.get_chat_info(chat_id)
                if "error" not in chat_info:
                    print(f"✅ Chat-Info:")
                    print(f"   Titel: {chat_info.get('title')}")
                    print(f"   Typ: {chat_info.get('type')}")
                    print(f"   Username: @{chat_info.get('username', 'N/A')}")
                    print(f"   Teilnehmer: {chat_info.get('participants_count')}")
                    
                    # Nachrichten abrufen
                    messages = await self.get_latest_messages(chat_id, chat_name, 3)
                    if messages:
                        print(f"\n📨 LETZTE {len(messages)} NACHRICHTEN:")
                        for i, msg in enumerate(messages, 1):
                            print(self.format_message(msg, chat_name))
                            all_messages.append(msg)
                            if i < len(messages):
                                print("\n" + "="*40 + "\n")
                    else:
                        print("❌ Keine Nachrichten abgerufen")
                else:
                    print(f"❌ Fehler: {chat_info.get('error')}")
                
                print("\n" + "="*60 + "\n")
            
            # 3. Zusammenfassung
            print(f"📊 ZUSAMMENFASSUNG:")
            print(f"   Gesamte Nachrichten: {len(all_messages)}")
            print(f"   Überwachte Chats: {len(self.chat_configs)}")
            
            # Signal-Analyse
            signal_count = 0
            for msg in all_messages:
                signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN"]
                if any(keyword.upper() in msg.get("text", "").upper() for keyword in signal_keywords):
                    signal_count += 1
            
            print(f"   Wahrscheinliche Signale: {signal_count}")
            
            if all_messages:
                print(f"\n🎯 NEUESTE NACHRICHT:")
                latest = max(all_messages, key=lambda x: x.get("date", ""))
                chat_name = "Unknown"
                for name, config in self.chat_configs.items():
                    if latest.get("chat_title", "").lower() in name.lower():
                        chat_name = name
                        break
                print(self.format_message(latest, chat_name))
            
        except SessionPasswordNeededError:
            print("🔒 Zwei-Faktor-Authentifizierung ist aktiviert.")
            password = input("Bitte geben Sie Ihr 2FA-Passwort ein: ")
            await self.client.sign_in(password=password)
            print("✅ 2FA erfolgreich!")
            # Versuche erneut
            await self.run_retrieval()
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.client.disconnect()
            print("✅ Client getrennt")

async def main():
    # Lösche alte Session-Datei falls vorhanden
    session_file = "fresh_signal_session.session"
    if os.path.exists(session_file):
        os.remove(session_file)
        print(f"🗑️ Alte Session-Datei gelöscht: {session_file}")
    
    retriever = FreshSessionSignalRetriever()
    await retriever.run_retrieval()

if __name__ == "__main__":
    print("📞 Verwende Telefonnummer: +4915217955921")
    print("💡 Wenn Sie zur Eingabe eines Codes aufgefordert werden, schauen Sie in Ihre Telegram-App!")
    print()
    
    asyncio.run(main())