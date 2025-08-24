#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script zum Abrufen der aktuellen Signale mit einer separaten Session
Verwendet eine eigene Session, um Konflikte mit dem laufenden System zu vermeiden
"""
import asyncio
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from telethon import TelegramClient
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class CurrentSignalRetriever:
    def __init__(self):
        # API Credentials
        api_id_str = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        
        if not (api_id_str and api_hash):
            raise RuntimeError("TELEGRAM_API_ID und TELEGRAM_API_HASH müssen gesetzt sein.")
        
        # Verwende eine separate Session für diesen Abruf
        self.session_name = "current_signals_session"
        self.client = TelegramClient(self.session_name, int(api_id_str), api_hash)
        
        # Überwachte Gruppen aus der Konfiguration
        self.chat_configs = {
            "VIP Signal Group": {"id": -2299206473, "type": "group"},
            "Cryptet Official Channel": {"id": -1001804143400, "type": "channel"}, 
            "PH FUTURES VIP": {"id": -1002773853382, "type": "group"}
        }
        
    async def start_session(self):
        """Starte Client mit der separaten Session"""
        try:
            # Versuche mit der bestehenden Session zu starten
            await self.client.start()
            
            # Bestätige Login
            me = await self.client.get_me()
            print(f"✅ Session aktiv:")
            print(f"   Name: {me.first_name} {me.last_name or ''}")
            print(f"   Username: @{me.username or 'kein_username'}")
            print(f"   ID: {me.id}")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Starten der Session: {e}")
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
                        "chat_title": getattr(entity, "title", chat_name),
                        "chat_id": chat_id
                    })
            
            return messages
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen von Nachrichten aus {chat_name}: {e}")
            return []
    
    def format_signal(self, msg: Dict, chat_name: str) -> str:
        """Formatiere ein Signal für die Ausgabe"""
        text = msg.get("text", "")
        
        # Signal-Erkennung
        signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN", 
                          "TARGET", "STOP", "LOSS", "PROFIT", "LEVERAGE", "🟢", "🔴", "↪️", "🔝", "BREAKOUT", "BREAK"]
        is_signal = any(keyword.upper() in text.upper() for keyword in signal_keywords)
        
        emoji = "🎯" if is_signal else "💬"
        priority = "SIGNAL" if is_signal else "Normal"
        
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
        
        # Kürze Text für Übersicht
        display_text = text
        if len(text) > 500:
            display_text = text[:500] + "\n... (gekürzt)"
        
        return f"""
{emoji} {chat_name} | {priority}
📅 {msg.get('date')} | 👤 {sender_info}
🆔 Message ID: {msg.get('id')} | Chat ID: {msg.get('chat_id')}
📝 Inhalt:
{display_text}
{'-' * 70}"""

    async def run_signal_retrieval(self):
        """Führe Signal-Abruf aus"""
        print("🎯 AKTUELLE SIGNALE AUS TELEGRAM-GRUPPEN")
        print("=" * 70)
        print(f"🔑 Session: {self.session_name}")
        print(f"🕐 Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Starte Session
            if not await self.start_session():
                print("❌ Session konnte nicht gestartet werden")
                return
            
            # 2. Prüfe alle Gruppen und hole Nachrichten
            print(f"\n📋 SIGNAL-ABRUF:")
            print("=" * 70)
            
            all_messages = []
            
            for chat_name, config in self.chat_configs.items():
                chat_id = config["id"]
                print(f"\n>>> {chat_name} (ID: {chat_id}) <<<")
                
                # Chat-Info
                chat_info = await self.get_chat_info(chat_id)
                if "error" not in chat_info:
                    print(f"✅ {chat_info.get('title')} | {chat_info.get('type')} | {chat_info.get('participants_count')} Mitglieder")
                    
                    # Nachrichten abrufen
                    messages = await self.get_latest_messages(chat_id, chat_name, 3)  # Nur die letzten 3
                    if messages:
                        print(f"📨 {len(messages)} Nachrichten abgerufen")
                        all_messages.extend(messages)
                        
                        # Zeige Nachrichten direkt
                        for i, msg in enumerate(messages, 1):
                            is_signal = any(keyword.upper() in msg.get("text", "").upper() for keyword in 
                                           ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN"])
                            if is_signal:
                                print(f"\n🎯 Signal #{i}:")
                                print(self.format_signal(msg, chat_name))
                    else:
                        print("❌ Keine Nachrichten abgerufen")
                else:
                    print(f"❌ Zugriff verweigert: {chat_info.get('error')}")
            
            # 3. Zusammenfassung
            if all_messages:
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
                
                print(f"\n📊 ZUSAMMENFASSUNG:")
                print(f"   Gesamte Nachrichten: {len(all_messages)}")
                print(f"   🎯 Trading-Signale: {len(signals)}")
                print(f"   💬 Normale Nachrichten: {len(normal_messages)}")
                
                # Zeige die neueste Nachricht
                if all_messages:
                    # Sortiere nach Datum
                    all_messages.sort(key=lambda x: x.get("date", ""), reverse=True)
                    latest = all_messages[0]
                    
                    # Finde den Chat-Namen
                    chat_name = "Unknown"
                    for name, config in self.chat_configs.items():
                        if latest.get("chat_id") == config["id"]:
                            chat_name = name
                            break
                    
                    print(f"\n🕐 NEUESTE NACHRICHT:")
                    print(self.format_signal(latest, chat_name))
                
                # Zeige nur die wichtigsten Signale
                if signals:
                    print(f"\n🎯 LETZTE TRADING-SIGNALE:")
                    print("-" * 50)
                    for i, signal in enumerate(signals[:3], 1):  # Top 3 Signale
                        chat_name = "Unknown"
                        for name, config in self.chat_configs.items():
                            if signal.get("chat_id") == config["id"]:
                                chat_name = name
                                break
                        print(f"\nSignal #{i}:")
                        print(self.format_signal(signal, chat_name))
            else:
                print(f"\n❌ KEINE NACHRICHTEN GEFUNDEN")
                print(f"   Mögliche Gründe:")
                print(f"   - Account ist nicht Mitglied der Gruppen")
                print(f"   - Keine neuen Nachrichten vorhanden")
                print(f"   - Gruppen sind privat/geschlossen")
                
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.client.disconnect()
            print("\n✅ Session beendet")

async def main():
    retriever = CurrentSignalRetriever()
    await retriever.run_signal_retrieval()

if __name__ == "__main__":
    print("🔑 Verwende separate Session für Signal-Abruf")
    print("🚀 System läuft parallel auf http://localhost:8000")
    print()
    
    asyncio.run(main())