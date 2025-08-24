#!/usr/bin/env python3
"""
Sendet zwei Testsignale - VIP Style und Cryptet Style
"""

import asyncio
import os
from telethon import TelegramClient
from datetime import datetime

# Telegram Konfiguration aus .env
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "26708757"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "e58c6204a1478da2b764d5fceff846e5")
TARGET_GROUP_ID = int(os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382"))

async def send_test_signals():
    """Sendet beide Testsignale an die Zielgruppe."""
    
    # VIP-Gruppen-Stil Signal (Original Format aus der VIP Gruppe)
    vip_signal = """🟢 Long
Name: BTC/USDT

Margin mode: Cross (50X)
Entry zone(USDT):
98000.0

Entry price(USDT):
98025.5

Targets(USDT):
1) 98500.0
2) 99000.0
3) 99500.0
4) 100000.0

Stop loss(USDT): 97200.0

💡 Risk management is key to successful trading."""

    # Cryptet-Stil Signal (Cornix-kompatibles Format)
    cryptet_signal = """🟢 #BTC/USDT LONG Cross 50x

↪️ Entry: 98025.5

🎯 Target 1: 98500.0
🎯 Target 2: 99000.0  
🎯 Target 3: 99500.0
🎯 Target 4: 100000.0
🔝 unlimited

🛑 Stop Loss: 97200.0

⚠️ Risk: 2% of portfolio"""

    client = TelegramClient('test_signals_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    try:
        await client.start()
        print("✅ Telegram Client verbunden")
        
        # Sende VIP-Stil Signal
        print(f"\n📤 Sende VIP-Stil Testsignal an Gruppe {TARGET_GROUP_ID}...")
        await client.send_message(TARGET_GROUP_ID, f"🧪 **TEST VIP SIGNAL** - {datetime.now().strftime('%H:%M:%S')}\n\n{vip_signal}")
        print("✅ VIP-Stil Signal gesendet")
        
        # Kurze Pause
        await asyncio.sleep(2)
        
        # Sende Cryptet-Stil Signal  
        print(f"\n📤 Sende Cryptet-Stil Testsignal an Gruppe {TARGET_GROUP_ID}...")
        await client.send_message(TARGET_GROUP_ID, f"🧪 **TEST CRYPTET SIGNAL** - {datetime.now().strftime('%H:%M:%S')}\n\n{cryptet_signal}")
        print("✅ Cryptet-Stil Signal gesendet")
        
        print(f"\n🎉 Beide Testsignale erfolgreich an Gruppe {TARGET_GROUP_ID} gesendet!")
        
    except Exception as e:
        print(f"❌ Fehler beim Senden: {e}")
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("🚀 Starte Testsignal-Versendung...")
    print(f"🎯 Zielgruppe: {TARGET_GROUP_ID}")
    
    asyncio.run(send_test_signals())