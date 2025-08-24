#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schneller Test der XRP/USDT URL-Extraktion
Testet die Verbesserungen ohne komplexe Browser-Tests
"""

import asyncio
import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class QuickXRPTester:
    """Schneller Test für XRP URL-Problem"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw")
        self.target_group_id = int(os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382"))
        
        # Die problematischen URLs
        self.wrong_url = "https://cryptet.com/de/signals/one/xrpusdt/2025/08/24/1655"
        self.correct_url = "https://cryptet.com/de/signals/one/xrp_usdt/2025/08/24/1456?utm_campaign=notification&utm_medium=telegram"
        
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
    
    def test_url_generation(self):
        """Teste die URL-Generierung"""
        
        print("🧪 TESTE XRP URL-GENERIERUNG")
        print("=" * 50)
        
        # Füge src zum Python Path hinzu
        if "src" not in sys.path:
            sys.path.insert(0, "src")
            sys.path.insert(0, ".")
        
        from src.core.cryptet_link_handler import CryptetLinkHandler
        
        link_handler = CryptetLinkHandler()
        
        # Teste verschiedene Symbol-Formate
        test_symbols = [
            "XRP/USDT",
            "XRPUSDT", 
            "xrp/usdt",
            "xrpusdt"
        ]
        
        results = []
        
        for symbol in test_symbols:
            print(f"\n🧪 Teste Symbol: {symbol}")
            
            # Teste Symbol-Erkennung
            is_symbol = link_handler.is_crypto_symbol(symbol)
            print(f"   📊 Als Symbol erkannt: {is_symbol}")
            
            # Teste URL-Generierung
            generated_url = link_handler.symbol_to_cryptet_url(symbol)
            print(f"   🔗 Generierte URL: {generated_url}")
            
            # Analysiere URL-Qualität
            has_underscore = generated_url and "xrp_usdt" in generated_url
            has_de_prefix = generated_url and "/de/" in generated_url
            
            print(f"   ✅ Unterstrich-Format: {has_underscore}")
            print(f"   ✅ /de/ Präfix: {has_de_prefix}")
            
            quality_score = (
                (1 if is_symbol else 0) +
                (1 if generated_url else 0) +
                (1 if has_underscore else 0) +
                (1 if has_de_prefix else 0)
            )
            
            results.append({
                'symbol': symbol,
                'recognized': is_symbol,
                'url_generated': bool(generated_url),
                'has_underscore': has_underscore,
                'has_de_prefix': has_de_prefix,
                'quality': quality_score,
                'url': generated_url
            })
        
        return results
    
    async def test_with_real_urls(self):
        """Teste mit den echten URLs aus der Nachricht"""
        
        print("\n🎯 TESTE MIT ECHTEN URLS")
        print("=" * 50)
        
        # Füge src zum Python Path hinzu
        if "src" not in sys.path:
            sys.path.insert(0, "src")
            sys.path.insert(0, ".")
        
        from src.core.cryptet_link_handler import CryptetLinkHandler
        from src.core.cryptet_signal_parser import CryptetSignalProcessor
        
        # Sende Start-Nachricht
        start_msg = f"""🔧 **XRP URL-FIX TEST** 🔧

🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}

❌ **Problema:** Falsche URL-Generierung
   `{self.wrong_url[:60]}...`

✅ **Sollte sein:** Korrekte URL mit Unterstrich
   `{self.correct_url[:60]}...`

🔧 **Fix:** Verbesserter URL-Generator
🔄 **Test läuft...**"""
        
        await self.send_telegram_message(str(self.target_group_id), start_msg)
        
        # Initialisiere Handler
        link_handler = CryptetLinkHandler()
        processor = CryptetSignalProcessor()
        
        # Teste direkten Link
        print("📝 Teste direkten korrekten Link...")
        extracted_from_correct = link_handler.extract_cryptet_url(self.correct_url)
        print(f"   Extrahiert: {extracted_from_correct}")
        
        # Teste Symbol-Extraktion
        print("📝 Teste Symbol-zu-URL Konvertierung...")
        generated_from_symbol = link_handler.symbol_to_cryptet_url("XRP/USDT")
        print(f"   Generiert: {generated_from_symbol}")
        
        # Vergleiche URLs
        correct_base = self.correct_url.split('?')[0]  # Ohne UTM-Parameter
        
        direct_match = extracted_from_correct and correct_base in extracted_from_correct
        generated_has_underscore = generated_from_symbol and "xrp_usdt" in generated_from_symbol
        generated_has_de = generated_from_symbol and "/de/" in generated_from_symbol
        
        print(f"\n📊 ERGEBNISSE:")
        print(f"   Direkter Link korrekt: {direct_match}")
        print(f"   Generiert mit Unterstrich: {generated_has_underscore}")
        print(f"   Generiert mit /de/: {generated_has_de}")
        
        # Sende Testergebnis
        if generated_has_underscore and generated_has_de:
            result_msg = f"""✅ **XRP URL-FIX ERFOLGREICH!** ✅

🎯 **Problem gelöst:**
✅ URLs werden jetzt mit Unterstrich generiert (xrp_usdt)
✅ Deutsche URLs mit /de/ Präfix funktionieren
✅ Symbol-Erkennung funktioniert korrekt

📊 **Generierte URL:**
`{generated_from_symbol}`

🔧 **Verbesserungen:**
• Korrekte Symbol-Normalisierung
• /de/ Präfix-Unterstützung  
• Unterstrich-Format für alle Symbole

🎉 **Das XRP-Problem ist behoben!**"""
        else:
            result_msg = f"""⚠️ **XRP URL-FIX UNVOLLSTÄNDIG** ⚠️

🔧 **Noch zu beheben:**
{'❌' if not generated_has_underscore else '✅'} Unterstrich-Format (xrp_usdt)
{'❌' if not generated_has_de else '✅'} /de/ Präfix

📊 **Aktuelle Generierung:**
`{generated_from_symbol}`

🔄 **Weitere Optimierung erforderlich**"""
        
        await self.send_telegram_message(str(self.target_group_id), result_msg)
        
        return generated_has_underscore and generated_has_de
    
    async def run_quick_test(self):
        """Führe schnellen Test aus"""
        
        print("🔧 QUICK XRP URL-FIX TESTER")
        print("=" * 60)
        print("Testet die XRP/USDT URL-Generierung schnell und effizient")
        print()
        
        try:
            # 1. Teste URL-Generierung
            print("📋 Phase 1: URL-Generierung")
            generation_results = self.test_url_generation()
            
            # 2. Teste mit echten URLs
            print("\n📋 Phase 2: Echte URL-Tests")
            real_url_success = await self.test_with_real_urls()
            
            # 3. Auswertung
            successful_generations = sum(1 for r in generation_results if r['quality'] >= 3)
            total_tests = len(generation_results)
            
            print(f"\n📊 GESAMT-ERGEBNIS:")
            print(f"   URL-Generierung: {successful_generations}/{total_tests}")
            print(f"   Echte URL-Tests: {'✅' if real_url_success else '❌'}")
            
            overall_success = (successful_generations == total_tests) and real_url_success
            
            if overall_success:
                print("\n🎉 XRP URL-PROBLEM VOLLSTÄNDIG GELÖST!")
                print("✅ Alle URLs werden jetzt korrekt mit Unterstrichen generiert")
                return True
            else:
                print(f"\n⚠️ Teilweise erfolgreich ({successful_generations}/{total_tests + 1})")
                print("🔧 Weitere Anpassungen erforderlich")
                return False
                
        except Exception as e:
            print(f"❌ Test fehlgeschlagen: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """Hauptfunktion"""
    
    tester = QuickXRPTester()
    success = await tester.run_quick_test()
    
    if success:
        print("\n🔧 XRP URL-PROBLEM IST GELÖST!")
        print("Das System generiert jetzt korrekte URLs mit xrp_usdt Format.")
    else:
        print("\n⚠️ Weitere Optimierung der URL-Generierung erforderlich.")

if __name__ == "__main__":
    print("🔧 QUICK XRP URL-FIX TESTER")
    print("Schneller Test der XRP/USDT URL-Generierung")
    print()
    
    asyncio.run(main())