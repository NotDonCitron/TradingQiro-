#!/usr/bin/env python3
"""
Test script using Telegram Bot API (HTTP) instead of Telethon
"""

import asyncio
import requests
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.cryptet_signal_parser import CryptetSignalProcessor

def send_telegram_message(bot_token: str, chat_id: int, message: str) -> bool:
    """Send message via Telegram Bot API."""
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

async def main():
    """Test Telegram Bot API sending."""
    
    print("🤖 TELEGRAM BOT API TEST")
    print("=" * 50)
    
    # Get credentials
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    group_id = -1002773853382  # Correct group ID found!
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env")
        return
    
    print(f"🎯 Bot Token: {bot_token[:10]}...")
    print(f"🎯 Group ID: {group_id}")
    print()
    
    # Create test signal
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
    
    # Format signal
    processor = CryptetSignalProcessor()
    formatted_message = processor.process_signal(signal_data)
    
    print("📝 Test Message:")
    print("-" * 30)
    print(formatted_message)
    print("-" * 30)
    print()
    
    # Send simple test first
    print("📤 Sending simple test message...")
    simple_test = "🧪 **CRYPTET AUTOMATION TEST**\\n\\nBot ist erfolgreich mit Ihrer Gruppe verbunden!\\n\\n✅ Integration funktioniert!"
    
    success = send_telegram_message(bot_token, group_id, simple_test)
    
    if success:
        print("✅ Simple test message sent successfully!")
        print()
        
        # Send the formatted signal
        print("📤 Sending formatted Cryptet signal...")
        signal_success = send_telegram_message(bot_token, group_id, formatted_message)
        
        if signal_success:
            print("🎉 SIGNAL SENT SUCCESSFULLY!")
            print("✅ Check your Telegram group for both messages!")
        else:
            print("❌ Failed to send formatted signal")
    else:
        print("❌ Failed to send simple test message")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Check if bot is added to your group")
        print("   2. Give bot admin rights or 'Send Messages' permission")
        print("   3. Verify group ID is correct")
        print(f"   4. Current group ID: {group_id}")
        print("   5. Try sending a message to the bot first to activate it")

if __name__ == "__main__":
    asyncio.run(main())