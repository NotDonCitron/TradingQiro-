#!/usr/bin/env python3
# Test script for Cryptet Signal Automation System

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.connectors.cryptet_scraper import CryptetScraper
from src.core.cryptet_link_handler import CryptetLinkHandler
from src.core.cryptet_signal_parser import CryptetSignalProcessor
from src.utils.cookie_parser import CookieParser

async def test_cookie_parser():
    """Test cookie parsing functionality."""
    print("🍪 Testing Cookie Parser...")
    
    parser = CookieParser("cookies.txt")
    cookies = parser.get_cryptet_cookies()
    
    if cookies:
        print(f"✅ Found {len(cookies)} cookies for cryptet.com")
        for cookie in cookies[:3]:  # Show first 3 cookies
            print(f"   - {cookie['name']}: {cookie['value'][:20]}...")
        return True
    else:
        print("❌ No cookies found for cryptet.com")
        return False

async def test_link_detection():
    """Test Cryptet link detection."""
    print("\n🔗 Testing Link Detection...")
    
    handler = CryptetLinkHandler()
    
    test_messages = [
        "Check this signal: https://cryptet.com/signal/123456",
        "New signal at cryptet.com/trade/abcdef",
        "Regular message without cryptet link",
        "Multiple links: https://cryptet.com/a and https://cryptet.com/b"
    ]
    
    for msg in test_messages:
        is_cryptet = handler.is_cryptet_link(msg)
        url = handler.extract_cryptet_url(msg)
        print(f"   Message: {msg[:50]}...")
        print(f"   Cryptet: {is_cryptet}, URL: {url}")
    
    return True

async def test_signal_formatter():
    """Test signal formatting."""
    print("\n📊 Testing Signal Formatter...")
    
    processor = CryptetSignalProcessor()
    
    # Mock signal data
    test_signal = {
        'symbol': 'BTCUSDT',
        'direction': 'LONG',
        'entry_price': '45000.00',
        'stop_loss': '44000.00',
        'take_profits': ['46000.00', '47000.00', '48000.00'],
        'leverage': 50,
        'source': 'cryptet',
        'url': 'https://cryptet.com/signal/test'
    }
    
    formatted = processor.process_signal(test_signal)
    
    if formatted:
        print("✅ Signal formatted successfully:")
        print(formatted[:200] + "...")
        return True
    else:
        print("❌ Signal formatting failed")
        return False

async def test_browser_init():
    """Test browser initialization."""
    print("\n🌐 Testing Browser Initialization...")
    
    try:
        scraper = CryptetScraper(headless=True)
        success = await scraper.initialize_browser()
        
        if success:
            print("✅ Browser initialized successfully")
            await scraper.close()
            return True
        else:
            print("❌ Browser initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        return False

async def test_config():
    """Test configuration."""
    print("\n⚙️ Testing Configuration...")
    
    required_files = ["cookies.txt", ".env"]
    required_env = ["OWN_GROUP_CHAT_ID", "TELEGRAM_BOT_TOKEN"]
    
    # Check files
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} found")
        else:
            print(f"⚠️  {file} not found (may be optional)")
    
    # Check environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    for env_var in required_env:
        value = os.getenv(env_var)
        if value:
            print(f"✅ {env_var} configured")
        else:
            print(f"⚠️  {env_var} not configured")
    
    return True

async def main():
    """Run all tests."""
    print("🧪 Cryptet Automation System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_config),
        ("Cookie Parser", test_cookie_parser),
        ("Link Detection", test_link_detection),
        ("Signal Formatter", test_signal_formatter),
        ("Browser Init", test_browser_init),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Tests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All tests passed! System is ready.")
    else:
        print("⚠️  Some tests failed. Please check configuration.")
    
    return passed == len(results)

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        sys.exit(1)