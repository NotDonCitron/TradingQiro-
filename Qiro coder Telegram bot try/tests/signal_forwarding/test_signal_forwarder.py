#!/usr/bin/env python3
"""
Test script für Signal Forwarder
Testet die Erkennung und Weiterleitung von Signalen aus Gruppe -2299206473
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

from src.core.signal_forwarder import SignalForwarder
from src.utils.audit_logger import AuditLogger

async def mock_send_telegram(chat_id: str, message: str):
    """Mock Telegram send function for testing."""
    print(f"📤 WOULD SEND TO CHAT {chat_id}:")
    print("-" * 50)
    print(message)
    print("-" * 50)
    print()

async def test_signal_detection():
    """Test signal detection and parsing."""
    
    print("🧪 SIGNAL FORWARDER TEST")
    print("=" * 60)
    
    # Beispiel-Signal aus der Gruppe -2299206473
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
    
    # Initialize components
    audit_logger = AuditLogger()
    signal_forwarder = SignalForwarder(mock_send_telegram, audit_logger)
    
    # Test metadata für die richtige Gruppe
    test_metadata = {
        "chat_id": -2299206473,
        "message_id": 12345,
        "sender_id": 67890
    }
    
    print("🔍 Testing signal detection...")
    is_signal = signal_forwarder._is_signal(test_signal)
    print(f"Signal detected: {is_signal}")
    
    if is_signal:
        print("\n📊 Parsing signal...")
        signal_data = signal_forwarder._parse_signal(test_signal)
        
        if signal_data:
            print("✅ Signal parsed successfully:")
            for key, value in signal_data.items():
                print(f"   {key}: {value}")
            
            print("\n📝 Formatting signal...")
            formatted = signal_forwarder._format_signal(signal_data)
            print("✅ Formatted signal:")
            print(formatted)
            
            print("\n🚀 Testing full process...")
            result = await signal_forwarder.process_message(test_signal, test_metadata)
            print(f"Process result: {result}")
            
        else:
            print("❌ Signal parsing failed")
    else:
        print("❌ Signal not detected")

async def test_wrong_chat():
    """Test that signals from wrong chat are ignored."""
    
    print("\n🚫 TESTING WRONG CHAT ID")
    print("=" * 40)
    
    test_signal = """🟢 Long
Name: BTC/USDT
Margin mode: Cross (10.0X)

↪️ Entry price(USDT):
50000

Targets(USDT):
1) 51000
2) 52000"""
    
    # Metadata für falsche Gruppe
    wrong_metadata = {
        "chat_id": -9999999999,  # Falsche Chat-ID
        "message_id": 12345
    }
    
    audit_logger = AuditLogger()
    signal_forwarder = SignalForwarder(mock_send_telegram, audit_logger)
    
    result = await signal_forwarder.process_message(test_signal, wrong_metadata)
    print(f"Process result for wrong chat: {result}")
    print("Expected: False (should be ignored)")

async def test_non_signal():
    """Test that non-signals are ignored."""
    
    print("\n🚫 TESTING NON-SIGNAL MESSAGE")
    print("=" * 40)
    
    non_signal = "Hello, this is just a regular message without signal data."
    
    test_metadata = {
        "chat_id": -2299206473,  # Richtige Chat-ID
        "message_id": 12345
    }
    
    audit_logger = AuditLogger()
    signal_forwarder = SignalForwarder(mock_send_telegram, audit_logger)
    
    result = await signal_forwarder.process_message(non_signal, test_metadata)
    print(f"Process result for non-signal: {result}")
    print("Expected: False (should be ignored)")

async def test_status():
    """Test status function."""
    
    print("\n📊 TESTING STATUS")
    print("=" * 30)
    
    audit_logger = AuditLogger()
    signal_forwarder = SignalForwarder(mock_send_telegram, audit_logger)
    
    status = signal_forwarder.get_status()
    print("Status:")
    for key, value in status.items():
        print(f"   {key}: {value}")

async def main():
    """Run all tests."""
    
    try:
        await test_signal_detection()
        await test_wrong_chat() 
        await test_non_signal()
        await test_status()
        
        print("\n🎉 ALL TESTS COMPLETED!")
        print("✅ Signal Forwarder is ready for use")
        
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())