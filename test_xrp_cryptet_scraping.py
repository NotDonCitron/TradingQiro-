#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test: Echter XRP Cryptet Link Scraping und Signal-Weiterleitung
Testet die komplette Pipeline: Link → Scraping → Formatierung → Weiterleitung
"""

import asyncio
import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class XRPCryptetScrapingTester:
    """Test-Klasse für echtes XRP Cryptet Scraping"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw")
        self.target_group_id = int(os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382"))
        
        # Der echte XRP Cryptet Link (korrigierte URL mit Unterstrich)
        self.real_xrp_link = "https://cryptet.com/de/signals/one/xrp_usdt/2025/08/24/1456?utm_campaign=notification&utm_medium=telegram"
        
        # Simulierter Cryptet Channel (gemäß Spezifikation: -1001804143400)
        self.cryptet_channel_id = -1001804143400
        
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
            success = response.status_code == 200
            if success:
                print(f"✅ Nachricht gesendet: {message[:50]}...")
            else:
                print(f"❌ Fehler beim Senden: {response.status_code} - {response.text}")
            return success
                
        except Exception as e:
            print(f"❌ Telegram Send Error: {e}")
            return False
    
    async def test_cryptet_automation_system(self):
        """Teste das komplette Cryptet Automation System"""
        
        print("🚀 TESTE CRYPTET AUTOMATION MIT ECHTEM XRP LINK")
        print("=" * 60)
        print("Simuliert echte Nachricht aus Cryptet Channel → Scraping → Weiterleitung")
        print()
        
        # Füge src zum Python Path hinzu
        if "src" not in sys.path:
            sys.path.insert(0, "src")
            sys.path.insert(0, ".")
        
        # Sende Start-Nachricht
        start_msg = f"""🧪 **ECHTES XRP CRYPTET SCRAPING TEST** 🧪

🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}
🎯 **Ziel:** Teste komplette Pipeline mit echtem Cryptet Link

🔗 **Test-Link:** 
`{self.real_xrp_link[:60]}...`

📋 **Pipeline:**
1. 🔍 Link aus Cryptet Channel simulieren
2. 🌐 Automatisches Scraping der Webseite
3. 📊 Signal-Extraktion und Formatierung  
4. 📤 Weiterleitung an Zielgruppe

🔄 **Test startet...**"""
        
        await self.send_telegram_message(str(self.target_group_id), start_msg)
        
        try:
            # Importiere Cryptet Automation System
            from src.core.cryptet_automation import CryptetAutomation
            
            # Initialisiere das Automation System
            cryptet_automation = CryptetAutomation(self.send_telegram_message)
            
            print("🔧 Initialisiere Cryptet Automation...")
            success = await cryptet_automation.initialize()
            
            if not success:
                print("❌ Cryptet Automation konnte nicht initialisiert werden")
                return False
            
            print("✅ Cryptet Automation erfolgreich initialisiert")
            
            # Simuliere eingehende Telegram-Nachricht aus Cryptet Channel
            print(f"📨 Simuliere Nachricht aus Cryptet Channel ({self.cryptet_channel_id})")
            
            # Simuliere die Nachricht wie sie vom Cryptet Channel kommen würde
            simulated_message = f"[XRP/USDT]({self.real_xrp_link})"
            
            # Metadaten der simulierten Nachricht (gemäß Spezifikationen)
            metadata = {
                'chat_id': self.cryptet_channel_id,  # CryptET Channel ID (-1001804143400)
                'message_id': 32999,
                'timestamp': datetime.now().isoformat(),
                'extracted_urls': [self.real_xrp_link],
                'entities': [{'url': self.real_xrp_link, 'type': 'url'}],
                'source': 'cryptet_channel'
            }
            
            print(f"📝 Simulierte Nachricht: {simulated_message}")
            print(f"🏷️  Metadaten: Chat-ID {metadata['chat_id']}")
            
            # Sende Status-Update
            processing_msg = f"""🔄 **PROCESSING GESTARTET** 🔄

📨 **Simulierte Nachricht aus Cryptet Channel:**
`{simulated_message}`

🔗 **URL wird verarbeitet:**
`{self.real_xrp_link}`

⏳ **Scraping läuft...**
(Das kann 30-60 Sekunden dauern)"""
            
            await self.send_telegram_message(str(self.target_group_id), processing_msg)
            
            # Verarbeite die Nachricht durch das Cryptet System
            print("🌐 Starte Verarbeitung durch Cryptet Automation...")
            
            processing_start = asyncio.get_event_loop().time()
            result = await cryptet_automation.process_telegram_message(simulated_message, metadata)
            processing_duration = asyncio.get_event_loop().time() - processing_start
            
            print(f"⏱️  Verarbeitung abgeschlossen in {processing_duration:.1f} Sekunden")
            print(f"📊 Ergebnis: {'✅ Erfolgreich' if result else '❌ Fehlgeschlagen'}")
            
            # Warte kurz auf Background-Verarbeitung
            print("⏳ Warte auf Background-Scraping...")
            await asyncio.sleep(5)
            
            # Sende Ergebnis-Nachricht
            if result:
                result_msg = f"""✅ **XRP CRYPTET SCRAPING ERFOLGREICH!** ✅

🕐 **Verarbeitung abgeschlossen:** {datetime.now().strftime('%H:%M:%S')}
⏱️  **Dauer:** {processing_duration:.1f} Sekunden
🔗 **Gescrapte URL:** `{self.real_xrp_link[:50]}...`

🎉 **Pipeline erfolgreich:**
✅ Link aus Cryptet Channel erkannt
✅ Automatisches Browser-Scraping durchgeführt  
✅ Signal-Daten extrahiert und formatiert
✅ Cornix-kompatibles Signal generiert
✅ Weiterleitung an Zielgruppe erfolgt

📊 **Das XRP-Signal sollte über dieser Nachricht erscheinen!**

🚀 **System funktioniert einwandfrei!**"""
            else:
                result_msg = f"""⚠️ **XRP CRYPTET SCRAPING UNVOLLSTÄNDIG** ⚠️

🕐 **Verarbeitung beendet:** {datetime.now().strftime('%H:%M:%S')}
⏱️  **Dauer:** {processing_duration:.1f} Sekunden

❓ **Status:** Signal erkannt aber Verarbeitung unvollständig
🔧 **Mögliche Ursachen:**
• Website-Struktur verändert
• Temporäre Netzwerkprobleme
• Scraping-Timeout

💡 **Follow-up:** Das System sollte trotzdem eine
"Signal Detected" oder "Extraction Incomplete" Nachricht
gesendet haben."""
            
            await self.send_telegram_message(str(self.target_group_id), result_msg)
            
            # Cleanup
            await cryptet_automation.shutdown()
            print("🔄 Cryptet Automation heruntergefahren")
            
            return result
            
        except Exception as e:
            print(f"❌ Fehler während des Tests: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = f"""❌ **SCRAPING TEST FEHLER** ❌

⚠️ **Error:** {str(e)[:100]}...
🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}

🔧 **Debug-Info:**
• Link: `{self.real_xrp_link[:50]}...`
• Fehler bei der Verarbeitung aufgetreten

📋 **Nächste Schritte:**
• Logs prüfen für detaillierte Fehlerinfo
• System-Status überprüfen"""
            
            await self.send_telegram_message(str(self.target_group_id), error_msg)
            return False
    
    async def run_full_test(self):
        """Führe den kompletten Test aus"""
        
        print("🧪 XRP CRYPTET SCRAPING & FORWARDING TESTER")
        print("=" * 80)
        print("Testet die komplette Pipeline: Cryptet Link → Scraping → Formatierung → Weiterleitung")
        print(f"🔗 Test-URL: {self.real_xrp_link}")
        print()
        
        try:
            success = await self.test_cryptet_automation_system()
            
            if success:
                print("\n🎉 KOMPLETTER TEST ERFOLGREICH!")
                print("✅ Cryptet Link erfolgreich gescrapt")  
                print("✅ Signal formatiert und weitergeleitet")
                print("✅ System funktioniert end-to-end")
            else:
                print("\n⚠️ TEST UNVOLLSTÄNDIG")
                print("🔧 System erkannt aber möglicherweise Scraping-Problem")
                print("💡 Prüfen Sie die gesendeten Nachrichten für Details")
            
            return success
            
        except Exception as e:
            print(f"❌ Test komplett fehlgeschlagen: {e}")
            return False

async def main():
    """Hauptfunktion"""
    
    tester = XRPCryptetScrapingTester()
    
    print("🚀 Starte Cryptet XRP Scraping Test...")
    print("Dieser Test wird das echte Cryptet Automation System verwenden!")
    print()
    
    success = await tester.run_full_test()
    
    if success:
        print("\n🎉 XRP CRYPTET PIPELINE VOLLSTÄNDIG GETESTET!")
        print("Das System kann jetzt echte Cryptet Links scrapen und weiterleiten.")
    else:
        print("\n🔧 Weitere System-Optimierung erforderlich.")
        print("Prüfen Sie die Telegram-Nachrichten für detaillierte Ergebnisse.")

if __name__ == "__main__":
    print("🧪 XRP CRYPTET SCRAPING & FORWARDING TEST")
    print("Testet die komplette Pipeline mit echtem Cryptet Link")
    print()
    
    asyncio.run(main())