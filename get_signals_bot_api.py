#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script zum Abrufen der letzten Telegram Updates über Bot API
Funktioniert mit Bot-Token und zeigt letzte Nachrichten aus überwachten Gruppen
"""
import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class TelegramBotSignalRetriever:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN muss in der .env Datei gesetzt sein.")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Konfigurierte Gruppen
        self.chat_configs = {
            "VIP Signal Group": {"id": -2299206473, "type": "group"},
            "Cryptet Official Channel": {"id": -1001804143400, "type": "channel"}, 
            "PH FUTURES VIP": {"id": -1002773853382, "type": "group"}
        }
        
    async def get_updates(self, limit: int = 100, offset: Optional[int] = None) -> List[Dict]:
        """Hole die letzten Updates über Bot API"""
        try:
            params = {"limit": limit}
            if offset:
                params["offset"] = offset
                
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/getUpdates", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return data.get("result", [])
                    else:
                        print(f"❌ HTTP Fehler: {response.status}")
                        
        except Exception as e:
            print(f"❌ Fehler beim Abrufen der Updates: {e}")
        
        return []
    
    async def get_chat_info(self, chat_id: int) -> Dict[str, Any]:
        """Hole Informationen über einen Chat"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/getChat", params={"chat_id": chat_id}) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return data.get("result", {})
                    else:
                        print(f"❌ Chat Info HTTP Fehler für {chat_id}: {response.status}")
                        
        except Exception as e:
            print(f"❌ Fehler beim Abrufen der Chat-Info für {chat_id}: {e}")
        
        return {}
    
    async def send_test_message(self, chat_id: int, test_text: str = "🤖 Test - Bot ist aktiv!") -> bool:
        """Sende eine Testnachricht, um zu prüfen, ob der Bot Zugriff hat"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "chat_id": chat_id,
                    "text": test_text
                }
                async with session.post(f"{self.base_url}/sendMessage", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("ok", False)
                    else:
                        response_text = await response.text()
                        print(f"❌ Testnachricht fehlgeschlagen für {chat_id}: {response.status} - {response_text}")
                        
        except Exception as e:
            print(f"❌ Fehler beim Senden der Testnachricht an {chat_id}: {e}")
        
        return False
    
    def filter_messages_by_chat(self, updates: List[Dict], target_chat_ids: List[int]) -> List[Dict]:
        """Filtere Updates nach bestimmten Chat-IDs"""
        filtered = []
        
        for update in updates:
            message = update.get("message")
            if message:
                chat = message.get("chat", {})
                chat_id = chat.get("id")
                
                if chat_id in target_chat_ids:
                    filtered.append({
                        "update_id": update.get("update_id"),
                        "message_id": message.get("message_id"),
                        "chat_id": chat_id,
                        "chat_title": chat.get("title", "Unknown"),
                        "chat_type": chat.get("type", "unknown"),
                        "text": message.get("text", ""),
                        "date": message.get("date"),
                        "from_user": message.get("from", {}),
                        "raw_update": update
                    })
        
        return filtered
    
    def format_message(self, msg: Dict, chat_name: str) -> str:
        """Formatiere eine Nachricht für die Ausgabe"""
        text = msg.get("text", "")
        
        # Suche nach Signal-Keywords
        signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN", 
                          "TARGET", "STOP", "LOSS", "PROFIT", "LEVERAGE", "COIN", "$", "USDT"]
        is_likely_signal = any(keyword.upper() in text.upper() for keyword in signal_keywords)
        
        emoji = "🎯" if is_likely_signal else "💬"
        
        # Formatiere Datum
        timestamp = msg.get("date", 0)
        date_str = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if timestamp else "Unknown"
        
        # Sender Info
        from_user = msg.get("from_user", {})
        sender_name = from_user.get("first_name", "Unknown")
        sender_username = from_user.get("username")
        if sender_username:
            sender_info = f"{sender_name} (@{sender_username})"
        else:
            sender_info = sender_name
        
        # Kürze lange Nachrichten
        if len(text) > 300:
            text = text[:300] + "\n... (gekürzt)"
        
        return f"""
{emoji} {chat_name} - {msg.get('chat_title', 'Unknown')}
🆔 Message ID: {msg.get('message_id')}
📅 Datum: {date_str}
👤 Von: {sender_info} (ID: {from_user.get('id', 'Unknown')})
🏷️  Chat Type: {msg.get('chat_type', 'unknown')}
📝 Inhalt:
{'-' * 50}
{text}
{'-' * 50}"""

async def main():
    retriever = TelegramBotSignalRetriever()
    
    try:
        print("🔍 HOLE TELEGRAM UPDATES UND CHAT-INFORMATIONEN...")
        print("=" * 80)
        
        # Hole Chat-Informationen für alle konfigurierten Chats
        print("\n📋 CHAT-INFORMATIONEN:")
        for chat_name, config in retriever.chat_configs.items():
            chat_id = config["id"]
            print(f"\n>>> {chat_name} (ID: {chat_id}) <<<")
            
            chat_info = await retriever.get_chat_info(chat_id)
            if chat_info:
                print(f"✅ Chat-Info abgerufen:")
                print(f"   Titel: {chat_info.get('title', 'Unknown')}")
                print(f"   Typ: {chat_info.get('type', 'unknown')}")
                print(f"   Beschreibung: {chat_info.get('description', 'Keine')[:100]}...")
                
                # Teste, ob Bot Nachrichten senden kann
                print(f"🧪 Teste Bot-Zugriff...")
                test_success = await retriever.send_test_message(chat_id, f"🤖 Bot Test - {datetime.now().strftime('%H:%M:%S')}")
                if test_success:
                    print(f"✅ Bot kann Nachrichten an {chat_name} senden")
                else:
                    print(f"❌ Bot kann KEINE Nachrichten an {chat_name} senden")
            else:
                print(f"❌ Chat-Info nicht verfügbar - Bot hat möglicherweise keinen Zugriff")
        
        print(f"\n\n🔍 HOLE LETZTE UPDATES...")
        
        # Hole Updates
        updates = await retriever.get_updates(limit=50)
        print(f"✅ {len(updates)} Updates abgerufen")
        
        if not updates:
            print("❌ Keine Updates verfügbar")
            return
        
        # Filtere Nachrichten aus überwachten Chats
        target_chat_ids = [config["id"] for config in retriever.chat_configs.values()]
        filtered_messages = retriever.filter_messages_by_chat(updates, target_chat_ids)
        
        print(f"🎯 {len(filtered_messages)} Nachrichten aus überwachten Chats gefunden")
        
        if filtered_messages:
            print(f"\n📨 LETZTE NACHRICHTEN AUS ÜBERWACHTEN CHATS:")
            print("=" * 80)
            
            # Gruppiere nach Chat
            messages_by_chat = {}
            for msg in filtered_messages:
                chat_id = msg["chat_id"]
                if chat_id not in messages_by_chat:
                    messages_by_chat[chat_id] = []
                messages_by_chat[chat_id].append(msg)
            
            # Zeige Nachrichten pro Chat
            for chat_name, config in retriever.chat_configs.items():
                chat_id = config["id"]
                chat_messages = messages_by_chat.get(chat_id, [])
                
                if chat_messages:
                    print(f"\n🎯 {chat_name} - {len(chat_messages)} Nachrichten:")
                    print("-" * 60)
                    
                    # Sortiere nach Datum (neueste zuerst)
                    chat_messages.sort(key=lambda x: x.get("date", 0), reverse=True)
                    
                    for i, msg in enumerate(chat_messages[:3], 1):  # Zeige nur die letzten 3
                        print(retriever.format_message(msg, chat_name))
                        if i < len(chat_messages[:3]):
                            print("\n" + "="*50 + "\n")
                else:
                    print(f"\n❌ Keine Nachrichten aus {chat_name} in den letzten Updates")
        else:
            print("❌ Keine Nachrichten aus den überwachten Chats gefunden")
        
        # Zeige alle Updates für Debugging
        print(f"\n\n🔧 DEBUG - ALLE CHAT-IDs IN DEN LETZTEN UPDATES:")
        chat_id_counts = {}
        for update in updates:
            message = update.get("message")
            if message:
                chat_id = message.get("chat", {}).get("id")
                if chat_id:
                    chat_title = message.get("chat", {}).get("title", "Unknown")
                    if chat_id not in chat_id_counts:
                        chat_id_counts[chat_id] = {"count": 0, "title": chat_title}
                    chat_id_counts[chat_id]["count"] += 1
        
        for chat_id, info in sorted(chat_id_counts.items(), key=lambda x: x[1]["count"], reverse=True):
            is_monitored = chat_id in target_chat_ids
            status = "🎯 ÜBERWACHT" if is_monitored else "📍 Nicht überwacht"
            print(f"   {chat_id:>15} | {info['count']:>3} msgs | {info['title']} | {status}")
        
        # Zusammenfassung
        print(f"\n📊 ZUSAMMENFASSUNG:")
        print(f"   Gesamte Updates: {len(updates)}")
        print(f"   Überwachte Chats: {len(retriever.chat_configs)}")
        print(f"   Nachrichten aus überwachten Chats: {len(filtered_messages)}")
        
        # Analysiere auf Signal-Keywords
        signal_count = 0
        for msg in filtered_messages:
            signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN"]
            text = msg.get("text", "")
            if any(keyword.upper() in text.upper() for keyword in signal_keywords):
                signal_count += 1
        
        print(f"   Wahrscheinliche Trading-Signale: {signal_count}")
        
    except Exception as e:
        print(f"❌ Fehler beim Ausführen des Scripts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())