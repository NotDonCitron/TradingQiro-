#!/usr/bin/env python3
"""
Test script für echte Signal-Weiterleitung
Sendet ein Test-Signal an die Telegram-Gruppe
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
from src.core.signal_forwarder import SignalForwarder
from src.utils.audit_logger import AuditLogger

async def test_real_signal_forwarding():
    """Test real signal forwarding to Telegram group."""
    
    print("📱 REAL SIGNAL FORWARDING TEST")
    print("=" * 60)
    
    # Example signal from group -2299206473
    test_signal = """🟢 Long
Name: API3/USDT
Margin mode: Cross (25.0X)

↪️ Entry price(USDT):
1.4619

Targets(USDT):
1) 1.4765
2) 1.4911
3) 1.5058
4) 1.5204
5) 🔝 unlimited"""
    
    print("📥 Test Signal:")
    print(test_signal)
    print()
    
    try:
        # Initialize Telegram connector
        print("🔌 Initializing Telegram connector...")
        telegram = TelethonConnector()
        await telegram.start()
        print("✅ Telegram connected!")
        
        # Create send callback function
        async def send_telegram_message(chat_id: str, message: str):
            await telegram.send_message(int(chat_id), message)
            print(f"✅ Message sent to chat {chat_id}")
        
        # Initialize SignalForwarder
        audit_logger = AuditLogger()
        signal_forwarder = SignalForwarder(send_telegram_message, audit_logger)
        
        # Test metadata (as if from group -2299206473)
        test_metadata = {
            "chat_id": -2299206473,
            "message_id": 12345,
            "sender_id": 67890,
            "timestamp": "2025-08-24T04:45:00Z"
        }
        
        print("🚀 Processing signal and forwarding to group...")
        result = await signal_forwarder.process_message(test_signal, test_metadata)
        
        if result:
            print("✅ SIGNAL SUCCESSFULLY FORWARDED!")
            print("🎉 Check your Telegram group for the forwarded signal!")
        else:
            print("❌ Signal forwarding failed")
        
        # Clean up
        await telegram.stop()
        
        return result
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_status():
    """Test the API endpoint for forwarder status."""
    
    print("\\n🌐 TESTING API STATUS")
    print("=" * 40)
    
    import requests
    
    try:
        # Test API endpoint
        response = requests.get("http://localhost:8000/forwarder/status", timeout=5)
        
        if response.status_code == 200:
            status_data = response.json()
            print("✅ API Status OK")
            print("Status Data:")
            for key, value in status_data.items():
                print(f"   {key}: {value}")
        else:
            print(f"⚠️  API Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  API not running. Start with: python run.py")
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    try:
        result = asyncio.run(test_real_signal_forwarding())
        
        if result:
            print("\\n" + "=" * 60)
            print("🎯 SIGNAL FORWARDER IS READY!")
            print("✅ The system will now automatically:")
            print("   1. Monitor group -2299206473 for signals")
            print("   2. Parse and format the signals")
            print("   3. Forward them to your group")
            print("\\n💡 Start the main system with: python run.py")
        
    except KeyboardInterrupt:
        print("\\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\\n💥 Test failed: {e}")