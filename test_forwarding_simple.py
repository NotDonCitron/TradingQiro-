#!/usr/bin/env python3
"""
Einfacher Test für Signalweiterleitung aus beiden Gruppen
Nutzt bestehende Session-Datei
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from telethon import TelegramClient
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Add src path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Telegram Konfiguration
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "26708757"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "e58c6204a1478da2b764d5fceff846e5")

# Überwachte Gruppen
VIP_GROUP_ID = int(os.getenv("VIP_GROUP_ID", "-1002299206473"))
CRYPTET_CHANNEL_ID = int(os.getenv("CRYPTET_CHANNEL_ID", "-1001804143400"))
TARGET_GROUP_ID = int(os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382"))

async def test_signal_forwarding():
    """Teste die Signalweiterleitung aus beiden Gruppen."""
    
    print("🔍 **SIGNALWEITERLEITUNGS-TEST**")
    print("=" * 50)
    print(f"VIP Group: {VIP_GROUP_ID}")
    print(f"Cryptet Channel: {CRYPTET_CHANNEL_ID}")
    print(f"Target Group: {TARGET_GROUP_ID}")
    print()
    
    # Nutze bestehende Session-Datei
    session_files = [
        'signal_forwarding_test.session',
        'test_signals_session.session',
        'anon.session'
    ]
    
    client = None
    session_used = None
    
    for session_file in session_files:
        if os.path.exists(session_file):
            try:
                client = TelegramClient(session_file.replace('.session', ''), TELEGRAM_API_ID, TELEGRAM_API_HASH)
                await client.start()
                session_used = session_file
                print(f"✅ Session '{session_file}' erfolgreich geladen")
                break
            except Exception as e:
                print(f"❌ Fehler mit Session '{session_file}': {e}")
                if client:
                    await client.disconnect()
                client = None
    
    if not client:
        print("❌ Keine verwendbare Session gefunden")
        return False
    
    try:
        # Test 1: Prüfe Zugriff auf alle Gruppen
        print("\n📋 Test 1: Gruppenzugriff")
        groups_info = {}
        
        for group_id, name in [(VIP_GROUP_ID, "VIP Group"), 
                              (CRYPTET_CHANNEL_ID, "Cryptet Channel"), 
                              (TARGET_GROUP_ID, "Target Group")]:
            try:
                entity = await client.get_entity(group_id)
                
                # Sammle letzte Nachrichten
                message_count = 0
                signal_count = 0
                async for message in client.iter_messages(entity, limit=10):
                    message_count += 1
                    if message.text and any(keyword in message.text for keyword in 
                                          ["Long", "Short", "USDT", "🟢", "Target", "Entry"]):
                        signal_count += 1
                
                groups_info[group_id] = {
                    "accessible": True,
                    "title": entity.title,
                    "messages": message_count,
                    "signals": signal_count
                }
                print(f"✅ {name}: '{entity.title}' - {message_count} Nachrichten, {signal_count} Signale")
                
            except Exception as e:
                groups_info[group_id] = {"accessible": False, "error": str(e)}
                print(f"❌ {name}: Kein Zugriff ({e})")
        
        # Test 2: Sende Testsignale
        print(f"\n📋 Test 2: Testsignale senden an Target Group")
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # VIP-Style Signal
        vip_signal = f"""🧪 **TEST: VIP SIGNAL FORWARDING** - {timestamp}
📍 Source: VIP Group ({VIP_GROUP_ID})

🟢 Long
Name: BTC/USDT

Margin mode: Cross (50X)
Entry zone(USDT):
97500.0

Entry price(USDT):
97625.5

Targets(USDT):
1) 98000.0
2) 98500.0
3) 99000.0
4) 99500.0

Stop loss(USDT): 97000.0

💡 VIP TEST SIGNAL - Forwarding Check"""
        
        # Cryptet-Style Signal
        cryptet_signal = f"""🧪 **TEST: CRYPTET SIGNAL FORWARDING** - {timestamp}
📍 Source: Cryptet Channel ({CRYPTET_CHANNEL_ID})

