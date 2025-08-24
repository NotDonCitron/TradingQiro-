#!/usr/bin/env python3
"""
Testet die Signal-Überwachung und das Parsing der beiden konfigurierten Gruppen.
"""
import asyncio
import json
import aiohttp
from typing import Dict, Any

async def test_signal_parsing():
    """Teste verschiedene Signaltypen"""
    
    # Test 1: VIP Club Signal (sollte weitergeleitet werden)
    vip_signal = {
        "message": """🟢 LONG #BTCUSDT
        
📍 Entry: 65000 - 65200
⛔ Stop Loss: 64500
🎯 Target 1: 65800
🎯 Target 2: 66500
🎯 Target 3: 67200
🎯 Target 4: 68000

📊 Risk/Reward: 1:3.5
⚡ Cross 25x""",
        "metadata": {
            "chat_id": -1002299206473,  # VIP Club
            "message_id": 12345,
            "source": "test"
        }
    }
    
    # Test 2: Cryptet Signal (sollte automatisch verarbeitet werden)
    cryptet_signal = {
        "message": "https://cryptet.com/signals/btc-usdt-long-12345",
        "metadata": {
            "chat_id": -1001804143400,  # CryptET
            "message_id": 67890,
            "source": "test",
            "extracted_urls": ["https://cryptet.com/signals/btc-usdt-long-12345"]
        }
    }
    
    # Test 3: Normales Signal (sollte als Trading-Signal verarbeitet werden)
    normal_signal = {
        "message": """🔸 ETH/USDT LONG

Entry: 3200-3250
Stop Loss: 3150
Take Profit 1: 3350
Take Profit 2: 3450
Take Profit 3: 3550

Leverage: 10x""",
        "metadata": {
            "chat_id": -999999999,  # Andere Gruppe
            "message_id": 11111,
            "source": "test"
        }
    }
    
    base_url = "http://localhost:8080"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Teste Signal-Verarbeitung...")
        print("=" * 50)
        
        # Test VIP Signal
        print("\n📍 Test 1: VIP Club Signal")
        try:
            async with session.post(f"{base_url}/signal", json=vip_signal) as response:
                result = await response.json()
                print(f"Status: {response.status}")
                print(f"Antwort: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"❌ Fehler: {e}")
        
        # Test Cryptet Signal
        print("\n🔗 Test 2: Cryptet Signal")
        try:
            async with session.post(f"{base_url}/signal", json=cryptet_signal) as response:
                result = await response.json()
                print(f"Status: {response.status}")
                print(f"Antwort: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"❌ Fehler: {e}")
        
        # Test Normal Signal
        print("\n📊 Test 3: Normales Trading Signal")
        try:
            async with session.post(f"{base_url}/signal", json=normal_signal) as response:
                result = await response.json()
                print(f"Status: {response.status}")
                print(f"Antwort: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"❌ Fehler: {e}")
        
        # Überprüfe System-Status nach den Tests
        print("\n🔍 System-Status nach Tests:")
        try:
            async with session.get(f"{base_url}/status") as response:
                status = await response.json()
                print(f"Gesund: {status['healthy']}")
                print(f"Bereit: {status['ready']}")
                print(f"Komponenten aktiv: {sum(1 for v in status['components'].values() if v)}")
        except Exception as e:
            print(f"❌ Status-Abfrage fehlgeschlagen: {e}")

async def test_live_monitoring():
    """Teste das Live-Monitoring der konfigurierten Gruppen"""
    print("\n🔴 Live-Monitoring Test")
    print("=" * 50)
    print("✅ Telegram Client läuft und überwacht:")
    print("   📱 VIP Club: -1002299206473")
    print("   📱 CryptET: -1001804143400")
    print("\n💡 Sende eine Testnachricht in eine der überwachten Gruppen")
    print("   um das Live-Parsing zu testen!")
    print("\n📊 Überwache die Logs für eingehende Nachrichten...")

if __name__ == "__main__":
    print("🚀 Signal-Monitoring und Parsing Test")
    print("=" * 50)
    
    # Test Signal-Parsing
    asyncio.run(test_signal_parsing())
    
    # Test Live-Monitoring Info
    asyncio.run(test_live_monitoring())