#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zeige die letzten Signale, die vom System empfangen wurden
Nutzt Telegram Bot API und zeigt Updates
"""
import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from typing import List, Dict

def get_bot_updates(bot_token: str, limit: int = 50) -> List[Dict]:
    """Hole Updates über Bot API"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        params = {"limit": limit, "offset": -limit}  # Die letzten Updates
        
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        with urllib.request.urlopen(full_url, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data.get("ok"):
                    return data.get("result", [])
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Updates: {e}")
    
    return []

def format_update(update: Dict) -> str:
    """Formatiere ein Update für die Anzeige"""
    message = update.get("message", {})
    if not message:
        return None
    
    text = message.get("text", "")
    if not text.strip():
        return None
    
    # Chat Info
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    chat_title = chat.get("title", "Private Chat")
    chat_type = chat.get("type", "unknown")
    
    # Sender Info
    from_user = message.get("from", {})
    sender_name = from_user.get("first_name", "Unknown")
    sender_username = from_user.get("username")
    if sender_username:
        sender_info = f"{sender_name} (@{sender_username})"
    else:
        sender_info = sender_name
    
    # Datum
    timestamp = message.get("date", 0)
    date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "Unknown"
    
    # Signal-Erkennung
    signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN", 
                      "TARGET", "LEVERAGE", "🟢", "🔴", "↪️", "🔝"]
    is_signal = any(keyword.upper() in text.upper() for keyword in signal_keywords)
    emoji = "🎯" if is_signal else "💬"
    
    # Prüfe, ob es einer der überwachten Chats ist
    monitored_chats = {
        -2299206473: "VIP Signal Group",
        -1001804143400: "Cryptet Official Channel", 
        -1002773853382: "PH FUTURES VIP"
    }
    
    chat_name = monitored_chats.get(chat_id, f"Chat {chat_id}")
    is_monitored = chat_id in monitored_chats
    
    # Kürze lange Nachrichten
    if len(text) > 200:
        text = text[:200] + "..."
    
    status = "🎯 ÜBERWACHT" if is_monitored else "📍 Nicht überwacht"
    
    return f"""
{emoji} {chat_name} | {status}
📅 {date_str} | 👤 {sender_info}
🆔 Chat: {chat_id} ({chat_type}) | Message: {message.get('message_id')}
📝 {text}
{'-' * 60}"""

def main():
    # Bot Token aus Umgebung
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN nicht in Umgebung gesetzt")
        return
    
    print("🔍 LADE LETZTE BOT-UPDATES")
    print("=" * 60)
    print(f"🤖 Bot Token: {bot_token[:20]}...")
    print()
    
    # Hole Updates
    updates = get_bot_updates(bot_token, limit=30)
    
    if not updates:
        print("❌ Keine Updates gefunden")
        print("💡 Hinweise:")
        print("   - Bot muss zu den Gruppen hinzugefügt sein")
        print("   - Nachrichten müssen seit Bot-Start gesendet worden sein")
        print("   - Bot benötigt Berechtigung zum Lesen von Nachrichten")
        return
    
    print(f"✅ {len(updates)} Updates gefunden")
    print()
    
    # Verarbeite und gruppiere Updates
    monitored_updates = []
    other_updates = []
    
    monitored_chat_ids = [-2299206473, -1001804143400, -1002773853382]
    
    for update in updates:
        message = update.get("message", {})
        if message and message.get("text"):
            chat_id = message.get("chat", {}).get("id")
            if chat_id in monitored_chat_ids:
                monitored_updates.append(update)
            else:
                other_updates.append(update)
    
    # Zeige Updates aus überwachten Chats
    if monitored_updates:
        print("🎯 NACHRICHTEN AUS ÜBERWACHTEN CHATS:")
        print("=" * 60)
        
        # Sortiere nach Datum (neueste zuerst)
        monitored_updates.sort(key=lambda x: x.get("message", {}).get("date", 0), reverse=True)
        
        for i, update in enumerate(monitored_updates[:10], 1):  # Top 10
            formatted = format_update(update)
            if formatted:
                print(f"#{i} {formatted}")
    else:
        print("❌ Keine Nachrichten aus überwachten Chats gefunden")
    
    # Zeige andere Updates (weniger Details)
    if other_updates:
        print(f"\n💬 ANDERE NACHRICHTEN ({len(other_updates)}):")
        print("-" * 40)
        
        for i, update in enumerate(other_updates[:5], 1):  # Top 5
            formatted = format_update(update)
            if formatted:
                print(f"#{i} {formatted}")
    
    # Zusammenfassung
    print(f"\n📊 ZUSAMMENFASSUNG:")
    print(f"   Gesamte Updates: {len(updates)}")
    print(f"   Überwachte Chats: {len(monitored_updates)}")
    print(f"   Andere Chats: {len(other_updates)}")
    
    # Analysiere Signale
    signal_count = 0
    for update in monitored_updates:
        message = update.get("message", {})
        text = message.get("text", "")
        signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN"]
        if any(keyword.upper() in text.upper() for keyword in signal_keywords):
            signal_count += 1
    
    print(f"   Wahrscheinliche Signale: {signal_count}")
    
    if len(monitored_updates) == 0:
        print(f"\n⚠️ KEINE ÜBERWACHTEN NACHRICHTEN GEFUNDEN")
        print(f"   Das bedeutet:")
        print(f"   1. Bot ist möglicherweise nicht in den Gruppen")
        print(f"   2. Keine neuen Nachrichten seit Bot-Start")
        print(f"   3. Bot hat keine Leseberechtigungen")
        print(f"\n💡 Lösungsvorschläge:")
        print(f"   1. Bot zu allen Gruppen hinzufügen")
        print(f"   2. Eine Testnachricht in die Gruppen senden")
        print(f"   3. Das Hauptsystem starten: python src/main.py")

if __name__ == "__main__":
    # Lade .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    main()