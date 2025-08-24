#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Login mit Telegram User API über Code aus der Telegram App
Telefonnummer: +4915217955921
"""
import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

async def login_with_telegram_code():
    # API Credentials
    api_id = 26708757
    api_hash = "e58c6204a1478da2b764d5fceff846e5"
    phone = "+4915217955921"
    
    # Neue Session erstellen
    session_name = "user_telegram_session"
    
    # Lösche alte Session falls vorhanden
    if os.path.exists(f"{session_name}.session"):
        os.remove(f"{session_name}.session")
        print(f"🗑️ Alte Session gelöscht: {session_name}.session")
    
    client = TelegramClient(session_name, api_id, api_hash)
    
    try:
        print("🔑 TELEGRAM USER API LOGIN")
        print("=" * 50)
        print(f"📱 Telefonnummer: {phone}")
        print(f"🔑 API ID: {api_id}")
        print(f"📁 Session: {session_name}")
        print()
        
        # Starte Client
        await client.start()
        
        print("🚀 Sende Login-Code-Anfrage...")
        
        # Sende Code-Anfrage
        sent = await client.send_code_request(phone)
        print(f"✅ Code-Anfrage gesendet!")
        print(f"   Code-Hash: {sent.phone_code_hash[:20]}...")
        print()
        print("📱 SCHAUEN SIE JETZT IN IHRE TELEGRAM APP!")
        print("   Sie sollten einen Bestätigungscode erhalten haben")
        print("   (NICHT per SMS, sondern direkt in Telegram)")
        print()
        
        # Code vom User abfragen
        while True:
            try:
                code = input("🔢 Geben Sie den Code aus Telegram ein: ").strip()
                
                if not code:
                    print("❌ Kein Code eingegeben. Versuchen Sie es erneut.")
                    continue
                
                print(f"🔄 Versuche Login mit Code: {code}")
                
                # Versuche Login mit Code
                await client.sign_in(phone, code)
                print("✅ LOGIN ERFOLGREICH!")
                break
                
            except PhoneCodeInvalidError:
                print("❌ Ungültiger Code. Bitte versuchen Sie es erneut.")
                print("   Schauen Sie noch einmal in Ihre Telegram App.")
                continue
            except SessionPasswordNeededError:
                print("🔒 Zwei-Faktor-Authentifizierung aktiviert.")
                password = input("🔑 Geben Sie Ihr 2FA-Passwort ein: ").strip()
                await client.sign_in(password=password)
                print("✅ 2FA LOGIN ERFOLGREICH!")
                break
            except Exception as e:
                print(f"❌ Login-Fehler: {e}")
                continue
        
        # Teste die Session
        print("\n🧪 TESTE SESSION...")
        me = await client.get_me()
        print(f"✅ Erfolgreich eingeloggt als:")
        print(f"   Name: {me.first_name} {me.last_name or ''}")
        print(f"   Username: @{me.username or 'kein_username'}")
        print(f"   ID: {me.id}")
        print(f"   Telefon: {me.phone}")
        
        # Teste Chat-Zugriff
        print(f"\n🎯 TESTE ZUGRIFF AUF ÜBERWACHTE GRUPPEN...")
        
        groups = {
            "VIP Signal Group": -2299206473,
            "Cryptet Official Channel": -1001804143400,
            "PH FUTURES VIP": -1002773853382
        }
        
        working_groups = []
        
        for group_name, group_id in groups.items():
            try:
                print(f"\n>>> {group_name} (ID: {group_id}) <<<")
                entity = await client.get_entity(group_id)
                print(f"✅ Zugriff erfolgreich: {entity.title}")
                
                # Teste Nachrichten abrufen
                message_count = 0
                async for message in client.iter_messages(entity, limit=3):
                    if message.text:
                        message_count += 1
                        if message_count == 1:  # Zeige erste Nachricht als Beispiel
                            preview = message.text[:50] + "..." if len(message.text) > 50 else message.text
                            date_str = message.date.strftime("%Y-%m-%d %H:%M") if message.date else "Unknown"
                            print(f"   📨 Letzte Nachricht [{date_str}]: {preview}")
                
                print(f"   📊 {message_count} Nachrichten verfügbar")
                working_groups.append((group_name, group_id))
                
            except Exception as e:
                print(f"❌ Zugriff fehlgeschlagen: {str(e)[:100]}...")
        
        print(f"\n📊 ERGEBNIS:")
        print(f"   ✅ Session erstellt: {session_name}.session")
        print(f"   📱 User: {me.first_name} (@{me.username or 'N/A'})")
        print(f"   🎯 Verfügbare Gruppen: {len(working_groups)}/{len(groups)}")
        
        for group_name, group_id in working_groups:
            print(f"      ✅ {group_name}")
        
        if len(working_groups) == len(groups):
            print(f"\n🎉 PERFEKT! Alle Gruppen sind zugänglich!")
            print(f"   Sie können jetzt das System mit der User-Session verwenden.")
        else:
            print(f"\n⚠️ Nicht alle Gruppen sind zugänglich.")
            print(f"   Das System kann trotzdem mit den verfügbaren Gruppen arbeiten.")
        
        return session_name
        
    except Exception as e:
        print(f"❌ Fehler beim Login: {e}")
        return None
        
    finally:
        await client.disconnect()

async def main():
    print("🔐 TELEGRAM USER API LOGIN")
    print("Verwenden Sie den Code aus Ihrer Telegram App, NICHT SMS!")
    print()
    
    session_name = await login_with_telegram_code()
    
    if session_name:
        print(f"\n✅ Session erfolgreich erstellt: {session_name}.session")
        print(f"   Sie können diese Session nun für das Hauptsystem verwenden.")
    else:
        print(f"\n❌ Login fehlgeschlagen.")

if __name__ == "__main__":
    asyncio.run(main())