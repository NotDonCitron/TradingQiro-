#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Abrufen der letzten Signale mit der erfolgreichen User-Session
Verwendet: user_telegram_session.session
"""
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any
from telethon import TelegramClient

class UserSessionSignalRetriever:
    def __init__(self):
        # API Credentials
        self.api_id = 26708757
        self.api_hash = "e58c6204a1478da2b764d5fceff846e5"
        
        # Verwende die erfolgreiche User-Session
        self.session_name = "user_telegram_session"
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Überwachte Gruppen
        self.chat_configs = {
            "VIP Signal Group": {"id": -2299206473, "type": "group"},
            "Cryptet Official Channel": {"id": -1001804143400, "type": "channel"}, 
            "PH FUTURES VIP": {"id": -1002773853382, "type": "group"}
        }
        
    async def start_session(self):
        """Starte mit der User-Session"""
        await self.client.start()
        
        # Bestätige User-Login
        me = await self.client.get_me()
        print(f"✅ User-Session aktiv:")
        print(f"   Name: {me.first_name} {me.last_name or ''}")
        print(f"   Username: @{me.username or 'kein_username'}")
        print(f"   ID: {me.id}")
        print(f"   Telefon: {me.phone}")
        
        return True
    
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
    
    async def get_latest_messages(self, chat_id: int, chat_name: str, limit: int = 10) -> List[Dict[str, Any]]:
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
                        "chat_title": getattr(entity, "title", chat_name)
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
                          "TARGET", "STOP", "LOSS", "PROFIT", "LEVERAGE", "🟢", "🔴", "↪️", "🔝"]
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
        if len(text) > 400:
            text = text[:400] + "\n... (gekürzt)"
        
        return f"""
{emoji} {chat_name} | {priority}
📅 {msg.get('date')} | 👤 {sender_info}
🆔 Message ID: {msg.get('id')}
📝 Inhalt:
{text}
{'-' * 70}"""

    async def run_signal_check(self):
        """Führe Signal-Abruf aus"""
        print("🎯 LETZTE SIGNALE AUS TELEGRAM-GRUPPEN")
        print("=" * 70)
        print(f"🔑 Session: {self.session_name}")
        
        try:
            # 1. Starte Session
            await self.start_session()
            
            # 2. Prüfe alle Gruppen
            print(f"\n📋 PRÜFE ZUGRIFF AUF GRUPPEN:")
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
                    messages = await self.get_latest_messages(chat_id, chat_name, 5)
                    if messages:
                        print(f"📨 {len(messages)} Nachrichten abgerufen")
                        all_messages.extend(messages)
                    else:
                        print("❌ Keine Nachrichten abgerufen")
                else:
                    print(f"❌ Zugriff verweigert: {chat_info.get('error')}")
            
            # 3. Zeige Ergebnisse
            if all_messages:
                print(f"\n🎯 ALLE NACHRICHTEN ({len(all_messages)}):")
                print("=" * 70)
                
                # Sortiere nach Datum (neueste zuerst)
                all_messages.sort(key=lambda x: x.get("date", ""), reverse=True)
                
                # Gruppiere nach Signalen und normalen Nachrichten
                signals = []
                normal_messages = []
                
                for msg in all_messages:
                    text = msg.get("text", "").upper()
                    signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN"]
                    if any(keyword in text for keyword in signal_keywords):
                        signals.append(msg)
                    else:
                        normal_messages.append(msg)
                
                # Zeige Signale zuerst
                if signals:
                    print(f"\n🎯 TRADING-SIGNALE ({len(signals)}):")
                    print("-" * 50)
                    for i, signal in enumerate(signals[:5], 1):  # Top 5 Signale
                        chat_name = "Unknown"
                        for name, config in self.chat_configs.items():
                            if signal.get("chat_title", "").lower() in name.lower():
                                chat_name = name
                                break
                        print(f"#{i} {self.format_signal(signal, chat_name)}")
                
                # Zeige normale Nachrichten
                if normal_messages:
                    print(f"\n💬 NORMALE NACHRICHTEN ({len(normal_messages)}):")
                    print("-" * 50)
                    for i, msg in enumerate(normal_messages[:3], 1):  # Top 3
                        chat_name = "Unknown"
                        for name, config in self.chat_configs.items():
                            if msg.get("chat_title", "").lower() in name.lower():
                                chat_name = name
                                break
                        print(f"#{i} {self.format_signal(msg, chat_name)}")
                
                # Zusammenfassung
                print(f"\n📊 ZUSAMMENFASSUNG:")
                print(f"   Gesamte Nachrichten: {len(all_messages)}")
                print(f"   🎯 Trading-Signale: {len(signals)}")
                print(f"   💬 Normale Nachrichten: {len(normal_messages)}")
                print(f"   📋 Verfügbare Gruppen: {len([c for c in self.chat_configs.keys()])}")
                
                # Zeige neueste Nachricht
                if all_messages:
                    latest = all_messages[0]  # Bereits sortiert
                    chat_name = "Unknown"
                    for name, config in self.chat_configs.items():
                        if latest.get("chat_title", "").lower() in name.lower():
                            chat_name = name
                            break
                    
                    print(f"\n🕐 NEUESTE NACHRICHT:")
                    print(self.format_signal(latest, chat_name))
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
    retriever = UserSessionSignalRetriever()
    await retriever.run_signal_check()

if __name__ == "__main__":
    print("🔑 Verwende erfolgreiche User-Session: user_telegram_session")
    print("📱 Account: Schosch (+4915217955921)")
    print()
    
    asyncio.run(main())