🟢 #BTC/USDT LONG Cross 50x

↪️ Entry: 97625.5

🎯 Target 1: 98000.0
🎯 Target 2: 98500.0
🎯 Target 3: 99000.0
🎯 Target 4: 99500.0
🔝 unlimited

🛑 Stop Loss: 97000.0

⚠️ CRYPTET TEST SIGNAL - Forwarding Check"""
        
        # Sende beide Signale
        try:
            await client.send_message(TARGET_GROUP_ID, vip_signal)
            print("✅ VIP Test-Signal gesendet")
            
            await asyncio.sleep(2)
            
            await client.send_message(TARGET_GROUP_ID, cryptet_signal)
            print("✅ Cryptet Test-Signal gesendet")
            
        except Exception as e:
            print(f"❌ Fehler beim Senden: {e}")
        
        # Test 3: Überprüfe ob Nachrichten angekommen sind
        print(f"\n📋 Test 3: Überprüfung der gesendeten Signale")
        await asyncio.sleep(3)
        
        try:
            target_entity = await client.get_entity(TARGET_GROUP_ID)
            test_messages = []
            
            async for message in client.iter_messages(target_entity, limit=10):
                if message.text and "TEST:" in message.text and timestamp in message.text:
                    test_messages.append({
                        "time": message.date.strftime("%H:%M:%S"),
                        "type": "VIP" if "VIP SIGNAL" in message.text else "CRYPTET" if "CRYPTET SIGNAL" in message.text else "UNKNOWN",
                        "preview": message.text[:100] + "..."
                    })
            
            print(f"✅ {len(test_messages)} Testnachrichten erfolgreich empfangen:")
            for msg in test_messages:
                print(f"   📨 {msg['type']} Signal um {msg['time']}")
            
        except Exception as e:
            print(f"❌ Fehler beim Prüfen der Nachrichten: {e}")
        
        # Zusammenfassung
        print(f"\n📊 **ZUSAMMENFASSUNG**")
        print("=" * 30)
        
        vip_accessible = groups_info.get(VIP_GROUP_ID, {}).get("accessible", False)
        cryptet_accessible = groups_info.get(CRYPTET_CHANNEL_ID, {}).get("accessible", False)
        target_accessible = groups_info.get(TARGET_GROUP_ID, {}).get("accessible", False)
        
        print(f"VIP Group Zugriff: {'✅' if vip_accessible else '❌'}")
        print(f"Cryptet Channel Zugriff: {'✅' if cryptet_accessible else '❌'}")
        print(f"Target Group Zugriff: {'✅' if target_accessible else '❌'}")
        
        if vip_accessible:
            vip_signals = groups_info[VIP_GROUP_ID].get("signals", 0)
            print(f"VIP Group Signale: {vip_signals}")
        
        if cryptet_accessible:
            cryptet_signals = groups_info[CRYPTET_CHANNEL_ID].get("signals", 0)
            print(f"Cryptet Channel Signale: {cryptet_signals}")
        
        # Speichere Ergebnisse
        results = {
            "timestamp": datetime.now().isoformat(),
            "session_used": session_used,
            "groups": groups_info,
            "test_signals_sent": 2,
            "summary": {
                "all_groups_accessible": vip_accessible and cryptet_accessible and target_accessible,
                "vip_group_ok": vip_accessible,
                "cryptet_channel_ok": cryptet_accessible,
                "target_group_ok": target_accessible
            }
        }
        
        with open('signal_forwarding_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detaillierte Ergebnisse in 'signal_forwarding_results.json' gespeichert")
        
        if results["summary"]["all_groups_accessible"]:
            print(f"\n🎉 **ERFOLG**: Alle Gruppen zugänglich - Signalweiterleitung sollte funktionieren!")
        else:
            print(f"\n⚠️ **WARNUNG**: Nicht alle Gruppen zugänglich - Prüfe Konfiguration!")
        
        return True
        
    finally:
        await client.disconnect()
        print(f"\n📱 Verbindung getrennt")

if __name__ == "__main__":
    asyncio.run(test_signal_forwarding())