#!/usr/bin/env python3
"""
Test des echten Cryptet-Signals mit vollständiger Integration
"""

import requests
import json
import time

def test_real_cryptet_signal():
    """Test the real LINK/USDT signal from Cryptet group."""
    
    print("🔥 LIVE TEST: ECHTES CRYPTET SIGNAL")
    print("=" * 60)
    
    # Das echte Signal aus der Cryptet-Gruppe
    signal_url = "https://cryptet.com/de/signals/one/link_usdt/2025/08/24/0330?utm_campaign=notification&utm_medium=telegram"
    
    print(f"📱 Signal URL: {signal_url}")
    print(f"🎯 Erwartetes Signal: LINK/USDT LONG")
    print(f"💰 Entry: 25.69 | TP: 26.03 | SL: 25.27")
    print(f"⚡ Leverage: 50x (automatisch hinzugefügt)")
    print(f"📤 Ziel-Gruppe: PH FUTURES VIP (-1002773853382)")
    print()
    
    # Test 1: Server Health Check
    print("🏥 1. Server Health Check...")
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            print("   ✅ Server läuft erfolgreich")
        else:
            print(f"   ❌ Server Probleme: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Server nicht erreichbar: {e}")
        return False
    
    # Test 2: Cryptet Status
    print("🤖 2. Cryptet System Status...")
    try:
        status_response = requests.get("http://localhost:8000/cryptet/status", timeout=5)
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"   ✅ Cryptet System: {status_data.get('status', 'unknown')}")
            print(f"   📊 Browser: {status_data.get('browser_status', 'unknown')}")
        else:
            print(f"   ⚠️  Cryptet Status: {status_response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Cryptet Status nicht abrufbar: {e}")
    
    print()
    
    # Test 3: Signal Processing
    print("📊 3. Signal Verarbeitung...")
    print("   🌐 Browser wird gestartet...")
    print("   🍪 Cookies werden geladen...")
    print("   📄 Seite wird geparst...")
    print()
    
    try:
        # API Call zum Signal-Test
        test_payload = {"url": signal_url}
        
        print("📤 Sende Signal an API...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/cryptet/test",
            json=test_payload,
            timeout=120  # 2 Minuten Timeout für Browser-Operationen
        )
        
        processing_time = time.time() - start_time
        print(f"⏱️  Verarbeitungszeit: {processing_time:.2f}s")
        print()
        
        if response.status_code == 200:
            result = response.json()
            
            print("🎉 SIGNAL ERFOLGREICH VERARBEITET!")
            print("-" * 40)
            
            # Signal Details anzeigen
            if result.get("success") and result.get("signal_data"):
                signal = result["signal_data"]
                
                print("📋 EXTRAHIERTE DATEN:")
                print(f"   Symbol: {signal.get('symbol', 'N/A')}")
                print(f"   Direction: {signal.get('direction', 'N/A')}")
                print(f"   Entry: {signal.get('entry_price', 'N/A')}")
                print(f"   Take Profits: {signal.get('take_profits', 'N/A')}")
                print(f"   Stop Loss: {signal.get('stop_loss', 'N/A')}")
                print(f"   Leverage: {signal.get('leverage', 'N/A')}x")
                print()
                
                # Telegram Message
                if result.get("telegram_message"):
                    print("📱 TELEGRAM NACHRICHT:")
                    print("-" * 30)
                    print(result["telegram_message"])
                    print("-" * 30)
                    print()
                
                # Status
                if result.get("forwarded_to_telegram"):
                    print("✅ Signal wurde erfolgreich an Telegram-Gruppe weitergeleitet!")
                    print("🎯 Gruppe: PH FUTURES VIP")
                else:
                    print("⚠️  Signal wurde verarbeitet, aber nicht an Telegram gesendet")
                
                print()
                
                # Metadata
                if result.get("metadata"):
                    meta = result["metadata"]
                    print("🔧 TECHNISCHE DETAILS:")
                    print(f"   Verarbeitungszeit: {meta.get('processing_time_ms', 'N/A')}ms")
                    print(f"   Browser verwendet: {meta.get('browser_used', 'N/A')}")
                    print(f"   Seite geladen: {meta.get('page_loaded', 'N/A')}")
                
            else:
                print("⚠️  Signal-Extraktion fehlgeschlagen")
                print(f"Grund: {result.get('reason', 'Unbekannt')}")
                
                # Fallback: Manuell verarbeitetes Signal senden
                print()
                print("🔄 FALLBACK: Manuell verarbeitetes Signal...")
                
                manual_signal = {
                    'symbol': 'LINKUSDT',
                    'direction': 'LONG',
                    'entry_price': '25.69',
                    'take_profits': ['26.03'],
                    'stop_loss': '25.27',
                    'leverage': 50,
                    'source': 'cryptet_manual',
                    'url': signal_url
                }
                
                # Sende manuelles Signal an Telegram
                try:
                    from dotenv import load_dotenv
                    import os
                    
                    load_dotenv()
                    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
                    group_id = -1002773853382
                    
                    # Formatiere das Signal
                    import sys
                    sys.path.insert(0, 'src')
                    from src.core.cryptet_signal_parser import CryptetSignalProcessor
                    
                    processor = CryptetSignalProcessor()
                    formatted_message = processor.process_signal(manual_signal)
                    
                    # Sende via Bot API
                    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    telegram_payload = {
                        'chat_id': group_id,
                        'text': formatted_message,
                        'parse_mode': 'Markdown'
                    }
                    
                    telegram_response = requests.post(telegram_url, json=telegram_payload, timeout=10)
                    
                    if telegram_response.status_code == 200:
                        print("✅ Manuelles Signal erfolgreich gesendet!")
                    else:
                        print(f"❌ Telegram-Sending fehlgeschlagen: {telegram_response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Fallback fehlgeschlagen: {e}")
                
        else:
            print(f"❌ API FEHLER: {response.status_code}")
            try:
                error_data = response.json()
                print("Fehler Details:")
                print(json.dumps(error_data, indent=2))
            except:
                print("Raw Response:", response.text)
                
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Request dauerte länger als 2 Minuten")
        print("💡 Browser-Operationen können länger dauern")
        
    except Exception as e:
        print(f"❌ UNERWARTETER FEHLER: {e}")
    
    print()
    print("=" * 60)
    print("🏁 TEST ABGESCHLOSSEN")
    print("💡 Prüfen Sie Ihre Telegram-Gruppe 'PH FUTURES VIP' für Nachrichten!")

if __name__ == "__main__":
    test_real_cryptet_signal()