#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finaler Test des erweiterten Cryptet-Systems mit Symbol-Erkennung
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.cryptet_automation import CryptetAutomation

load_dotenv()

async def test_complete_cryptet_system():
    """Teste das komplette erweiterte Cryptet-System"""
    print("🧪 TESTE KOMPLETTES ERWEITERES CRYPTET-SYSTEM")
    print("=" * 70)
    
    # Mock send_message callback
    sent_messages = []
    
    async def mock_send_message(chat_id: str, message: str):
        sent_messages.append({"chat_id": chat_id, "message": message})
        print(f"\n📤 NACHRICHT GESENDET an {chat_id}:")
        print("-" * 40)
        print(message)
        print("-" * 40)
    
    # Initialize Cryptet automation
    print("🚀 Initialisiere Cryptet-Automation...")
    automation = CryptetAutomation(send_message_callback=mock_send_message)
    
    # Mock initialization (ohne echten Browser für Test)
    automation.is_running = True
    automation.is_initialized = True
    automation.own_group_chat_id = "-1002773853382"
    
    print("✅ Cryptet-Automation bereit")
    
    # Test verschiedene Nachrichtentypen
    test_cases = [
        {
            "name": "Crypto Symbol (BTC/USDT)",
            "message": "BTC/USDT",
            "metadata": {"chat_id": -1001804143400, "message_id": 1},
            "expected": "sollte Symbol-Notification + Background-Processing auslösen"
        },
        {
            "name": "Crypto Symbol (ETHUSDT)",
            "message": "ETHUSDT", 
            "metadata": {"chat_id": -1001804143400, "message_id": 2},
            "expected": "sollte Symbol-Notification + Background-Processing auslösen"
        },
        {
            "name": "Vollständige Cryptet-URL",
            "message": "https://cryptet.com/signals/one/btc_usdt/2025/08/24/0646",
            "metadata": {"chat_id": -1001804143400, "message_id": 3},
            "expected": "sollte normales Signal-Processing auslösen"
        },
        {
            "name": "Nicht-Cryptet Nachricht",
            "message": "Hallo, wie geht's?",
            "metadata": {"chat_id": -1001804143400, "message_id": 4},
            "expected": "sollte ignoriert werden"
        },
        {
            "name": "API3 Symbol",
            "message": "API3/USDT",
            "metadata": {"chat_id": -1001804143400, "message_id": 5},
            "expected": "sollte Symbol-Notification + Background-Processing auslösen"
        }
    ]
    
    print(f"\n🔍 TESTE {len(test_cases)} VERSCHIEDENE NACHRICHTENTYPEN")
    print("=" * 70)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   📝 Nachricht: '{test_case['message']}'")
        print(f"   📋 Erwartung: {test_case['expected']}")
        
        # Reset sent messages for this test
        initial_message_count = len(sent_messages)
        
        try:
            # Process the message
            processed = await automation.process_telegram_message(test_case['message'], test_case['metadata'])
            
            # Count new messages
            new_message_count = len(sent_messages) - initial_message_count
            
            result = {
                "test_name": test_case['name'],
                "processed": processed,
                "messages_sent": new_message_count,
                "success": processed if test_case['name'] != "Nicht-Cryptet Nachricht" else not processed
            }
            
            results.append(result)
            
            if result["success"]:
                print(f"   ✅ ERFOLGREICH: Verarbeitet={processed}, Nachrichten={new_message_count}")
            else:
                print(f"   ❌ FEHLGESCHLAGEN: Verarbeitet={processed}, Nachrichten={new_message_count}")
                
        except Exception as e:
            print(f"   ❌ FEHLER: {e}")
            results.append({
                "test_name": test_case['name'],
                "processed": False,
                "messages_sent": 0,
                "success": False,
                "error": str(e)
            })
        
        # Wait a bit between tests
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n🎯 TESTERGEBNISSE")
    print("=" * 70)
    
    successful_tests = sum(1 for r in results if r["success"])
    total_tests = len(results)
    total_messages = len(sent_messages)
    
    print(f"📊 Erfolgreiche Tests: {successful_tests}/{total_tests}")
    print(f"📤 Gesendete Nachrichten: {total_messages}")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"   {status} {result['test_name']}: {result['processed']} ({result['messages_sent']} msgs)")
    
    if successful_tests == total_tests:
        print(f"\n🎉 ALLE TESTS ERFOLGREICH!")
        print(f"Das erweiterte Cryptet-System funktioniert korrekt!")
        print(f"Es kann jetzt sowohl vollständige URLs als auch Crypto-Symbole verarbeiten!")
    else:
        print(f"\n⚠️ {total_tests - successful_tests} TESTS FEHLGESCHLAGEN")
        print(f"Bitte prüfen Sie die Logs für Details.")
    
    return successful_tests == total_tests

if __name__ == "__main__":
    print("🧪 FINALER CRYPTET-SYSTEM-TEST")
    print("Testet das komplette erweiterte System mit Symbol-Erkennung")
    print()
    
    success = asyncio.run(test_complete_cryptet_system())
    
    if success:
        print("\n🎉 SYSTEM IST BEREIT!")
        print("Das Cryptet-System kann jetzt BTC/USDT Nachrichten verarbeiten!")
    else:
        print("\n⚠️ SYSTEM BENÖTIGT WEITERE ANPASSUNGEN")