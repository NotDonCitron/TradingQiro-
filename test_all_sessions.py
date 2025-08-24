#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste alle verfügbaren Sessions und finde User-Sessions (nicht Bot-Sessions)
"""
import asyncio
import os
from telethon import TelegramClient

async def test_session(session_name):
    """Teste eine einzelne Session"""
    api_id = 26708757
    api_hash = "e58c6204a1478da2b764d5fceff846e5"
    
    client = TelegramClient(session_name, api_id, api_hash)
    
    try:
        await client.start()
        me = await client.get_me()
        
        # Prüfe ob es ein Bot oder User ist
        is_bot = getattr(me, 'bot', False)
        session_type = "BOT" if is_bot else "USER"
        
        print(f"✅ {session_name}:")
        print(f"   Typ: {session_type}")
        print(f"   Name: {me.first_name} {me.last_name or ''}")
        print(f"   Username: @{me.username or 'kein_username'}")
        print(f"   ID: {me.id}")
        print(f"   Telefon: {me.phone or 'nicht verfügbar'}")
        
        # Teste Chat-Zugriff nur bei User-Sessions
        if not is_bot:
            print(f"   🧪 Teste Chat-Zugriff...")
            try:
                # Teste Zugriff auf PH FUTURES VIP
                entity = await client.get_entity(-1002773853382)
                print(f"   ✅ Zugriff auf PH FUTURES VIP: {entity.title}")
                
                # Teste Nachrichten abrufen
                message_count = 0
                async for message in client.iter_messages(entity, limit=3):
                    if message.text:
                        message_count += 1
                
                print(f"   ✅ Kann {message_count} Nachrichten abrufen")
                return session_name, True  # Diese Session funktioniert
                
            except Exception as e:
                print(f"   ❌ Chat-Zugriff fehlgeschlagen: {str(e)[:100]}...")
        
        return session_name, False
        
    except Exception as e:
        print(f"❌ {session_name}: Fehler - {str(e)[:100]}...")
        return session_name, False
        
    finally:
        await client.disconnect()

async def main():
    print("🔍 TESTE ALLE VERFÜGBAREN SESSIONS")
    print("=" * 60)
    
    # Finde alle Session-Dateien
    session_files = []
    for file in os.listdir("."):
        if file.endswith(".session"):
            session_name = file[:-8]  # Entferne .session
            session_files.append(session_name)
    
    print(f"📁 Gefundene Sessions: {session_files}")
    print()
    
    working_sessions = []
    
    for session_name in session_files:
        print(f"🔍 Teste {session_name}...")
        session_name, works = await test_session(session_name)
        if works:
            working_sessions.append(session_name)
        print("-" * 40)
    
    print(f"\n📊 ERGEBNIS:")
    print(f"   Gesamte Sessions: {len(session_files)}")
    print(f"   Funktionierende User-Sessions: {working_sessions}")
    
    if working_sessions:
        print(f"\n🎯 VERWENDE SESSION: {working_sessions[0]}")
        return working_sessions[0]
    else:
        print(f"\n❌ Keine funktionierende User-Session gefunden!")
        return None

if __name__ == "__main__":
    asyncio.run(main())