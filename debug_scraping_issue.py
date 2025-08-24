#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug-Skript um das Scraping-Problem zu analysieren
Testet einen echten Cryptet-Link um zu sehen was gescraped wird
"""

import asyncio
import os
import sys
from datetime import datetime
import requests
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class ScrapingDebugger:
    """Debug-Klasse für Scraping-Probleme"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw")
        self.target_group_id = int(os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382"))
        
        # URLs aus dem letzten Test
        self.test_urls = [
            "https://cryptet.com/signals/one/link_usdt/2025/08/24/1517?utm_campaign=notification&utm_medium=telegram",
            "https://cryptet.com/signals/one/xrp_usdt/2025/08/24/1456?utm_campaign=notification&utm_medium=telegram",
            "https://cryptet.com/signals/one/trx_usdt/2025/08/24/1440?utm_campaign=notification&utm_medium=telegram",
            "https://cryptet.com/signals/one/ltc_usdt/2025/08/24/1415?utm_campaign=notification&utm_medium=telegram"
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
    
    async def debug_single_url(self, url: str, url_number: int):
        """Debug eine einzelne URL um zu sehen was gescraped wird"""
        try:
            from src.connectors.cryptet_scraper import CryptetScraper
            
            print(f"\n🔍 DEBUGGING URL {url_number}: {url}")
            print("-" * 80)
            
            # Initialisiere Scraper
            scraper = CryptetScraper(headless=False)  # Nicht headless für bessere Debugging
            
            # Initialisiere Browser
            success = await scraper.initialize_browser()
            if not success:
                print(f"❌ Browser konnte nicht initialisiert werden")
                return None
            
            print(f"✅ Browser initialisiert")
            
            # Scrape das Signal
            start_time = asyncio.get_event_loop().time()
            
            signal_data = await scraper.scrape_signal(url)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            print(f"🕐 Scraping-Zeit: {processing_time:.2f}s")
            
            if signal_data:
                print(f"✅ Signal erfolgreich gescraped!")
                print(f"📊 Vollständige Signal-Daten:")
                for key, value in signal_data.items():
                    print(f"   {key}: {value}")
                
                # Formatiere das Signal für Cornix
                from src.core.cryptet_automation import CryptetAutomation
                automation = CryptetAutomation()
                formatted_signal = automation._format_cornix_signal(signal_data)
                
                if formatted_signal:
                    print(f"\n📤 Formatiertes Signal für Cornix:")
                    print(formatted_signal)
                    
                    # Sende das formatierte Signal
                    debug_msg = f"""🔍 **DEBUG SCRAPING URL {url_number}** 🔍

✅ **Scraping erfolgreich:** {processing_time:.2f}s
🔗 **URL:** {url[:60]}...

📊 **Rohdaten:**
• Symbol: {signal_data.get('symbol', 'N/A')}
• Direction: {signal_data.get('direction', 'N/A')}
• Entry: {signal_data.get('entry_price', 'N/A')}
• Stop Loss: {signal_data.get('stop_loss', 'N/A')}
• Take Profits: {signal_data.get('take_profits', 'N/A')}

📤 **Formatiertes Signal:**
```
{formatted_signal}
```"""
                    
                    await self.send_telegram_message(str(self.target_group_id), debug_msg)
                else:
                    print(f"❌ Fehler beim Formatieren des Signals")
                    error_msg = f"""⚠️ **DEBUG URL {url_number} - FORMATIERUNGSFEHLER** ⚠️

✅ **Scraping:** Erfolgreich ({processing_time:.2f}s)
❌ **Formatierung:** Fehlgeschlagen

📊 **Rohdaten waren:** {signal_data}
🔧 **Problem:** _format_cornix_signal() returnierte None"""
                    
                    await self.send_telegram_message(str(self.target_group_id), error_msg)
            else:
                print(f"❌ Kein Signal gescraped")
                error_msg = f"""❌ **DEBUG URL {url_number} - SCRAPING FEHLGESCHLAGEN** ❌

🕐 **Zeit:** {processing_time:.2f}s
🔗 **URL:** {url[:60]}...

⚠️ **Problem:** scrape_signal() returnierte None
🔧 **Mögliche Ursachen:**
• Seite nicht geladen
• Struktur der Seite geändert
• Extraction-Pattern passen nicht
• Browser-Probleme"""
                
                await self.send_telegram_message(str(self.target_group_id), error_msg)
            
            # Cleanup
            await scraper.close()
            
            return signal_data
            
        except Exception as e:
            print(f"❌ Fehler beim Debugging: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = f"""❌ **DEBUG URL {url_number} - EXCEPTION** ❌

⚠️ **Fehler:** {str(e)[:100]}...
🔧 **Details:** Siehe Logs für vollständigen Stacktrace"""
            
            await self.send_telegram_message(str(self.target_group_id), error_msg)
            return None
    
    async def run_complete_debug(self):
        """Führe komplettes Debug aller URLs durch"""
        
        print("🔍 DEBUGGING CRYPTET SCRAPING PROBLEM")
        print("=" * 60)
        print("Testet echte Cryptet URLs um herauszufinden warum kein Signal gescraped wird")
        print()
        
        # Sende Start-Nachricht
        start_msg = f"""🔍 **CRYPTET SCRAPING DEBUG GESTARTET** 🔍

🕐 **Start:** {datetime.now().strftime('%H:%M:%S')}
🎯 **Ziel:** Herausfinden warum Signale nicht gescraped werden

📋 **Test-URLs:** {len(self.test_urls)} echte Cryptet-Links
🔧 **Methode:** Einzelverarbeitung mit detaillierter Analyse

🔄 **Status:** Debug beginnt..."""
        
        await self.send_telegram_message(str(self.target_group_id), start_msg)
        
        results = []
        
        # Debug jede URL einzeln
        for i, url in enumerate(self.test_urls, 1):
            result = await self.debug_single_url(url, i)
            results.append({
                'url_number': i,
                'url': url,
                'success': result is not None,
                'data': result
            })
            
            # Pause zwischen URLs
            if i < len(self.test_urls):
                print(f"⏳ Pause zwischen URLs...")
                await asyncio.sleep(3)
        
        # Zusammenfassung
        successful = sum(1 for r in results if r['success'])
        
        summary_msg = f"""📊 **CRYPTET SCRAPING DEBUG ABGESCHLOSSEN** 📊

🕐 **Ende:** {datetime.now().strftime('%H:%M:%S')}
📈 **Erfolgsrate:** {successful}/{len(results)} URLs

✅ **Erfolgreich:** {successful}
❌ **Fehlgeschlagen:** {len(results) - successful}

📋 **Detaillierte Ergebnisse:**"""
        
        for result in results:
            status = "✅" if result['success'] else "❌"
            url_short = result['url'].split('/')[-1][:20]
            summary_msg += f"\n{status} URL {result['url_number']}: {url_short}..."
        
        if successful == 0:
            summary_msg += f"\n\n❌ **PROBLEM IDENTIFIZIERT:**\nKEINE der URLs konnte erfolgreich gescraped werden!"
            summary_msg += f"\n\n🔧 **MÖGLICHE URSACHEN:**\n• Cryptet Website-Struktur geändert\n• Browser/Selenium-Problem\n• Cookie/Authentication-Problem\n• Extraction-Pattern veraltet"
        elif successful < len(results):
            summary_msg += f"\n\n⚠️ **TEILPROBLEM:**\nNur {successful}/{len(results)} URLs funktionieren"
        else:
            summary_msg += f"\n\n🎉 **ALLES FUNKTIONIERT:**\nAlle URLs wurden erfolgreich gescraped!"
        
        await self.send_telegram_message(str(self.target_group_id), summary_msg)
        
        return successful, len(results)

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
    
    debugger = ScrapingDebugger()
    
    try:
        successful, total = await debugger.run_complete_debug()
        
        if successful == total:
            print("\n✅ SCRAPING FUNKTIONIERT KORREKT!")
            print("Das Problem liegt woanders im System.")
        elif successful > 0:
            print(f"\n⚠️ TEILWEISE FUNKTIONSFÄHIG: {successful}/{total}")
            print("Einige URLs funktionieren, andere nicht.")
        else:
            print(f"\n❌ SCRAPING KOMPLETT DEFEKT!")
            print("Keine der URLs konnte gescraped werden.")
            
    except Exception as e:
        print(f"❌ Debug fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 CRYPTET SCRAPING DEBUGGER")
    print("Analysiert warum keine Signale gescraped werden")
    print()
    
    asyncio.run(main())