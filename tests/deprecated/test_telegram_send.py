#!/usr/bin/env python3
"""
Test script to verify Telegram message sending to user's group
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.connectors.telethon_connector import TelethonConnector
from src.core.cryptet_signal_parser import CryptetSignalProcessor

async def test_telegram_send():
    """Test sending a Cryptet signal to the user's Telegram group."""
    
    print("📱 TELEGRAM SEND TEST")
    print("=" * 50)
    
    # Your group ID
    group_id = -2773853382
    print(f"🎯 Target Group ID: {group_id}")
    
    # Create test signal data (LINK/USDT from your example)
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
    
    print("📊 Test Signal Data:")
    for key, value in signal_data.items():
        print(f"   {key}: {value}")
    print()
    
    try:
        # Format the signal
        processor = CryptetSignalProcessor()
        formatted_message = processor.process_signal(signal_data)
        
        print("📝 Formatted Message:")
        print("-" * 30)
        print(formatted_message)
        print("-" * 30)
        print()
        
        # Initialize Telegram connector
        print("🔌 Initializing Telegram connector...")
        telegram = TelethonConnector()
        await telegram.start()
        
        print("✅ Telegram connected successfully!")
        print()
        
        # Send the message
        print(f"📤 Sending message to group {group_id}...")
        await telegram.send_message(group_id, formatted_message)
        
        print("✅ MESSAGE SENT SUCCESSFULLY!")
        print("🎉 Check your Telegram group for the test signal!")
        
        # Clean up
        await telegram.stop()
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Check if TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN are set in .env")
        print("   2. Ensure bot is added to your group and has send message permissions")
        print("   3. Verify group ID is correct (should be negative for groups)")
        print(f"   4. Current group ID: {group_id}")
        
        return False

async def test_group_access():
    """Test if we can access the group and get its info."""
    
    print("\n🔍 GROUP ACCESS TEST")
    print("=" * 50)
    
    group_id = -2773853382
    
    try:
        telegram = TelethonConnector()
        await telegram.start()
        
        # Try to get group info
        print(f"📋 Getting info for group {group_id}...")
        
        # Send a simple test message
        test_message = "🧪 **CRYPTET AUTOMATION TEST**\n\nThis is a test message to verify the bot can send messages to this group.\n\n✅ If you see this, the integration is working!"
        
        await telegram.send_message(group_id, test_message)
        
        print("✅ Group access successful!")
        print("🎯 Test message sent to verify bot permissions")
        
        await telegram.stop()
        return True
        
    except Exception as e:
        print(f"❌ Group access failed: {e}")
        return False

async def main():
    """Run all tests."""
    
    print("🧪 CRYPTET TELEGRAM INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Group access
    group_test = await test_group_access()
    
    if group_test:
        # Test 2: Signal sending
        signal_test = await test_telegram_send()
        
        if signal_test:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Cryptet signals will be automatically forwarded to your group")
        else:
            print("\n⚠️  Signal formatting test failed")
    else:
        print("\n❌ Group access test failed")
        print("💡 Please check bot permissions and group ID")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")