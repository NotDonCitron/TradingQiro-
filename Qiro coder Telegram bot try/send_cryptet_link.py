#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sende einen echten Cryptet-Link, damit das Hauptsystem ihn verarbeitet
"""
import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

async def send_cryptet_link():
    # Verwende die bestehende Session
    client = TelegramClient("user_telegram_session", 
                           int(os.getenv("TELEGRAM_API_ID")), 
                           os.getenv("TELEGRAM_API_HASH"))
    
    try:
        await client.start()
        
        # Zielgruppe
        target_group = int(os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382"))
        
        # Echter Cryptet-Link (wie er im Screenshot gezeigt wird)
        cryptet_link = "https://cryptet.com/signals/one/btc_usdt/2025/08/24/0646?utm_campaign=notification&utm_medium=telegram"
        
        print(f"🔗 Sende Cryptet-Link an Gruppe {target_group}")
        print(f"📎 Link: {cryptet_link}")
        
        # Sende den Link
        await client.send_message(target_group, cryptet_link)
        
        print(f"✅ Cryptet-Link gesendet!")
        print(f"⏳ Das Hauptsystem sollte ihn jetzt automatisch verarbeiten...")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("🧪 CRYPTET-LINK SENDER")
    print("Sendet einen echten Cryptet-Link zur automatischen Verarbeitung")
    print()
    
    asyncio.run(send_cryptet_link())