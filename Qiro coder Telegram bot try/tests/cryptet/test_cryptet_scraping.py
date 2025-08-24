#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direkter Test des Cryptet-Scraping-Systems
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.connectors.cryptet_scraper import CryptetScraper
from src.core.cryptet_link_handler import CryptetLinkHandler
from src.core.cryptet_automation import CryptetAutomation

load_dotenv()

async def test_cryptet_scraping():
    """Teste das Cryptet-Scraping direkt"""
    print("🧪 TESTE CRYPTET-SCRAPING")
    print("=" * 50)
    
    # Test-URL (aus dem Screenshot)
    test_url = "https://cryptet.com/signals/one/btc_usdt/2025/08/24/0646"
    print(f"🔗 Test-URL: {test_url}")
    
    # 1. Teste CryptetScraper direkt
    print(f"\n1️⃣ TESTE CRYPTET-SCRAPER DIREKT")
    print("-" * 30)
    
    scraper = CryptetScraper(headless=False)  # Nicht headless für Debug
    
    try:
        # Browser initialisieren
        print("🌐 Initialisiere Browser...")
        browser_ok = await scraper.initialize_browser()
        
        if browser_ok:
            print("✅ Browser erfolgreich initialisiert")
            
            # Signal scrapen
            print(f"📊 Scrape Signal von: {test_url}")
            signal_data = await scraper.scrape_signal(test_url)
            
            if signal_data:
                print("✅ SIGNAL ERFOLGREICH GESCRAPT!")
                print(f"📈 Signal-Daten: {signal_data}")
            else:
                print("❌ KEIN SIGNAL GEFUNDEN!")
                print("Das ist wahrscheinlich das Problem!")
        else:
            print("❌ Browser-Initialisierung fehlgeschlagen")
            
    except Exception as e:
        print(f"❌ Fehler beim Scraping: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()
    
    # 2. Teste CryptetLinkHandler
    print(f"\n2️⃣ TESTE CRYPTET-LINK-HANDLER")
    print("-" * 30)
    
    try:
        link_handler = CryptetLinkHandler()
        
        # Link-Erkennung testen
        is_cryptet = link_handler.is_cryptet_link(test_url)
        print(f"🔍 Link erkannt: {is_cryptet}")
        
        # URL extrahieren
        extracted_url = link_handler.extract_cryptet_url(test_url)
        print(f"🔗 Extrahierte URL: {extracted_url}")
        
        # URL validieren
        is_valid = link_handler.validate_cryptet_url(test_url)
        print(f"✅ URL gültig: {is_valid}")
        
        # Komplett verarbeiten
        print("📊 Verarbeite Link komplett...")
        processed_data = await link_handler.process_cryptet_link(test_url)
        
        if processed_data:
            print("✅ LINK ERFOLGREICH VERARBEITET!")
            print(f"📈 Verarbeitete Daten: {processed_data}")
        else:
            print("❌ LINK-VERARBEITUNG FEHLGESCHLAGEN!")
            
    except Exception as e:
        print(f"❌ Fehler beim Link-Handler: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Teste nur die Nachricht (ohne Browser)
    print(f"\n3️⃣ TESTE NUR MESSAGE-PARSING")
    print("-" * 30)
    
    # Simuliere eine Telegram-Nachricht mit dem Cryptet-Link
    test_message = "BTC/USDT"  # Das ist was der User vom System sieht
    test_metadata = {
        "chat_id": -1001804143400,
        "message_id": 12345,
        "sender_id": 123456789
    }
    
    print(f"📝 Test-Nachricht: '{test_message}'")
    print(f"📋 Metadata: {test_metadata}")
    
    # Prüfe, ob das als Cryptet-Link erkannt wird
    link_handler2 = CryptetLinkHandler()
    is_recognized = link_handler2.is_cryptet_link(test_message)
    
    print(f"🔍 Als Cryptet-Link erkannt: {is_recognized}")
    
    if not is_recognized:
        print("❌ DAS IST DAS PROBLEM!")
        print("Das System erkennt 'BTC/USDT' nicht als Cryptet-Link!")
        print("Das erklärt, warum nur Benachrichtigungen gesendet werden!")

if __name__ == "__main__":
    print("🧪 CRYPTET-SCRAPING TESTER")
    print("Testet das komplette Cryptet-System Schritt für Schritt")
    print()
    
    asyncio.run(test_cryptet_scraping())