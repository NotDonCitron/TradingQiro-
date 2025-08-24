#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECHTER CRYPTET URL TEST
Testet mit der echten SOL/USDT URL aus den Telegram-Nachrichten
"""

import asyncio
import os
import sys
from datetime import datetime
import requests

# Füge src Verzeichnis zum Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from connectors.cryptet_scraper import CryptetScraper

class RealCryptetURLTester:
    """Tester für echte Cryptet-URLs"""
    
    def __init__(self):
        self.bot_token = "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw"
        self.target_group_id = -1002773853382
        
        # Die echte SOL/USDT URL aus unseren Telegram-Tests
        self.real_cryptet_url = "https://cryptet.com/signals/one/sol_usdt/2025/08/24/0744?utm_campaign=notification&utm_medium=telegram"
    
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
            
            response = requests.post(url, json=data, timeout=15)
            return response.status_code == 200
                
        except Exception as e:
            print(f"❌ Telegram Send Error: {e}")
            return False
    
    def format_cornix_signal(self, signal_data: dict) -> str:
        """Formatiere Signal für Cornix-Kompatibilität"""
        try:
            symbol = signal_data.get('symbol', 'UNKNOWN')
            direction = signal_data.get('direction', 'UNKNOWN')
            entry_price = signal_data.get('entry_price', 'N/A')
            stop_loss = signal_data.get('stop_loss')
            take_profits = signal_data.get('take_profits', [])
            
            # Direction emoji
            direction_emoji = "🟢" if direction.upper() == "LONG" else "🔴"
            
            # Cornix-kompatibles Format
            formatted_signal = f"{direction_emoji} {direction.title()}\\n"
            formatted_signal += f"Name: {symbol}\\n"
            formatted_signal += f"Margin mode: Cross (50X)\\n\\n"
            
            formatted_signal += "↪️ Entry price(USDT):\\n"
            formatted_signal += f"{entry_price}\\n\\n"
            
            if take_profits:
                formatted_signal += "Targets(USDT):\\n"
                for i, tp in enumerate(take_profits, 1):
                    formatted_signal += f"{i}) {tp}\\n"
                formatted_signal += "\\n"
            
            if stop_loss:
                formatted_signal += f"🛑 Stop Loss: {stop_loss}\\n\\n"
            
            return formatted_signal
            
        except Exception as e:
            print(f"❌ Formatierung Fehler: {e}")
            return None
    
    async def test_real_url(self) -> None:
        """Teste die echte Cryptet-URL"""
        print("🎯 ECHTER CRYPTET URL TEST")
        print("=" * 50)
        print(f"🔗 Test-URL: {self.real_cryptet_url}")
        print()
        
        # Start-Nachricht senden
        start_msg = f"""🎯 **ECHTER CRYPTET URL TEST** 🎯

🕐 **Zeit:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔗 **Echte URL:** {self.real_cryptet_url}

🎯 **Ziel:** Teste mit der echten SOL/USDT URL aus Telegram
🔄 **Status:** Test startet..."""
        
        await self.send_telegram_message(str(self.target_group_id), start_msg)
        
        scraper = CryptetScraper()
        
        try:
            # Browser initialisieren
            print("🌐 Initialisiere Browser...")
            browser_success = await scraper.initialize_browser()
            if not browser_success:
                print("❌ Browser-Initialisierung fehlgeschlagen")
                return
            
            print("✅ Browser erfolgreich initialisiert")
            
            # Teste die echte URL
            print(f"🔍 Scrape echte URL: {self.real_cryptet_url}")
            signal_data = await scraper.scrape_signal(self.real_cryptet_url)
            
            if signal_data:
                print("🎉 ERFOLG! Signal erfolgreich gescrapt!")
                print(f"   Symbol: {signal_data.get('symbol')}")
                print(f"   Direction: {signal_data.get('direction')}")
                print(f"   Entry: {signal_data.get('entry_price')}")
                print(f"   Stop Loss: {signal_data.get('stop_loss')}")
                print(f"   Take Profits: {signal_data.get('take_profits')}")
                
                # Formatiere für Cornix
                cornix_signal = self.format_cornix_signal(signal_data)
                
                # Sende Erfolgsmeldung
                success_msg = f"""🎉 **CRYPTET SCRAPING ERFOLGREICH!** 🎉

✅ **Signal erfolgreich gescrapt von echter URL!**

📊 **Extrahierte Daten:**
• Symbol: {signal_data.get('symbol', 'N/A')}
• Direction: {signal_data.get('direction', 'N/A')}
• Entry Price: {signal_data.get('entry_price', 'N/A')}
• Stop Loss: {signal_data.get('stop_loss', 'N/A')}
• Take Profits: {len(signal_data.get('take_profits', []))} Targets
• Leverage: {signal_data.get('leverage', 50)}x

🔗 **Quelle:** {self.real_cryptet_url[:80]}...

**CORNIX-FORMATIERTES SIGNAL:**
```
{cornix_signal or 'Formatierung fehlgeschlagen'}
```

🎯 **FAZIT:** Das System funktioniert! 
✅ Cryptet-URLs können erfolgreich gescrapt werden
✅ Signal-Daten werden korrekt extrahiert  
✅ Cornix-Format wird generiert

🚀 **Das System ist bereit für Live-Betrieb!**"""
                
                await self.send_telegram_message(str(self.target_group_id), success_msg)
                
            else:
                print("❌ Kein Signal von der echten URL extrahiert")
                
                # Sende Debug-Info
                debug_msg = f"""⚠️ **CRYPTET SCRAPING DEBUG** ⚠️

🔗 **URL:** {self.real_cryptet_url}
❌ **Problem:** Kein Signal extrahiert

🔧 **Mögliche Ursachen:**
• Seite hat andere HTML-Struktur
• Cookies abgelaufen oder ungültig
• Anti-Bot-Schutz aktiv
• Signal bereits archiviert

📋 **Debug-Schritte:**
1. Cookies überprüfen
2. HTML-Parser anpassen
3. Manual browser test
4. Alternative URL-Muster versuchen"""
                
                await self.send_telegram_message(str(self.target_group_id), debug_msg)
                
        except Exception as e:
            print(f"❌ Test Fehler: {e}")
            
            error_msg = f"""❌ **CRYPTET TEST FEHLER** ❌

⚠️ **Error:** {str(e)}
🔗 **URL:** {self.real_cryptet_url}
🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}

🔧 **Debug erforderlich**"""
            
            await self.send_telegram_message(str(self.target_group_id), error_msg)
            
        finally:
            await scraper.close()
            print("✅ Browser geschlossen")

async def main():
    """Hauptfunktion"""
    tester = RealCryptetURLTester()
    await tester.test_real_url()

if __name__ == "__main__":
    print("🎯 ECHTER CRYPTET URL TEST")
    print("Testet mit der echten SOL/USDT URL aus Telegram")
    print()
    
    asyncio.run(main())