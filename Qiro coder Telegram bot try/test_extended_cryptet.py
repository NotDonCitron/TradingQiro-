#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test der erweiterten Cryptet-Funktionen: Symbol-Erkennung und URL-Generierung
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.cryptet_link_handler import CryptetLinkHandler

load_dotenv()

async def test_extended_cryptet_functions():
    """Teste die erweiterten Cryptet-Funktionen"""
    print("🧪 TESTE ERWEITERTE CRYPTET-FUNKTIONEN")
    print("=" * 60)
    
    link_handler = CryptetLinkHandler()
    
    # Test verschiedene Nachrichten-Typen
    test_messages = [
        "BTC/USDT",  # Das was der User sieht
        "ETHUSDT", 
        "DOGE/USDT",
        "btc/usdt",  # Kleinbuchstaben
        "https://cryptet.com/signals/one/btc_usdt/2025/08/24/0646",  # Vollständige URL
        "Hier ist ein Signal für BTC/USDT",  # Text mit Symbol
        "API3/USDT",  # Anderes Symbol
        "Irgendein anderer Text",  # Kein Signal
    ]
    
    print("🔍 TESTE SYMBOL-ERKENNUNG")
    print("-" * 40)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Message: '{message}'")
        
        # Test is_cryptet_link (jetzt erweitert)
        is_cryptet = link_handler.is_cryptet_link(message)
        print(f"   ✅ Als Cryptet erkannt: {is_cryptet}")
        
        # Test is_crypto_symbol
        is_symbol = link_handler.is_crypto_symbol(message)
        print(f"   📊 Als Crypto-Symbol erkannt: {is_symbol}")
        
        # Test URL-Extraktion/Generierung
        extracted_url = link_handler.extract_cryptet_url(message)
        if extracted_url:
            print(f"   🔗 Extrahierte/Generierte URL: {extracted_url}")
        else:
            print(f"   ❌ Keine URL extrahiert/generiert")
        
        # Test komplette Verarbeitung
        if is_cryptet:
            print(f"   🎯 Würde verarbeitet werden!")
            
            # Teste die komplette Verarbeitung (ohne Browser)
            try:
                # Nur URL-Verarbeitung ohne Browser-Scraping
                if extracted_url:
                    print(f"   📡 Würde diese URL scrapen: {extracted_url}")
            except Exception as e:
                print(f"   ❌ Fehler bei Verarbeitung: {e}")
        else:
            print(f"   ⏸️ Würde NICHT verarbeitet werden")
    
    print(f"\n🎯 ZUSAMMENFASSUNG")
    print("-" * 40)
    
    # Zähle erkannte Nachrichten
    recognized_count = sum(1 for msg in test_messages if link_handler.is_cryptet_link(msg))
    symbol_count = sum(1 for msg in test_messages if link_handler.is_crypto_symbol(msg))
    
    print(f"📊 Getestete Nachrichten: {len(test_messages)}")
    print(f"✅ Als Cryptet erkannt: {recognized_count}")
    print(f"📈 Als Crypto-Symbol erkannt: {symbol_count}")
    
    if symbol_count > 0:
        print(f"🎉 ERFOLG! Das System kann jetzt Crypto-Symbole erkennen!")
        print(f"🔧 Die 'BTC/USDT' Nachrichten sollten jetzt verarbeitet werden!")
    else:
        print(f"❌ Problem: Crypto-Symbole werden nicht erkannt!")

if __name__ == "__main__":
    print("🧪 TESTE ERWEITERTE CRYPTET-FUNKTIONEN")
    print("Testet Symbol-Erkennung und URL-Generierung")
    print()
    
    asyncio.run(test_extended_cryptet_functions())