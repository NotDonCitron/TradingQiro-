#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test der verbesserten Cryptet-Symbol-Verarbeitung
Testet das robuste Timeout-Handling und die besseren Fehlermeldungen
"""

import asyncio
import os
import sys
from datetime import datetime
import requests
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class ImprovedCryptetTester:
    """Test-Klasse für verbesserte Cryptet-Verarbeitung"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw")
        self.target_group_id = int(os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382"))
        
        # Test-Symbole
        self.test_symbols = [
            "XRPUSDT",  # Das problematische Symbol
            "BTC/USDT", 
            "ETH/USDT",
            "SOL/USDT"
        ]
    
    async def send_telegram_message(self, chat_id: str, message: str) -> bool:
        """Sende Nachricht über Telegram Bot API"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
                
        except Exception as e:
            print(f"❌ Telegram Send Error: {e}")
            return False
    
    async def test_symbol_processing(self, symbol: str):
        """Teste die Verarbeitung eines einzelnen Symbols"""
        try:
            from src.core.cryptet_automation import CryptetAutomation
            from src.connectors.telethon_connector import TelethonConnector
            
            print(f"\n🧪 Teste Symbol: {symbol}")
            print("-" * 40)
            
            # Initialisiere Cryptet Automation
            cryptet_automation = CryptetAutomation(self.send_telegram_message)
            
            # Simuliere eine eingehende Telegram-Nachricht 
            test_message = f"[{symbol}](https://cryptet.com/signals/one/{symbol.lower().replace('/', '_')}/2025/08/24/1655)"
            
            metadata = {
                'chat_id': -1001804143400,  # Cryptet Channel ID
                'message_id': 99999,
                'timestamp': datetime.now().isoformat(),
                'extracted_urls': [],
                'entities': []
            }
            
            print(f"📤 Simulierte Nachricht: {test_message[:50]}...")
            
            # Initialisiere das System
            success = await cryptet_automation.initialize()
            if not success:
                print(f"❌ Cryptet Automation konnte nicht initialisiert werden")
                return False
            
            print(f"✅ Cryptet Automation initialisiert")
            
            # Verarbeite die Nachricht
            start_time = asyncio.get_event_loop().time()
            
            result = await cryptet_automation.process_telegram_message(test_message, metadata)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            print(f"🕐 Verarbeitungszeit: {processing_time:.1f}s")
            
            if result:
                print(f"✅ Symbol {symbol} erfolgreich verarbeitet!")
            else:
                print(f"⚠️ Symbol {symbol} nicht verarbeitet (möglicherweise kein Cryptet-Signal)")
            
            # Shutdown
            await cryptet_automation.shutdown()
            
            return result
            
        except Exception as e:
            print(f"❌ Fehler beim Testen von {symbol}: {e}")
            return False
    
    async def test_timeout_handling(self):
        """Teste das Timeout-Handling mit einer nicht existierenden URL"""
        try:
            from src.connectors.cryptet_scraper import CryptetScraper
            
            print(f"\n🕐 Teste Timeout-Handling...")
            print("-" * 40)
            
            scraper = CryptetScraper(headless=True)
            
            # Initialisiere Browser
            success = await scraper.initialize_browser()
            if not success:
                print("❌ Browser konnte nicht initialisiert werden")
                return False
            
            print("✅ Browser initialisiert")
            
            # Teste mit einer nicht-existierenden URL
            fake_url = "https://cryptet.com/signals/one/fake_usdt/2025/08/24/9999"
            
            print(f"🔍 Teste Fake-URL: {fake_url}")
            
            start_time = asyncio.get_event_loop().time()
            
            # Das sollte schnell fehlschlagen und nicht hängen bleiben
            result = await scraper.scrape_signal(fake_url)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            print(f"🕐 Verarbeitungszeit: {processing_time:.1f}s")
            
            if result is None:
                print("✅ Timeout-Handling funktioniert korrekt (kein Ergebnis wie erwartet)")
            else:
                print(f"⚠️ Unerwartetes Ergebnis: {result}")
            
            # Cleanup
            await scraper.close()
            
            return processing_time < 35  # Sollte unter 35 Sekunden bleiben
            
        except Exception as e:
            print(f"❌ Fehler beim Timeout-Test: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Führe umfassende Tests der verbesserten Cryptet-Verarbeitung durch"""
        
        print("🚀 TESTE VERBESSERTE CRYPTET-VERARBEITUNG")
        print("=" * 60)
        print("Testet robustes Timeout-Handling und bessere Fehlermeldungen")
        print(f"🕐 Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Sende Start-Nachricht
        start_msg = f"""🧪 **VERBESSERTER CRYPTET-TEST GESTARTET** 🧪

🕐 **Start:** {datetime.now().strftime('%H:%M:%S')}
🎯 **Ziel:** Teste verbesserte Symbol-Verarbeitung

🔧 **Verbesserungen:**
• ⏰ 60s Timeout für Scraping-Operationen
• 🛡️ Robuste Fehlerbehandlung
• 📊 Strukturierte Fehlermeldungen
• 🔄 Bessere Background-Verarbeitung

📊 **Test-Symbole:** {', '.join(self.test_symbols)}

🔄 **Status:** Tests beginnen..."""
        
        await self.send_telegram_message(str(self.target_group_id), start_msg)
        
        results = []
        
        # 1. Teste Timeout-Handling
        print("📋 Test 1: Timeout-Handling")
        timeout_success = await self.test_timeout_handling()
        results.append(("Timeout-Handling", timeout_success))
        
        # 2. Teste Symbol-Verarbeitung
        print("📋 Test 2: Symbol-Verarbeitung")
        for symbol in self.test_symbols:
            symbol_success = await self.test_symbol_processing(symbol)
            results.append((f"Symbol {symbol}", symbol_success))
            
            # Kurze Pause zwischen Tests
            await asyncio.sleep(3)
        
        # Zusammenfassung
        self.print_summary(results)
        
        # Sende Ergebnis-Nachricht
        successful_tests = sum(1 for _, success in results if success)
        total_tests = len(results)
        
        result_msg = f"""📊 **VERBESSERTER CRYPTET-TEST ABGESCHLOSSEN** 📊

🕐 **Ende:** {datetime.now().strftime('%H:%M:%S')}
📊 **Ergebnis:** {successful_tests}/{total_tests} Tests erfolgreich

✅ **Erfolgreiche Tests:**"""
        
        for test_name, success in results:
            emoji = "✅" if success else "❌"
            result_msg += f"\n{emoji} {test_name}"
        
        if successful_tests == total_tests:
            result_msg += f"\n\n🎉 **ALLE TESTS ERFOLGREICH!**\n✨ Das verbesserte System funktioniert einwandfrei!"
        elif successful_tests > 0:
            result_msg += f"\n\n⚠️ **TEILWEISE ERFOLGREICH**\n🔧 Einige Verbesserungen sind aktiv"
        else:
            result_msg += f"\n\n❌ **TESTS FEHLGESCHLAGEN**\n🔧 System benötigt weitere Debugging"
        
        await self.send_telegram_message(str(self.target_group_id), result_msg)
        
        return successful_tests, total_tests
    
    def print_summary(self, results):
        """Drucke Test-Zusammenfassung"""
        print(f"\n📊 TEST-ZUSAMMENFASSUNG")
        print("=" * 60)
        
        successful = 0
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if success:
                successful += 1
        
        print(f"\n📈 Erfolgsrate: {successful}/{len(results)} ({100*successful/len(results):.1f}%)")
        
        if successful == len(results):
            print("🎉 Alle Verbesserungen funktionieren korrekt!")
        elif successful > len(results) // 2:
            print("⚠️ Die meisten Verbesserungen sind aktiv")
        else:
            print("❌ System benötigt weitere Optimierung")

async def main():
    """Hauptfunktion"""
    
    # Überprüfe Systemumgebung
    if not os.path.exists("src"):
        print("❌ Fehler: 'src' Verzeichnis nicht gefunden")
        print("Bitte aus dem Hauptprojektverzeichnis ausführen")
        sys.exit(1)
    
    # Füge src zum Python Path hinzu
    if "src" not in sys.path:
        sys.path.insert(0, "src")
        sys.path.insert(0, ".")
    
    tester = ImprovedCryptetTester()
    
    try:
        successful, total = await tester.run_comprehensive_test()
        
        if successful == total:
            print("\n🎉 VERBESSERUNGEN ERFOLGREICH IMPLEMENTIERT!")
            print("Das Cryptet-System ist jetzt robuster und zuverlässiger.")
        else:
            print(f"\n⚠️ {successful}/{total} Verbesserungen aktiv")
            print("Weitere Optimierungen möglich.")
            
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 TESTE VERBESSERTE CRYPTET-VERARBEITUNG")
    print("Überprüft Timeout-Handling und Fehlerbehandlung")
    print()
    
    asyncio.run(main())