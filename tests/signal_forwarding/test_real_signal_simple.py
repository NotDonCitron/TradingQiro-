#!/usr/bin/env python3
import requests
import json

# Test the real Cryptet signal
url = "https://cryptet.com/de/signals/one/link_usdt/2025/08/24/0330?utm_campaign=notification&utm_medium=telegram"

print("🔥 TESTING REAL CRYPTET SIGNAL")
print("=" * 50)
print(f"URL: {url}")
print()

try:
    response = requests.post(
        "http://localhost:8000/cryptet/test",
        json={"url": url},
        timeout=60
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS!")
        print()
        
        if "signal_data" in data:
            signal = data["signal_data"]
            print("📊 EXTRACTED SIGNAL:")
            print(f"   Symbol: {signal.get('symbol', 'N/A')}")
            print(f"   Direction: {signal.get('direction', 'N/A')}")
            print(f"   Entry: {signal.get('entry_price', 'N/A')}")
            print(f"   Take Profit: {signal.get('take_profits', 'N/A')}")
            print(f"   Stop Loss: {signal.get('stop_loss', 'N/A')}")
            print(f"   Leverage: {signal.get('leverage', 'N/A')}x")
        
        if "telegram_message" in data:
            print()
            print("📤 TELEGRAM MESSAGE:")
            print(data["telegram_message"])
            
        if "metadata" in data:
            print()
            print("🔧 METADATA:")
            meta = data["metadata"]
            print(f"   Processing Time: {meta.get('processing_time_ms', 'N/A')}ms")
            print(f"   Browser Used: {meta.get('browser_used', 'N/A')}")
    else:
        print("❌ FAILED")
        try:
            error_data = response.json()
            print("Error Details:")
            print(json.dumps(error_data, indent=2))
        except:
            print("Raw Response:", response.text)
            
except Exception as e:
    print(f"❌ ERROR: {e}")

print()
print("=" * 50)