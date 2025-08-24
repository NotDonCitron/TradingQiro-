#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script zum Abrufen der letzten Signale mit vorhandenen funktionierenden Sessions
Nutzt bestehende Session-Dateien ohne erneute Anmeldung
"""
import asyncio
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from telethon import TelegramClient

class ExistingSessionRetriever:
    def __init__(self):
        # API Credentials
        self.api_id = 26708757
        self.api_hash = "e58c6204a1478da2b764d5fceff846e5"
        
        # Verfügbare Session-Dateien prüfen
        self.available_sessions = []
        session_candidates = [
            "trading_bot_session",
            "user_signal_session", 
            "user_trading_bot_session",
            "cryptet_finder_session",
            "signal_retriever_session"
        ]
        
        for session in session_candidates:
            if os.path.exists(f"{session}.session"):
                self.available_sessions.append(session)
        
        print(f"📁 Verfügbare Sessions: {self.available_sessions}")
        
        # Verwende die erste verfügbare Session
        if self.available_sessions:
            self.session_name = self.available_sessions[0]
            print(f"🔑 Verwende Session: {self.session_name}")
        else:
            raise RuntimeError("Keine Session-Dateien gefunden!")
        
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Überwachte Gruppen
        self.chat_configs = {
            "VIP Signal Group": {"id": -2299206473, "type": "group"},
            "Cryptet Official Channel": {"id": -1001804143400, "type": "channel"}, 
            "PH FUTURES VIP": {"id": -1002773853382, "type": "group"}
        }
        
    async def start_with_existing_session(self):
        """Starte mit vorhandener Session"""
        try:
            await self.client.start()
            
            # Prüfe ob wir eingeloggt sind
            me = await self.client.get_me()
            print(f"✅ Erfolgreich mit bestehender Session verbunden!")
            print(f"   Name: {me.first_name} {me.last_name or ''}")
            print(f"   Username: @{me.username or 'kein_username'}")
            print(f"   User ID: {me.id}")
            print(f"   Telefon: {me.phone or 'nicht verfügbar'}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Starten mit Session {self.session_name}: {e}")
            
            # Versuche nächste Session
            if len(self.available_sessions) > 1:
                self.available_sessions.remove(self.session_name)
                self.session_name = self.available_sessions[0]
                print(f"🔄 Versuche nächste Session: {self.session_name}")
                
                await self.client.disconnect()
                self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
                return await self.start_with_existing_session()
            
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
                "participants_count": getattr(entity, "participants_count", "Unknown")
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
        if len(text) > 350:
            text = text[:350] + "\n... (gekürzt)"
        
        return f"""
{emoji} {chat_name}
🆔 ID: {msg.get('id')} | 📅 {msg.get('date')} | 👤 {sender_info}
📝 Inhalt:
{text}
{'-' * 60}"""

    async def run_signal_retrieval(self):
        """Führe den Signal-Abruf aus"""
        print("🚀 STARTE SIGNAL-ABRUF MIT BESTEHENDER SESSION")
        print("=" * 70)
        
        try:
            # 1. Verbinde mit bestehender Session
            success = await self.start_with_existing_session()
            if not success:
                print("❌ Keine funktionierende Session gefunden")
                return
            
            # 2. Hole Nachrichten aus allen überwachten Chats
            print(f"\n📨 HOLE LETZTE NACHRICHTEN AUS ÜBERWACHTEN CHATS:")
            print("=" * 70)
            
            all_messages = []
            
            for chat_name, config in self.chat_configs.items():
                chat_id = config["id"]
                print(f"\n>>> {chat_name} (ID: {chat_id}) <<<")
                
                # Chat-Info
                chat_info = await self.get_chat_info(chat_id)
                if "error" not in chat_info:
                    print(f"✅ {chat_info.get('title')} | {chat_info.get('type')} | {chat_info.get('participants_count')} Mitglieder")
                    
                    # Nachrichten
                    messages = await self.get_latest_messages(chat_id, chat_name, 3)
                    if messages:
                        for msg in messages:
                            print(self.format_message(msg, chat_name))
                            all_messages.append(msg)
                    else:
                        print("❌ Keine Nachrichten abgerufen")
                else:
                    print(f"❌ Zugriff verweigert: {chat_info.get('error')}")
                
                print("="*70)
            
            # 3. Zusammenfassung und Analyse
            print(f"\n📊 ZUSAMMENFASSUNG:")
            print(f"   📁 Verwendete Session: {self.session_name}")
            print(f"   📨 Gesamte Nachrichten: {len(all_messages)}")
            print(f"   📋 Überwachte Chats: {len(self.chat_configs)}")
            
            # Analysiere Signale
            signals = []
            normal_messages = []
            
            for msg in all_messages:
                text = msg.get("text", "").upper()
                signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN"]
                if any(keyword in text for keyword in signal_keywords):
                    signals.append(msg)
                else:
                    normal_messages.append(msg)
            
            print(f"   🎯 Trading-Signale: {len(signals)}")
            print(f"   💬 Normale Nachrichten: {len(normal_messages)}")
            
            # Zeige neueste Signale
            if signals:
                print(f"\n🎯 NEUESTE TRADING-SIGNALE:")
                print("-" * 50)
                
                # Sortiere nach Datum
                signals.sort(key=lambda x: x.get("date", ""), reverse=True)
                
                for i, signal in enumerate(signals[:2], 1):  # Zeige top 2 Signale
                    chat_name = "Unknown"
                    for name, config in self.chat_configs.items():
                        if signal.get("chat_title", "").lower() in name.lower():
                            chat_name = name
                            break
                    
                    print(f"\n#{i} - {self.format_message(signal, chat_name)}")
            
            # Zeige neueste Nachricht insgesamt
            if all_messages:
                print(f"\n💬 ALLERLETZTE NACHRICHT (ALLE CHATS):")
                print("-" * 50)
                latest = max(all_messages, key=lambda x: x.get("date", ""))
                chat_name = "Unknown"
                for name, config in self.chat_configs.items():
                    if latest.get("chat_title", "").lower() in name.lower():
                        chat_name = name
                        break
                print(self.format_message(latest, chat_name))
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.client.disconnect()
            print("\n✅ Session beendet")

async def main():
    retriever = ExistingSessionRetriever()
    await retriever.run_signal_retrieval()

if __name__ == "__main__":
    print("🔄 Verwende bestehende Session-Dateien")
    print("💡 Kein erneuter Login erforderlich")
    print()
    
    asyncio.run(main())