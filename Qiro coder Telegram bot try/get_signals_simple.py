#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einfaches Script zum Abrufen der letzten Telegram Updates über Bot API
Verwendet nur Standard-Python-Bibliotheken
"""
import json
import os
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class SimpleTelegramBotRetriever:
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
        
    def make_request(self, endpoint: str, params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """Mache eine HTTP-Anfrage an die Telegram Bot API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            
            if params:
                query_string = urllib.parse.urlencode(params)
                url = f"{url}?{query_string}"
            
            if data:
                # POST-Request
                post_data = urllib.parse.urlencode(data).encode('utf-8')
                req = urllib.request.Request(url, data=post_data)
                req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            else:
                # GET-Request
                req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    return result
                else:
                    print(f"❌ HTTP Fehler: {response.status}")
                    
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Fehler: {e.code} - {e.reason}")
            if e.code == 400:
                error_response = e.read().decode('utf-8')
                print(f"   Details: {error_response}")
        except Exception as e:
            print(f"❌ Request Fehler: {e}")
        
        return None
    
    def get_updates(self, limit: int = 100, offset: Optional[int] = None) -> List[Dict]:
        """Hole die letzten Updates über Bot API"""
        params = {"limit": limit}
        if offset:
            params["offset"] = offset
            
        result = self.make_request("getUpdates", params=params)
        if result and result.get("ok"):
            return result.get("result", [])
        
        return []
    
    def get_chat_info(self, chat_id: int) -> Dict[str, Any]:
        """Hole Informationen über einen Chat"""
        result = self.make_request("getChat", params={"chat_id": chat_id})
        if result and result.get("ok"):
            return result.get("result", {})
        
        return {}
    
    def send_test_message(self, chat_id: int, test_text: str = "🤖 Test - Bot ist aktiv!") -> bool:
        """Sende eine Testnachricht, um zu prüfen, ob der Bot Zugriff hat"""
        data = {
            "chat_id": chat_id,
            "text": test_text
        }
        result = self.make_request("sendMessage", data=data)
        return result is not None and result.get("ok", False)
    
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
                          "TARGET", "STOP", "LOSS", "PROFIT", "LEVERAGE", "COIN", "$", "USDT", "BTCUSDT", "ETHUSDT"]
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

def main():
    retriever = SimpleTelegramBotRetriever()
    
    try:
        print("🔍 HOLE TELEGRAM UPDATES UND CHAT-INFORMATIONEN...")
        print("=" * 80)
        
        # Hole Chat-Informationen für alle konfigurierten Chats
        print("\n📋 CHAT-INFORMATIONEN:")
        for chat_name, config in retriever.chat_configs.items():
            chat_id = config["id"]
            print(f"\n>>> {chat_name} (ID: {chat_id}) <<<")
            
            chat_info = retriever.get_chat_info(chat_id)
            if chat_info:
                print(f"✅ Chat-Info abgerufen:")
                print(f"   Titel: {chat_info.get('title', 'Unknown')}")
                print(f"   Typ: {chat_info.get('type', 'unknown')}")
                description = chat_info.get('description', '')
                if description:
                    print(f"   Beschreibung: {description[:100]}...")
                
                # Teste, ob Bot Nachrichten senden kann (nur bei eigener Gruppe)
                if chat_id == -1002773853382:  # Nur bei PH FUTURES VIP testen
                    print(f"🧪 Teste Bot-Zugriff...")
                    test_success = retriever.send_test_message(chat_id, f"🤖 Signal-Abruf Test - {datetime.now().strftime('%H:%M:%S')}")
                    if test_success:
                        print(f"✅ Bot kann Nachrichten an {chat_name} senden")
                    else:
                        print(f"❌ Bot kann KEINE Nachrichten an {chat_name} senden")
            else:
                print("❌ Chat-Info nicht verfügbar - Bot hat möglicherweise keinen Zugriff")
        
        print(f"\n\n🔍 HOLE LETZTE UPDATES...")
        
        # Hole Updates
        updates = retriever.get_updates(limit=100)
        print(f"✅ {len(updates)} Updates abgerufen")
        
        if not updates:
            print("❌ Keine Updates verfügbar")
            print("   💡 Hinweis: Bot muss in den Gruppen aktiv sein und Nachrichten empfangen haben")
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
                    
                    for i, msg in enumerate(chat_messages[:5], 1):  # Zeige die letzten 5
                        print(retriever.format_message(msg, chat_name))
                        if i < len(chat_messages[:5]):
                            print("\n" + "="*50 + "\n")
                else:
                    print(f"\n❌ Keine Nachrichten aus {chat_name} in den letzten Updates")
        else:
            print("❌ Keine Nachrichten aus den überwachten Chats gefunden")
            print("   💡 Mögliche Gründe:")
            print("   - Bot ist nicht Mitglied der Gruppen/Kanäle")
            print("   - Keine neuen Nachrichten seit dem letzten Bot-Neustart")
            print("   - Bot hat keine Berechtigung, Nachrichten zu lesen")
        
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
        
        if chat_id_counts:
            for chat_id, info in sorted(chat_id_counts.items(), key=lambda x: x[1]["count"], reverse=True):
                is_monitored = chat_id in target_chat_ids
                status = "🎯 ÜBERWACHT" if is_monitored else "📍 Nicht überwacht"
                print(f"   {chat_id:>15} | {info['count']:>3} msgs | {info['title']} | {status}")
        else:
            print("   Keine Chat-Nachrichten in den Updates gefunden")
        
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
        
        if len(filtered_messages) == 0:
            print(f"\n💡 NÄCHSTE SCHRITTE:")
            print(f"   1. Stellen Sie sicher, dass der Bot zu allen Gruppen hinzugefügt wurde")
            print(f"   2. Senden Sie eine Testnachricht in die Gruppen")
            print(f"   3. Führen Sie das Skript erneut aus")
        
    except Exception as e:
        print(f"❌ Fehler beim Ausführen des Scripts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()