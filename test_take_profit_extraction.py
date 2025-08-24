#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug-Script für Take Profit-Extraktion aus Cryptet-Seiten
"""
import asyncio
import os
import sys
from bs4 import BeautifulSoup
import re

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.connectors.cryptet_scraper import CryptetScraper

async def test_take_profit_extraction():
    """Teste die Take Profit-Extraktion mit verschiedenen Formaten"""
    print("🧪 TESTE TAKE PROFIT-EXTRAKTION")
    print("=" * 50)
    
    # Test HTML-Inhalte mit verschiedenen Formaten
    test_html_samples = [
        {
            "name": "Cryptet Format mit Take Profit*",
            "html": """
            <div>
                <h2>BTC/USDT LONG Signal</h2>
                <p>Entry Price: 114950</p>
                <p>Take Profit*</p>
                <p>115310</p>
                <p>Stop Loss: 114490</p>
            </div>
            """
        },
        {
            "name": "Standard Take Profit Format",
            "html": """
            <div>
                <p>Take Profit: 115310</p>
                <p>TP1: 115000</p>
                <p>Target 1: 115500</p>
            </div>
            """
        },
        {
            "name": "Deutsche Take Profit Begriffe",
            "html": """
            <div>
                <p>Gewinnmitnahme: 115310</p>
                <p>Ziel 1: 115000</p>
            </div>
            """
        },
        {
            "name": "Cryptet Format - Mehrzeilig",
            "html": """
            <div class="signal">
                <span>BTC/USDT LONG</span>
                <div>Entry: 114950</div>
                <div>Take Profit*</div>
                <div>115310</div>
                <div>115500</div>
                <div>Stop Loss: 114490</div>
            </div>
            """
        },
        {
            "name": "Gemischtes Format",
            "html": """
            <body>
                <h1>Trading Signal</h1>
                <p>Symbol: BTC/USDT</p>
                <p>Direction: LONG</p>
                <p>Entry Price: 114950</p>
                <p>Take Profit*</p>
                <span>115310</span>
                <p>Additional target: 116000</p>
                <p>Stop Loss: 114490</p>
                <p>Leverage: 50x</p>
            </body>
            """
        }
    ]
    
    # Erstelle einen Scraper für die Extraktion
    scraper = CryptetScraper(headless=True)
    
    for i, test_case in enumerate(test_html_samples, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        
        # Parse HTML
        soup = BeautifulSoup(test_case['html'], 'html.parser')
        
        # Test die Take Profit-Extraktion
        try:
            take_profits = await scraper.extract_take_profits(soup)
            
            if take_profits:
                print(f"✅ Take Profits gefunden: {take_profits}")
                for j, tp in enumerate(take_profits, 1):
                    print(f"   TP{j}: {tp}")
            else:
                print("❌ Keine Take Profits gefunden")
                
            # Debug: Zeige den Text-Inhalt
            page_text = soup.get_text()
            print(f"📄 Text-Inhalt: {repr(page_text[:200])}...")
            
        except Exception as e:
            print(f"❌ Fehler bei Extraktion: {e}")
    
    # Test mit echtem Cryptet-Link
    print(f"\n6. ECHTER CRYPTET-LINK TEST")
    print("-" * 40)
    
    test_url = "https://cryptet.com/signals/one/btc_usdt/2025/08/24/0646"
    
    try:
        # Browser initialisieren
        await scraper.initialize_browser()
        
        # Scrape echte Seite
        print(f"🌐 Scrape echte Cryptet-Seite: {test_url}")
        signal_data = await scraper.scrape_signal(test_url)
        
        if signal_data:
            print(f"✅ Signal erfolgreich gescrapt:")
            for key, value in signal_data.items():
                print(f"   {key}: {value}")
        else:
            print("❌ Signal-Scraping fehlgeschlagen")
            
        # Manueller Test der Take Profit-Extraktion
        scraper.driver.get(test_url)
        await asyncio.sleep(3)
        
        html = scraper.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        print(f"\n🔍 MANUELLE TAKE PROFIT-EXTRAKTION:")
        take_profits = await scraper.extract_take_profits(soup)
        
        if take_profits:
            print(f"✅ Take Profits von echter Seite: {take_profits}")
        else:
            print("❌ Keine Take Profits von echter Seite")
            # Debug: Zeige relevanten Text
            page_text = soup.get_text()
            print(f"📄 Seitentext (erste 1000 Zeichen):")
            print(page_text[:1000])
            
            # Suche manuell nach "Take Profit" im Text
            if "take profit" in page_text.lower():
                print("🔍 'Take Profit' gefunden im Text!")
                # Zeige Zeilen mit "Take Profit"
                lines = page_text.split('\n')
                for line_num, line in enumerate(lines):
                    if 'take profit' in line.lower() or 'profit' in line.lower():
                        print(f"   Zeile {line_num}: {line.strip()}")
            else:
                print("❌ 'Take Profit' nicht im Text gefunden")
        
    except Exception as e:
        print(f"❌ Fehler beim echten Test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()
    
    print(f"\n🎯 ZUSAMMENFASSUNG")
    print("=" * 50)
    print("Dieser Test hilft dabei, die Take Profit-Extraktion zu debuggen")
    print("und sicherzustellen, dass das Format 'Take Profit* 115310' erkannt wird.")

if __name__ == "__main__":
    print("🧪 TAKE PROFIT EXTRAKTION DEBUG")
    print("Testet die erweiterten Regex-Patterns für Take Profit-Erkennung")
    print()
    
    asyncio.run(test_take_profit_extraction())