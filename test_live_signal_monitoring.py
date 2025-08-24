#!/usr/bin/env python3
"""
Testet die Live-Signal-Überwachung durch Senden einer Testnachricht an die konfigurierten Gruppen.
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any

async def simulate_vip_signal():
    """Simuliere ein Signal aus der VIP-Gruppe"""
    # Signal aus -1002299206473 (VIP Club) sollte weitergeleitet werden
    vip_signal = {
        "message": """🟢 LONG #SOLUSDT
        
📍 Entry: 180.5 - 182.0
⛔ Stop Loss: 175.0
🎯 Target 1: 186.0
🎯 Target 2: 190.5
🎯 Target 3: 195.0
🎯 Target 4: 200.0

📊 Risk/Reward: 1:4.2
⚡ Cross 50x""",
        "metadata": {
            "chat_id": -1002299206473,  # VIP Club - sollte weitergeleitet werden
            "message_id": 99999,
            "source": "live_test"
        }
    }
    
    print("🚀 Teste VIP-Signal-Weiterleitung...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("http://localhost:8080/signal", json=vip_signal) as response:
                result = await response.json()
                print(f"📊 VIP Signal Status: {response.status}")
                print(f"📝 Antwort: {json.dumps(result, indent=2)}")
                
                if result.get("status") == "success":
                    print("✅ VIP-Signal erfolgreich verarbeitet!")
                    order_id = result.get("order_id")
                    if order_id:
                        print(f"🏷️  Order ID: {order_id}")
                else:
                    print("❌ VIP-Signal-Verarbeitung fehlgeschlagen")
                    
        except Exception as e:
            print(f"❌ Fehler beim VIP-Signal-Test: {e}")

async def simulate_cryptet_signal():
    """Simuliere ein Cryptet-Signal"""
    # Signal aus -1001804143400 (CryptET) sollte durch CryptetAutomation verarbeitet werden
    cryptet_signal = {
        "message": "https://cryptet.com/signals/eth-usdt-short-test-signal",
        "metadata": {
            "chat_id": -1001804143400,  # CryptET Channel
            "message_id": 88888,
            "source": "live_test",
            "extracted_urls": ["https://cryptet.com/signals/eth-usdt-short-test-signal"]
        }
    }
    
    print("\n🔗 Teste Cryptet-Signal-Verarbeitung...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("http://localhost:8080/signal", json=cryptet_signal) as response:
                result = await response.json()
                print(f"📊 Cryptet Signal Status: {response.status}")
                print(f"📝 Antwort: {json.dumps(result, indent=2)}")
                
                # Bei Cryptet-Signalen wird erwartet, dass sie von CryptetAutomation verarbeitet werden
                if result.get("status") == "success":
                    print("✅ Cryptet-Signal erfolgreich verarbeitet!")
                elif "failed" in result.get("status", ""):
                    print("🔄 Cryptet-Signal wird von CryptetAutomation verarbeitet (normal)")
                    
        except Exception as e:
            print(f"❌ Fehler beim Cryptet-Signal-Test: {e}")

async def check_forwarder_status():
    """Überprüfe den Status des Signal Forwarders"""
    print("\n📡 Überprüfe Signal Forwarder Status...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8080/forwarder/status") as response:
                result = await response.json()
                print(f"Status: {json.dumps(result, indent=2)}")
                
                if result.get("status", {}).get("enabled"):
                    print("✅ Signal Forwarder ist aktiv")
                    print(f"📱 Überwacht Chat: {result.get('monitored_chat')}")
                    print(f"🎯 Zielgruppe: {result.get('target_group')}")
                else:
                    print("❌ Signal Forwarder ist nicht aktiv")
                    
        except Exception as e:
            print(f"❌ Fehler bei Forwarder-Status-Abfrage: {e}")

async def check_cryptet_status():
    """Überprüfe den Status der Cryptet-Automation"""
    print("\n🤖 Überprüfe Cryptet-Automation Status...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8080/cryptet/status") as response:
                result = await response.json()
                print(f"Status: {json.dumps(result, indent=2)}")
                
                status = result.get("status", {})
                if status.get("initialized") and status.get("running"):
                    print("✅ Cryptet-Automation ist aktiv")
                    print(f"📊 Aktive Signale: {result.get('active_count', 0)}")
                else:
                    print("❌ Cryptet-Automation ist nicht vollständig aktiv")
                    
        except Exception as e:
            print(f"❌ Fehler bei Cryptet-Status-Abfrage: {e}")

async def main():
    """Führe alle Live-Tests aus"""
    print("=" * 60)
    print("🔥 LIVE SIGNAL MONITORING TEST")
    print("=" * 60)
    print("📋 Übersicht der konfigurierten Gruppen:")
    print("   📱 VIP Club: -1002299206473 (Signal-Weiterleitung)")
    print("   📱 CryptET: -1001804143400 (Cryptet-Automation)")
    print("=" * 60)
    
    # 1. System-Status überprüfen
    await check_forwarder_status()
    await check_cryptet_status()
    
    # 2. VIP-Signal testen
    await simulate_vip_signal()
    
    # 3. Cryptet-Signal testen
    await simulate_cryptet_signal()
    
    print("\n" + "=" * 60)
    print("✅ Live-Tests abgeschlossen!")
    print("💡 Das System überwacht nun kontinuierlich die beiden Gruppen.")
    print("📊 Sende echte Nachrichten in die Gruppen, um Live-Verarbeitung zu testen!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())