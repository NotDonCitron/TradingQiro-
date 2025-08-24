#!/usr/bin/env python3
"""
Erstellt eine Telegram Session für den Docker-Container
"""

import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

async def create_session():
    """Erstellt eine persistente Telegram Session."""
    
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    
    print("🔐 Erstelle Telegram Session für Docker-Container...")
    print(f"📱 API ID: {api_id}")
    print()
    
    # Session im session_files Verzeichnis erstellen
    os.makedirs("session_files", exist_ok=True)
    session_path = "session_files/telegram_receiver"
    
    client = TelegramClient(session_path, api_id, api_hash)
    
    try:
        print("📞 Verbinde mit Telegram...")
        await client.start()
        
        # Test der Verbindung
        me = await client.get_me()
        print(f"✅ Erfolgreich angemeldet als: {me.first_name}")
        if me.username:
            print(f"👤 Username: @{me.username}")
        print(f"📱 Telefon: {me.phone}")
        print()
        
        print(f"💾 Session gespeichert unter: {session_path}.session")
        print("🐳 Diese Session kann jetzt in Docker verwendet werden!")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Session: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TELEGRAM SESSION CREATOR")
    print("=" * 50)
    
    asyncio.run(create_session())