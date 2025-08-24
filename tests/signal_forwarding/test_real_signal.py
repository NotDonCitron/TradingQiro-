#!/usr/bin/env python3
"""
Test script for real Cryptet signal processing
Tests the actual signal from Telegram group
"""

import asyncio
import sys
import os
from pathlib import Path
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_real_cryptet_signal():
    """Test the real Cryptet signal from Telegram group."""
    
    print("🧪 Testing Real Cryptet Signal")
    print("=" * 50)
    
    # The real signal URL from user's Telegram group
    test_url = "https://cryptet.com/de/signals/one/link_usdt/2025/08/24/0330?utm_campaign=notification&utm_medium=telegram"
    
    print(f"📱 Signal URL: {test_url}")
    print()
    
    try:
        # Test API endpoint
        api_url = "http://localhost:8000/cryptet/test"
        payload = {"url": test_url}
        
        print("🌐 Sending test request to API...")
        response = requests.post(api_url, json=payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - Signal processed successfully!")
            print()
            print("📋 Signal Details:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Check if signal was extracted
            if result.get("success") and result.get("signal_data"):
                signal = result["signal_data"]
                print()
                print("🎯 Extracted Signal:")
                print(f"   Symbol: {signal.get('symbol', 'N/A')}")
                print(f"   Direction: {signal.get('direction', 'N/A')}")
                print(f"   Entry Price: {signal.get('entry_price', 'N/A')}")
                print(f"   Leverage: {signal.get('leverage', 'N/A')}x")
                print(f"   Stop Loss: {signal.get('stop_loss', 'N/A')}")
                print(f"   Take Profits: {signal.get('take_profits', 'N/A')}")
                
                # Check if it would be sent to Telegram
                if result.get("telegram_message"):
                    print()
                    print("📤 Telegram Message Preview:")
                    print(result["telegram_message"])
            
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            try:
                error_data = response.json()
                print("Error Details:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print("Raw Response:", response.text)
                
    except requests.exceptions.ConnectionError:
        print("❌ FAILED - Cannot connect to API")
        print("💡 Ensure the server is running: python run.py")
        
    except requests.exceptions.Timeout:
        print("❌ FAILED - Request timeout (>30s)")
        print("💡 The browser might be taking too long to load")
        
    except Exception as e:
        print(f"❌ FAILED - Unexpected error: {e}")
    
    print()
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_real_cryptet_signal())