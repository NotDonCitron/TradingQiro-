#!/usr/bin/env python3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.cryptet_signal_parser import CryptetSignalProcessor

# Manual signal data from user's Cryptet link
signal_data = {
    'symbol': 'LINKUSDT',
    'direction': 'LONG',
    'entry_price': '25.69',
    'take_profits': ['26.03'],
    'stop_loss': '25.27',
    'leverage': 50,
    'source': 'cryptet',
    'url': 'https://cryptet.com/de/signals/one/link_usdt/2025/08/24/0330'
}

print("🚀 CRYPTET SIGNAL AUTOMATION DEMO")
print("=" * 60)
print("📱 Original Signal aus Telegram:")
print("   LINK/USDT")
print("   Kaufen bei: 25.69")
print("   Take Profit: 26.03") 
print("   Stop Loss: 25.27")
print("   Direction: LONG (Kaufen)")
print()
print("🤖 Automatisch formatierte Telegram-Nachricht:")
print("=" * 60)

processor = CryptetSignalProcessor()
formatted_message = processor.process_signal(signal_data)

print(formatted_message)

print("=" * 60)
print("✅ Das Signal würde automatisch mit 50x Leverage")
print("   an Ihre eigene Telegram-Gruppe weitergeleitet!")