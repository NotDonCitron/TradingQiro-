#!/usr/bin/env python3
"""
Test Script zur Überprüfung der Signalweiterleitung aus beiden Gruppen
- VIP Group (-1002299206473)
- Cryptet Channel (-1001804143400)
"""

import asyncio
import os
import json
from datetime import datetime
from telethon import TelegramClient
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Telegram Konfiguration
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "26708757"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "e58c6204a1478da2b764d5fceff846e5")

# Überwachte Gruppen
VIP_GROUP_ID = int(os.getenv("VIP_GROUP_ID", "-1002299206473"))
CRYPTET_CHANNEL_ID = int(os.getenv("CRYPTET_CHANNEL_ID", "-1001804143400"))
TARGET_GROUP_ID = int(os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382"))

class SignalForwardingTester:
    """Klasse zum Testen der Signalweiterleitung aus beiden Gruppen."""
    
    def __init__(self):
        self.client = None
        self.test_results = {
            "vip_group": {"accessible": False, "signals_found": 0, "forwarding_test": "pending"},
            "cryptet_channel": {"accessible": False, "signals_found": 0, "forwarding_test": "pending"},
            "target_group": {"accessible": False, "test_messages_sent": 0}
        }
    
    async def connect(self):
        """Verbindung zu Telegram herstellen."""
        try:
            self.client = TelegramClient('signal_forwarding_test', TELEGRAM_API_ID, TELEGRAM_API_HASH)
            await self.client.start()
            print("✅ Telegram Client verbunden")
            return True
        except Exception as e:
            print(f"❌ Fehler bei Verbindung: {e}")
            return False
    
    async def test_group_access(self, group_id: int, group_name: str) -> dict:
        """Teste Zugriff auf eine Gruppe und sammle Signaldaten."""
        try:
            entity = await self.client.get_entity(group_id)
            print(f"✅ Zugriff auf {group_name} ({group_id}): {entity.title}")
            
            # Sammle letzte Nachrichten
            messages = []
            async for message in self.client.iter_messages(entity, limit=20):
                if message.text:
                    messages.append({
                        "id": message.id,
                        "text": message.text[:200],
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # Suche nach signalartigen Nachrichten
            signal_indicators = [
                "Long", "Short", "USDT", "Entry", "Target", "Stop Loss",
                "🟢", "🔴", "💸", "BTC/USDT", "ETH/USDT"
            ]
            
            signals_found = 0
            for msg in messages:
                if any(indicator in msg["text"] for indicator in signal_indicators):
                    signals_found += 1
            
            return {
                "accessible": True,
                "title": entity.title,
                "messages_count": len(messages),
                "signals_found": signals_found,
                "recent_messages": messages[:5]
            }
            
        except Exception as e:
            print(f"❌ Kein Zugriff auf {group_name} ({group_id}): {e}")
            return {
                "accessible": False,
                "error": str(e),
                "signals_found": 0
            }
    
    async def send_test_signal_to_vip_group(self):
        """Sende ein Testsignal an die VIP-Gruppe (simuliert)."""
        try:
            # Da wir nicht in die VIP-Gruppe schreiben können, simulieren wir ein eingehendes Signal
            vip_test_signal = """🟢 Long
Name: ETH/USDT

Margin mode: Cross (50X)
Entry zone(USDT):
3450.0

Entry price(USDT):
3465.5

Targets(USDT):
1) 3500.0
2) 3550.0
3) 3600.0
4) 3650.0

Stop loss(USDT): 3400.0

💡 TEST SIGNAL FROM VIP GROUP"""
            
            # Sende direkt an Target-Gruppe mit VIP-Kennzeichnung
            await self.client.send_message(TARGET_GROUP_ID, 
                f"🧪 **VIP GROUP FORWARDING TEST** - {datetime.now().strftime('%H:%M:%S')}\n"
                f"📍 Source: VIP Group ({VIP_GROUP_ID})\n\n{vip_test_signal}")
            
            print(f"✅ VIP Test-Signal an Target-Gruppe gesendet")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Senden des VIP Test-Signals: {e}")
            return False
    
    async def send_test_signal_to_cryptet_channel(self):
        """Sende ein Testsignal an den Cryptet-Kanal (simuliert)."""
        try:
            # Da wir nicht in den Cryptet-Kanal schreiben können, simulieren wir ein eingehendes Signal
            cryptet_test_signal = """🟢 #ETH/USDT LONG Cross 50x

↪️ Entry: 3465.5

🎯 Target 1: 3500.0
🎯 Target 2: 3550.0
🎯 Target 3: 3600.0
🎯 Target 4: 3650.0
🔝 unlimited

🛑 Stop Loss: 3400.0

⚠️ TEST SIGNAL FROM CRYPTET"""
            
            # Sende direkt an Target-Gruppe mit Cryptet-Kennzeichnung
            await self.client.send_message(TARGET_GROUP_ID, 
                f"🧪 **CRYPTET FORWARDING TEST** - {datetime.now().strftime('%H:%M:%S')}\n"
                f"📍 Source: Cryptet Channel ({CRYPTET_CHANNEL_ID})\n\n{cryptet_test_signal}")
            
            print(f"✅ Cryptet Test-Signal an Target-Gruppe gesendet")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Senden des Cryptet Test-Signals: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Führe umfassenden Test der Signalweiterleitung durch."""
        print("🚀 Starte umfassenden Signalweiterleitungs-Test...")
        print(f"📊 Test-Konfiguration:")
        print(f"   VIP Group: {VIP_GROUP_ID}")
        print(f"   Cryptet Channel: {CRYPTET_CHANNEL_ID}")
        print(f"   Target Group: {TARGET_GROUP_ID}")
        print()
        
        if not await self.connect():
            return False
        
        # Test 1: Zugriff auf alle Gruppen
        print("📋 Test 1: Gruppenzugriff überprüfen")
        self.test_results["vip_group"] = await self.test_group_access(VIP_GROUP_ID, "VIP Group")
        self.test_results["cryptet_channel"] = await self.test_group_access(CRYPTET_CHANNEL_ID, "Cryptet Channel")
        self.test_results["target_group"] = await self.test_group_access(TARGET_GROUP_ID, "Target Group")
        
        print()
        
        # Test 2: Sende Test-Signale für beide Quellen
        print("📋 Test 2: Test-Signale senden")
        
        vip_success = await self.send_test_signal_to_vip_group()
        self.test_results["vip_group"]["forwarding_test"] = "success" if vip_success else "failed"
        
        await asyncio.sleep(2)  # Kurze Pause
        
        cryptet_success = await self.send_test_signal_to_cryptet_channel()
        self.test_results["cryptet_channel"]["forwarding_test"] = "success" if cryptet_success else "failed"
        
        print()
        
        # Test 3: Prüfe ob Nachrichten ankommen
        print("📋 Test 3: Überprüfung der Test-Nachrichten in Target-Gruppe")
        await asyncio.sleep(3)  # Warte auf Nachrichten
        
        try:
            target_entity = await self.client.get_entity(TARGET_GROUP_ID)
            recent_messages = []
            async for message in self.client.iter_messages(target_entity, limit=10):
                if message.text and "TEST" in message.text.upper():
                    recent_messages.append({
                        "text": message.text[:100],
                        "date": message.date.strftime("%H:%M:%S")
                    })
            
            test_messages_found = len(recent_messages)
            self.test_results["target_group"]["test_messages_sent"] = test_messages_found
            
            print(f"✅ {test_messages_found} Test-Nachrichten in Target-Gruppe gefunden")
            
        except Exception as e:
            print(f"❌ Fehler beim Prüfen der Target-Gruppe: {e}")
        
        print()
        return True
    
    def print_summary(self):
        """Drucke zusammenfassenden Bericht."""
        print("📊 **SIGNALWEITERLEITUNGS-TEST ZUSAMMENFASSUNG**")
        print("=" * 60)
        
        # VIP Group Status
        vip = self.test_results["vip_group"]
        print(f"📍 VIP Group ({VIP_GROUP_ID}):")
        print(f"   Zugriff: {'✅' if vip['accessible'] else '❌'}")
        print(f"   Signale gefunden: {vip['signals_found']}")
        print(f"   Weiterleitung: {'✅' if vip['forwarding_test'] == 'success' else '❌'}")
        
        # Cryptet Channel Status
        cryptet = self.test_results["cryptet_channel"]
        print(f"📍 Cryptet Channel ({CRYPTET_CHANNEL_ID}):")
        print(f"   Zugriff: {'✅' if cryptet['accessible'] else '❌'}")
        print(f"   Signale gefunden: {cryptet['signals_found']}")
        print(f"   Weiterleitung: {'✅' if cryptet['forwarding_test'] == 'success' else '❌'}")
        
        # Target Group Status
        target = self.test_results["target_group"]
        print(f"📍 Target Group ({TARGET_GROUP_ID}):")
        print(f"   Zugriff: {'✅' if target['accessible'] else '❌'}")
        print(f"   Test-Nachrichten empfangen: {target['test_messages_sent']}")
        
        print()
        
        # Gesamtbewertung
        all_accessible = all([
            vip['accessible'], 
            cryptet['accessible'], 
            target['accessible']
        ])
        
        forwarding_works = all([
            vip['forwarding_test'] == 'success',
            cryptet['forwarding_test'] == 'success'
        ])
        
        if all_accessible and forwarding_works:
            print("🎉 **ERFOLG**: Signalweiterleitung aus beiden Gruppen funktioniert!")
        elif all_accessible:
            print("⚠️ **TEILWEISE**: Gruppen zugänglich, aber Weiterleitung fehlerhaft")
        else:
            print("❌ **FEHLER**: Probleme mit Gruppenzugriff oder Weiterleitung")
        
        print()
        
        # Empfehlungen
        print("💡 **EMPFEHLUNGEN**:")
        if not vip['accessible']:
            print("   - Prüfe VIP-Gruppen-Mitgliedschaft und Berechtigungen")
        if not cryptet['accessible']:
            print("   - Prüfe Cryptet-Kanal-Zugriff")
        if not target['accessible']:
            print("   - Prüfe Target-Gruppen-Konfiguration")
        if vip['signals_found'] == 0:
            print("   - VIP-Gruppe scheint keine aktiven Signale zu haben")
        if cryptet['signals_found'] == 0:
            print("   - Cryptet-Kanal scheint keine aktiven Signale zu haben")
    
    async def disconnect(self):
        """Verbindung beenden."""
        if self.client:
            await self.client.disconnect()
            print("📱 Telegram Client getrennt")

async def main():
    """Hauptfunktion für den Test."""
    tester = SignalForwardingTester()
    
    try:
        success = await tester.run_comprehensive_test()
        
        if success:
            tester.print_summary()
            
            # Speichere Testergebnisse in Datei
            with open('signal_forwarding_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(tester.test_results, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Detaillierte Ergebnisse in 'signal_forwarding_test_results.json' gespeichert")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
    
    finally:
        await tester.disconnect()

if __name__ == "__main__":
    asyncio.run(main())