#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Cross-Margin Integration in Signal-Formatierung
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.cryptet_signal_parser import CryptetSignalProcessor, CryptetSignalFormatter

load_dotenv()

async def test_cross_margin_formatting():
    """Teste Cross-Margin in Signal-Formatierung"""
    print("🧪 TESTE CROSS-MARGIN FORMATIERUNG")
    print("=" * 50)
    
    # Test Cryptet Signal Processor
    print("1️⃣ CRYPTET SIGNAL PROCESSOR")
    print("-" * 30)
    
    processor = CryptetSignalProcessor()
    
    # Test-Signal-Daten
    test_signal_data = {
        'symbol': 'BTCUSDT',
        'direction': 'LONG',
        'entry_price': '114950',
        'take_profits': ['115310'],
        'stop_loss': '114490',
        'leverage': 50,
        'source': 'cryptet',
        'url': 'https://cryptet.com/signals/test'
    }
    
    # Test normale Signal-Verarbeitung
    formatted_signal = processor.process_signal(test_signal_data)
    
    if formatted_signal:
        print("✅ Signal erfolgreich formatiert:")
        print("📋 Ausgabe:")
        print("-" * 40)
        print(formatted_signal)
        print("-" * 40)
        
        # Prüfe ob "Cross" im Text enthalten ist
        if "Cross 50x" in formatted_signal:
            print("✅ Cross-Margin korrekt angezeigt!")
        else:
            print("❌ Cross-Margin NICHT gefunden!")
            print("🔍 Suche nach 'Cross' im Text...")
            if "Cross" in formatted_signal:
                print("✅ 'Cross' gefunden, aber nicht im erwarteten Format")
            else:
                print("❌ 'Cross' gar nicht gefunden!")
    else:
        print("❌ Signal-Formatierung fehlgeschlagen!")
    
    print(f"\n2️⃣ SYMBOL-ONLY PROCESSOR")
    print("-" * 30)
    
    # Test Symbol-Only Processing
    symbol_signal = processor.process_symbol_only("BTC/USDT", "https://cryptet.com/test")
    
    if symbol_signal:
        print("✅ Symbol-Signal erfolgreich formatiert:")
        print("📋 Ausgabe:")
        print("-" * 40)
        print(symbol_signal)
        print("-" * 40)
        
        # Prüfe ob "Cross 50x" im Text enthalten ist
        if "Cross 50x" in symbol_signal:
            print("✅ Cross-Margin im Symbol-Signal korrekt angezeigt!")
        else:
            print("❌ Cross-Margin im Symbol-Signal NICHT gefunden!")
    else:
        print("❌ Symbol-Signal-Formatierung fehlgeschlagen!")
    
    print(f"\n3️⃣ DIREKTER FORMATTER TEST")
    print("-" * 30)
    
    # Test direkter Formatter
    formatter = CryptetSignalFormatter()
    direct_formatted = formatter.format_for_telegram(test_signal_data)
    
    if direct_formatted:
        print("✅ Direkter Formatter erfolgreich:")
        print("📋 Ausgabe:")
        print("-" * 40)
        print(direct_formatted)
        print("-" * 40)
        
        # Detaillierte Cross-Margin-Prüfung
        if "Cross 50x" in direct_formatted:
            print("✅ Cross-Margin im direkten Formatter korrekt!")
        else:
            print("❌ Cross-Margin im direkten Formatter NICHT gefunden!")
            print("🔍 Debug-Suche...")
            lines = direct_formatted.split('\n')
            for i, line in enumerate(lines):
                if 'leverage' in line.lower() or 'cross' in line.lower():
                    print(f"   Zeile {i}: {line}")
    
    print(f"\n4️⃣ VERGLEICH: VOR UND NACH ÄNDERUNG")
    print("-" * 30)
    
    # Zeige erwartetes vs. aktuelles Format
    expected_line = "⚡ **Leverage:** Cross 50x"
    old_line = "⚡ **Leverage:** 50x"
    
    print(f"❌ Alt: {old_line}")
    print(f"✅ Neu: {expected_line}")
    
    if expected_line in direct_formatted:
        print("✅ ERFOLGREICH: Neue Cross-Margin Formatierung aktiv!")
    elif old_line in direct_formatted:
        print("⚠️ WARNUNG: Alte Formatierung noch aktiv!")
    else:
        print("❓ UNBEKANNT: Weder alte noch neue Formatierung gefunden!")
    
    print(f"\n🎯 ZUSAMMENFASSUNG")
    print("=" * 50)
    
    # Sammle Ergebnisse
    tests = [
        ("Cryptet Signal Processor", "Cross 50x" in formatted_signal if formatted_signal else False),
        ("Symbol-Only Processor", "Cross 50x" in symbol_signal if symbol_signal else False),
        ("Direkter Formatter", "Cross 50x" in direct_formatted if direct_formatted else False)
    ]
    
    successful_tests = sum(1 for _, success in tests if success)
    total_tests = len(tests)
    
    print(f"📊 Erfolgreiche Tests: {successful_tests}/{total_tests}")
    
    for test_name, success in tests:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
    
    if successful_tests == total_tests:
        print(f"\n🎉 ALLE TESTS ERFOLGREICH!")
        print(f"Cross-Margin wird korrekt in allen Signal-Formatierungen angezeigt!")
    else:
        print(f"\n⚠️ {total_tests - successful_tests} TESTS FEHLGESCHLAGEN")
        print(f"Cross-Margin Integration muss überprüft werden.")
    
    return successful_tests == total_tests

if __name__ == "__main__":
    print("🧪 CROSS-MARGIN INTEGRATION TEST")
    print("Überprüft ob Cross-Margin in allen Signal-Formatierungen korrekt angezeigt wird")
    print()
    
    success = asyncio.run(test_cross_margin_formatting())
    
    if success:
        print("\n🎉 CROSS-MARGIN ERFOLGREICH INTEGRIERT!")
        print("Alle Signale zeigen jetzt 'Cross 50x' Leverage an!")
    else:
        print("\n⚠️ CROSS-MARGIN INTEGRATION UNVOLLSTÄNDIG")