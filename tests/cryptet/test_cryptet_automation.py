#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test der Cryptet-Automation: Sende einen echten Cryptet-Link an das System
"""
import asyncio
import os
from datetime import datetime
from telethon import TelegramClient
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class CryptetAutomationTester:
    def __init__(self):
        # API Credentials
        api_id_str = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        
        if not (api_id_str and api_hash):
            raise RuntimeError("TELEGRAM_API_ID und TELEGRAM_API_HASH müssen gesetzt sein.")
        
        # Verwende die bestehende User-Session
        self.session_name = "user_telegram_session"
        self.client = TelegramClient(self.session_name, int(api_id_str), api_hash)
        
        # Zielgruppe für das Senden
        self.target_group_id = int(os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382"))
        
        # Beispiel Cryptet-Links (aus den Screenshots)
        self.test_links = [
            "https://cryptet.com/signals/one/btc_usdt/2025/08/24/0646?utm_campaign=notification&utm_medium=telegram",
            "https://cryptet.com/signals/one/eth_usdt/2025/08/24/0554?utm_campaign=notification&utm_medium=telegram", 
            "https://cryptet.com/signals/one/doge_usdt/2025/08/24/0523?utm_campaign=notification&utm_medium=telegram"
        ]
        
    async def start_session(self):
        """Starte die Test-Session"""
        try:
            await self.client.start()
            
            # Bestätige Login
            me = await self.client.get_me()
            print(f"✅ Test-Session aktiv:")
            print(f"   Name: {me.first_name} {me.last_name or ''}")
            print(f"   ID: {me.id}")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Starten der Session: {e}")
            return False
    
    async def send_test_cryptet_links(self):
        """Sende Test-Cryptet-Links an die Gruppe"""
        print(f"\n🧪 TESTE CRYPTET-AUTOMATION")
        print("=" * 50)
        print(f"🎯 Zielgruppe: {self.target_group_id}")
        print(f"🔗 Anzahl Test-Links: {len(self.test_links)}")
        
        try:
            # Sende Header
            header_msg = f"""🧪 **CRYPTET-AUTOMATION TEST**

🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
🎯 Teste automatische Link-Verarbeitung

Die folgenden Links sollten automatisch verarbeitet werden:"""
            
            await self.client.send_message(self.target_group_id, header_msg)
            print(f"✅ Header gesendet")
            await asyncio.sleep(2)
            
            # Sende jeden Cryptet-Link einzeln
            for i, link in enumerate(self.test_links, 1):
                try:
                    # Simuliere eine echte Cryptet-Nachricht
                    symbol = link.split('/')[-2].replace('_', '/').upper()
                    message = f"[{symbol}]({link})"
                    
                    await self.client.send_message(self.target_group_id, message)
                    print(f"✅ Test-Link {i}/{len(self.test_links)} gesendet: {symbol}")
                    
                    # Pause zwischen Links (wie echte Cryptet-Nachrichten)
                    if i < len(self.test_links):
                        await asyncio.sleep(5)
                        
                except Exception as e:
                    print(f"❌ Fehler beim Senden von Link {i}: {e}")
                    continue
            
            # Sende Hinweis
            await asyncio.sleep(3)
            footer_msg = f"""ℹ️ **TEST ABGESCHLOSSEN**

✅ {len(self.test_links)} Cryptet-Links gesendet
⏳ Das Hauptsystem sollte diese automatisch verarbeiten:

1. 🌐 Browser öffnet die Links
2. 📊 Signale werden gescrapt
3. ⚡ 50x Leverage wird hinzugefügt
4. 📤 Formatierte Signale werden gesendet

Erwarte in wenigen Sekunden die formatierten Signale!"""
            
            await self.client.send_message(self.target_group_id, footer_msg)
            print(f"✅ Test abgeschlossen")
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Senden der Test-Links: {e}")
            return False
    
    async def run_test(self):
        """Führe den kompletten Test aus"""
        print("🧪 CRYPTET-AUTOMATION TESTER")
        print("=" * 60)
        print("Testet die automatische Verarbeitung von Cryptet-Links")
        print(f"🕐 Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Starte Session
            if not await self.start_session():
                print("❌ Session konnte nicht gestartet werden")
                return False
            
            # 2. Sende Test-Links
            success = await self.send_test_cryptet_links()
            
            if success:
                print(f"\n✅ TEST ERFOLGREICH!")
                print(f"   📤 {len(self.test_links)} Cryptet-Links gesendet")
                print(f"   🎯 Hauptsystem sollte sie automatisch verarbeiten")
                print(f"   ⏳ Prüfen Sie die Gruppe auf formatierte Signale!")
            else:
                print(f"\n❌ TEST FEHLGESCHLAGEN!")
            
            return success
            
        except Exception as e:
            print(f"❌ Fehler während des Tests: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            await self.client.disconnect()
            print("\n✅ Test-Session beendet")

async def main():
    tester = CryptetAutomationTester()
    success = await tester.run_test()
    
    if success:
        print("\n🎉 TEST ABGESCHLOSSEN!")
        print("Das Hauptsystem sollte die Links jetzt automatisch verarbeiten.")
        print("Prüfen Sie die Gruppe auf die formatierten Signale!")
    else:
        print("\n⚠️ TEST UNVOLLSTÄNDIG!")

if __name__ == "__main__":
    print("🧪 CRYPTET-AUTOMATION TESTER")
    print("Sendet echte Cryptet-Links an das System zur automatischen Verarbeitung")
    print()
    
    asyncio.run(main())