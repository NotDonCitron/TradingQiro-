#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test: Verarbeitung der letzten 4 Signale aus der echten Cryptet Gruppe
Holt echte Signale und verarbeitet sie durch das komplette System
"""

import asyncio
import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class Last4CryptetSignalsTester:
    """Test-Klasse für die letzten 4 echten Cryptet Signale"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw")
        self.target_group_id = int(os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382"))
        
        # Cryptet Channel ID (gemäß Spezifikation)
        self.cryptet_channel_id = -1001804143400
        
        # API Credentials für Telethon
        self.api_id = int(os.getenv("TELEGRAM_API_ID", "26708757"))
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "e58c6204a1478da2b764d5fceff846e5")
        
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
                print(f"❌ Fehler beim Senden: {response.status_code}")
            return success
                
        except Exception as e:
            print(f"❌ Telegram Send Error: {e}")
            return False
    
    async def fetch_last_cryptet_signals(self, limit=4):
        """Hole die letzten Signale aus der echten Cryptet Gruppe"""
        
        print("📡 HOLE ECHTE SIGNALE AUS CRYPTET GRUPPE")
        print("=" * 60)
        print(f"🎯 Ziel: Letzte {limit} Signale aus Cryptet Channel")
        print(f"📱 Channel ID: {self.cryptet_channel_id}")
        print()
        
        try:
            from telethon import TelegramClient
            
            # Verwende die bestehende User-Session
            client = TelegramClient('user_telegram_session', self.api_id, self.api_hash)
            
            print("🔗 Verbinde mit Telegram...")
            await client.start()
            
            me = await client.get_me()
            print(f"✅ Verbunden als: {me.first_name} {me.last_name or ''}")
            
            # Hole Entität für Cryptet Channel
            print(f"📋 Zugriff auf Cryptet Channel...")
            entity = await client.get_entity(self.cryptet_channel_id)
            print(f"✅ Verbunden mit: {entity.title}")
            
            # Sammle die letzten Nachrichten
            cryptet_signals = []
            message_count = 0
            
            print(f"🔍 Suche nach den letzten {limit} Cryptet-Signalen...")
            
            async for message in client.iter_messages(entity, limit=50):  # Mehr Nachrichten prüfen
                message_count += 1
                
                if not message.text:
                    continue
                
                # Prüfe ob es ein Cryptet Signal ist (enthält cryptet.com Link oder Crypto-Symbol)
                text = message.text.lower()
                is_cryptet_signal = (
                    'cryptet.com' in text or
                    any(symbol in message.text.upper() for symbol in 
                        ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'SOL/USDT', 'DOGE/USDT', 
                         'ADA/USDT', 'MATIC/USDT', 'DOT/USDT', 'LINK/USDT', 'UNI/USDT'])
                )
                
                if is_cryptet_signal:
                    # Extrahiere URLs aus Entities
                    extracted_urls = []
                    if message.entities:
                        for entity_obj in message.entities:
                            if hasattr(entity_obj, 'url') and entity_obj.url:
                                extracted_urls.append(entity_obj.url)
                    
                    signal_data = {
                        'message_id': message.id,
                        'text': message.text,
                        'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'entities': extracted_urls,
                        'raw_entities': message.entities or []
                    }
                    
                    cryptet_signals.append(signal_data)
                    
                    print(f"📊 Signal {len(cryptet_signals)} gefunden: ID {message.id} - {message.date.strftime('%H:%M:%S')}")
                    print(f"   Text: {message.text[:80]}...")
                    print(f"   URLs: {extracted_urls}")
                    
                    if len(cryptet_signals) >= limit:
                        break
            
            await client.disconnect()
            
            print(f"\n📊 ERGEBNIS:")
            print(f"   Nachrichten durchsucht: {message_count}")
            print(f"   Cryptet-Signale gefunden: {len(cryptet_signals)}")
            
            return cryptet_signals
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen der Signale: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def process_signal_through_system(self, signal_data, signal_number):
        """Verarbeite ein Signal durch das komplette Cryptet System"""
        
        print(f"\n🔄 VERARBEITE SIGNAL {signal_number}")
        print("-" * 40)
        print(f"📨 Nachricht ID: {signal_data['message_id']}")
        print(f"📅 Zeit: {signal_data['date']}")
        print(f"📝 Text: {signal_data['text'][:100]}...")
        
        try:
            # Füge src zum Python Path hinzu
            if "src" not in sys.path:
                sys.path.insert(0, "src")
                sys.path.insert(0, ".")
            
            from src.core.cryptet_automation import CryptetAutomation
            
            # Initialisiere Cryptet Automation (einmalig pro Signal)
            cryptet_automation = CryptetAutomation(self.send_telegram_message)
            success = await cryptet_automation.initialize()
            
            if not success:
                print(f"❌ Cryptet Automation konnte nicht initialisiert werden")
                return False
            
            # Bereite Metadaten vor
            metadata = {
                'chat_id': self.cryptet_channel_id,
                'message_id': signal_data['message_id'],
                'timestamp': signal_data['date'],
                'extracted_urls': signal_data['entities'],
                'entities': signal_data['raw_entities'],
                'source': 'cryptet_channel_real'
            }
            
            # Sende Verarbeitungs-Notification
            processing_msg = f"""🔄 **SIGNAL {signal_number} PROCESSING** 🔄

📊 **Cryptet Signal #{signal_number}**
🆔 **Message ID:** {signal_data['message_id']}
📅 **Zeit:** {signal_data['date']}

📝 **Inhalt:** {signal_data['text'][:150]}...

🔗 **URLs:** {len(signal_data['entities'])} gefunden
⏳ **Status:** Verarbeitung läuft..."""
            
            await self.send_telegram_message(str(self.target_group_id), processing_msg)
            
            # Verarbeite durch Cryptet System
            print("🌐 Starte Verarbeitung...")
            start_time = asyncio.get_event_loop().time()
            
            result = await cryptet_automation.process_telegram_message(signal_data['text'], metadata)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            print(f"⏱️  Verarbeitung abgeschlossen in {processing_time:.1f}s")
            print(f"📊 Ergebnis: {'✅ Erfolgreich' if result else '❌ Fehlgeschlagen'}")
            
            # Kurz warten für Background-Processing
            await asyncio.sleep(3)
            
            # Cleanup
            await cryptet_automation.shutdown()
            
            return result
            
        except Exception as e:
            print(f"❌ Fehler bei Signal {signal_number}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_batch_processing(self):
        """Führe die Batch-Verarbeitung der letzten 4 Signale aus"""
        
        print("🚀 BATCH-VERARBEITUNG DER LETZTEN 4 CRYPTET SIGNALE")
        print("=" * 80)
        print("Holt echte Signale aus Cryptet Gruppe und verarbeitet sie komplett")
        print()
        
        # Sende Start-Nachricht
        start_msg = f"""🚀 **BATCH CRYPTET SIGNAL PROCESSING** 🚀

🕐 **Start:** {datetime.now().strftime('%H:%M:%S')}
🎯 **Ziel:** Verarbeitung der letzten 4 echten Cryptet-Signale

📋 **Pipeline pro Signal:**
1. 📡 Signal aus Cryptet Channel abrufen
2. 🔍 Link/Symbol-Erkennung  
3. 🌐 Automatisches Scraping
4. 📊 Signal-Formatierung
5. 📤 Weiterleitung an Zielgruppe

🔄 **Status:** Abrufen der Signale..."""
        
        await self.send_telegram_message(str(self.target_group_id), start_msg)
        
        try:
            # 1. Hole die letzten 4 Signale
            signals = await self.fetch_last_cryptet_signals(limit=4)
            
            if not signals:
                error_msg = """❌ **KEINE SIGNALE GEFUNDEN** ❌

⚠️ **Problem:** Keine Cryptet-Signale in den letzten 50 Nachrichten gefunden

🔧 **Mögliche Ursachen:**
• Keine neuen Signale im Channel
• Zugriffsprobleme auf Cryptet Channel
• Signale in anderem Format

💡 **Lösung:** Prüfen Sie den Cryptet Channel manuell"""
                
                await self.send_telegram_message(str(self.target_group_id), error_msg)
                return False
            
            print(f"\n✅ {len(signals)} Signale abgerufen, starte Verarbeitung...")
            
            # Sende Update über gefundene Signale
            signals_msg = f"""📊 **{len(signals)} SIGNALE ABGERUFEN** 📊

✅ **Erfolgreich abgerufen:** {len(signals)} Cryptet-Signale
📅 **Zeitraum:** {signals[-1]['date']} bis {signals[0]['date']}

🔄 **Nächster Schritt:** Einzelverarbeitung startet..."""
            
            await self.send_telegram_message(str(self.target_group_id), signals_msg)
            
            # 2. Verarbeite jedes Signal einzeln
            results = []
            successful_processings = 0
            
            for i, signal in enumerate(signals, 1):
                print(f"\n{'='*20} SIGNAL {i}/{len(signals)} {'='*20}")
                
                result = await self.process_signal_through_system(signal, i)
                results.append({
                    'signal_number': i,
                    'message_id': signal['message_id'],
                    'success': result,
                    'text_preview': signal['text'][:50] + '...'
                })
                
                if result:
                    successful_processings += 1
                
                # Pause zwischen Signalen
                if i < len(signals):
                    print("⏳ Pause zwischen Signalen...")
                    await asyncio.sleep(5)
            
            # 3. Sende finale Zusammenfassung
            summary_msg = f"""📊 **BATCH PROCESSING ABGESCHLOSSEN** 📊

🕐 **Ende:** {datetime.now().strftime('%H:%M:%S')}
📈 **Erfolgsrate:** {successful_processings}/{len(signals)} Signale

✅ **Erfolgreich verarbeitet:** {successful_processings}
⚠️ **Fehlgeschlagen:** {len(signals) - successful_processings}

📋 **Detaillierte Ergebnisse:**"""
            
            for result in results:
                status_emoji = "✅" if result['success'] else "❌"
                summary_msg += f"\n{status_emoji} Signal {result['signal_number']}: {result['text_preview']}"
            
            if successful_processings == len(signals):
                summary_msg += f"\n\n🎉 **ALLE SIGNALE ERFOLGREICH VERARBEITET!**\nAlle {len(signals)} Cryptet-Signale wurden gescrapt und weitergeleitet."
            elif successful_processings > 0:
                summary_msg += f"\n\n⚠️ **TEILWEISE ERFOLGREICH**\n{successful_processings} von {len(signals)} Signalen verarbeitet."
            else:
                summary_msg += f"\n\n❌ **BATCH FEHLGESCHLAGEN**\nKeines der {len(signals)} Signale konnte verarbeitet werden."
            
            await self.send_telegram_message(str(self.target_group_id), summary_msg)
            
            return successful_processings == len(signals)
            
        except Exception as e:
            print(f"❌ Batch-Processing fehlgeschlagen: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = f"""❌ **BATCH PROCESSING FEHLER** ❌

⚠️ **Error:** {str(e)[:100]}...
🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}

🔧 **Weitere Debugging erforderlich**"""
            
            await self.send_telegram_message(str(self.target_group_id), error_msg)
            return False

async def main():
    """Hauptfunktion"""
    
    tester = Last4CryptetSignalsTester()
    
    print("🚀 STARTE BATCH-VERARBEITUNG DER LETZTEN 4 CRYPTET SIGNALE")
    print("=" * 80)
    print("Holt echte Signale aus der Cryptet Gruppe und verarbeitet sie komplett")
    print()
    
    success = await tester.run_batch_processing()
    
    if success:
        print("\n🎉 BATCH-VERARBEITUNG VOLLSTÄNDIG ERFOLGREICH!")
        print("✅ Alle 4 Signale wurden erfolgreich gescrapt und weitergeleitet")
        print("✅ Das System funktioniert einwandfrei mit echten Cryptet-Daten")
    else:
        print("\n⚠️ BATCH-VERARBEITUNG UNVOLLSTÄNDIG")
        print("🔧 Prüfen Sie die Telegram-Nachrichten für detaillierte Ergebnisse")

if __name__ == "__main__":
    print("🚀 LAST 4 CRYPTET SIGNALS BATCH PROCESSOR")
    print("Verarbeitet die letzten 4 echten Signale aus der Cryptet Gruppe")
    print()
    
    asyncio.run(main())