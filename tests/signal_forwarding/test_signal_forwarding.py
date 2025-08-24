#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Skript zum Abrufen, Parsen und Weiterleiten der neuesten Signale
Holt das neueste Signal aus der VIP-Gruppe und von Cryptet und leitet sie weiter
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from telethon import TelegramClient
import requests

# Füge src Verzeichnis zum Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.signal_forwarder import SignalForwarder
from core.cryptet_automation import CryptetAutomation
from core.cryptet_signal_parser import CryptetSignalProcessor
from utils.audit_logger import AuditLogger

class SignalForwardingTester:
    """Test-Klasse für Signal-Weiterleitung"""
    
    def __init__(self):
        # API Credentials
        self.api_id = 26708757
        self.api_hash = "e58c6204a1478da2b764d5fceff846e5"
        self.bot_token = "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw"
        
        # Session verwenden
        self.session_name = "user_telegram_session"
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Chat-Konfigurationen
        self.vip_group_id = -2299206473  # VIP Signal Group
        self.cryptet_channel_id = -1001804143400  # Cryptet Official Channel
        self.target_group_id = -1002773853382  # PH FUTURES VIP (Zielgruppe)
        
        # Komponenten initialisieren
        self.signal_forwarder = None
        self.cryptet_automation = None
        self.audit_logger = AuditLogger()
        
    async def initialize(self) -> bool:
        """Initialisiere alle Komponenten"""
        try:
            print("🚀 INITIALISIERUNG STARTET...")
            print("=" * 60)
            
            # Telegram Client starten
            await self.client.start()
            me = await self.client.get_me()
            print(f"✅ Telegram User API verbunden: {me.first_name} (@{me.username})")
            
            # Signal Forwarder initialisieren
            self.signal_forwarder = SignalForwarder(
                send_telegram_callback=self.send_telegram_message,
                audit_logger=self.audit_logger
            )
            print("✅ Signal Forwarder initialisiert")
            
            # Cryptet Automation initialisieren
            self.cryptet_automation = CryptetAutomation(
                send_message_callback=self.send_telegram_message
            )
            
            # Cryptet Automation starten
            cryptet_success = await self.cryptet_automation.initialize()
            if cryptet_success:
                print("✅ Cryptet Automation initialisiert")
            else:
                print("⚠️ Cryptet Automation konnte nicht initialisiert werden")
            
            print("✅ Alle Komponenten erfolgreich initialisiert\n")
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei der Initialisierung: {e}")
            return False
    
    async def send_telegram_message(self, chat_id: str, message: str) -> None:
        """Sende Nachricht über Telegram Bot API"""
        try:
            # Verwende Bot API für das Senden
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                print(f"✅ Nachricht erfolgreich gesendet an {chat_id}")
            else:
                print(f"❌ Fehler beim Senden an {chat_id}: {response.text}")
                
        except Exception as e:
            print(f"❌ Telegram Send Error: {e}")
    
    async def get_latest_vip_signal(self) -> Optional[Dict[str, Any]]:
        """Hole das neueste Signal aus der VIP-Gruppe"""
        try:
            print("🔍 SUCHE NACH VIP-GRUPPENSIGNAL...")
            print("-" * 40)
            
            entity = await self.client.get_entity(self.vip_group_id)
            print(f"📊 Verbindung zur VIP-Gruppe: {entity.title}")
            
            # Hole die letzten 10 Nachrichten
            messages = []
            async for message in self.client.iter_messages(entity, limit=10):
                if message.text and message.text.strip():
                    messages.append({
                        "id": message.id,
                        "text": message.text,
                        "date": message.date,
                        "sender_id": message.sender_id if message.sender else None
                    })
            
            print(f"📨 {len(messages)} Nachrichten gefunden")
            
            # Suche nach Signal-Pattern
            for msg in messages:
                text = msg["text"]
                
                # Prüfe ob es ein VIP-Signal ist (unser Format)
                if self.signal_forwarder._is_signal(text):
                    print(f"🎯 VIP-Signal gefunden (ID: {msg['id']})")
                    print(f"📅 Datum: {msg['date']}")
                    print(f"📝 Text (erste 100 Zeichen): {text[:100]}...")
                    
                    # Parse das Signal
                    signal_data = self.signal_forwarder._parse_signal(text)
                    if signal_data:
                        signal_data["message_id"] = msg["id"]
                        signal_data["timestamp"] = msg["date"]
                        signal_data["source_chat"] = "VIP_GROUP"
                        return signal_data
            
            print("❌ Kein VIP-Signal in den letzten 10 Nachrichten gefunden")
            return None
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen des VIP-Signals: {e}")
            return None
    
    async def get_latest_cryptet_signal(self) -> Optional[Dict[str, Any]]:
        """Hole das neueste Signal vom Cryptet-Kanal"""
        try:
            print("🔍 SUCHE NACH CRYPTET-SIGNAL...")
            print("-" * 40)
            
            entity = await self.client.get_entity(self.cryptet_channel_id)
            print(f"📊 Verbindung zum Cryptet-Kanal: {entity.title}")
            
            # Hole die letzten 5 Nachrichten
            messages = []
            async for message in self.client.iter_messages(entity, limit=5):
                if message.text and message.text.strip():
                    messages.append({
                        "id": message.id,
                        "text": message.text,
                        "date": message.date,
                        "entities": message.entities or []
                    })
            
            print(f"📨 {len(messages)} Nachrichten gefunden")
            
            # Suche nach Cryptet-Links oder Crypto-Symbolen
            for msg in messages:
                text = msg["text"]
                
                # Prüfe auf Cryptet-Link oder Crypto-Symbol
                if "cryptet.com" in text.lower() or any(symbol in text.upper() for symbol in ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT"]):
                    print(f"🎯 Cryptet-Signal gefunden (ID: {msg['id']})")
                    print(f"📅 Datum: {msg['date']}")
                    print(f"📝 Text: {text}")
                    
                    # Prüfe auf URLs in Entities
                    urls = []
                    for entity in msg["entities"]:
                        if hasattr(entity, 'url') and entity.url:
                            urls.append(entity.url)
                    
                    signal_data = {
                        "message_id": msg["id"],
                        "text": text,
                        "timestamp": msg["date"],
                        "source_chat": "CRYPTET_CHANNEL",
                        "urls": urls
                    }
                    
                    return signal_data
            
            print("❌ Kein Cryptet-Signal in den letzten 5 Nachrichten gefunden")
            return None
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen des Cryptet-Signals: {e}")
            return None
    
    async def process_and_forward_vip_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Verarbeite und leite VIP-Signal weiter"""
        try:
            print("🔄 VERARBEITUNG VIP-SIGNAL...")
            print("-" * 40)
            
            # Signal formatieren
            formatted_signal = self.signal_forwarder._format_signal(signal_data)
            
            # Test-Header hinzufügen
            test_message = f"""🧪 **VIP SIGNAL TEST** 🧪

📅 **Original Datum:** {signal_data.get('timestamp')}
🆔 **Original ID:** {signal_data.get('message_id')}
📊 **Symbol:** {signal_data.get('symbol')}
🎯 **Richtung:** {signal_data.get('direction')}

{formatted_signal}

✅ **Status:** Test-Weiterleitung erfolgreich"""
            
            # An Zielgruppe senden
            await self.send_telegram_message(str(self.target_group_id), test_message)
            print("✅ VIP-Signal erfolgreich weitergeleitet")
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei VIP-Signal-Verarbeitung: {e}")
            return False
    
    async def process_and_forward_cryptet_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Verarbeite und leite Cryptet-Signal weiter"""
        try:
            print("🔄 VERARBEITUNG CRYPTET-SIGNAL...")
            print("-" * 40)
            
            message_text = signal_data.get("text", "")
            
            # Versuche Cryptet-Automation zu verwenden
            metadata = {
                "chat_id": self.cryptet_channel_id,
                "source_url": signal_data.get("urls", [None])[0] if signal_data.get("urls") else None
            }
            
            # Test-Nachricht für Cryptet-Verarbeitung
            test_header = f"""🧪 **CRYPTET SIGNAL TEST** 🧪

📅 **Original Datum:** {signal_data.get('timestamp')}
🆔 **Original ID:** {signal_data.get('message_id')}
📝 **Original Text:** {message_text[:100]}...

🔄 **Verarbeitung startet...**"""
            
            await self.send_telegram_message(str(self.target_group_id), test_header)
            
            # Verwende Cryptet Automation
            if self.cryptet_automation:
                success = await self.cryptet_automation.process_telegram_message(message_text, metadata)
                
                if success:
                    print("✅ Cryptet-Signal erfolgreich verarbeitet")
                    return True
                else:
                    print("⚠️ Cryptet-Signal konnte nicht automatisch verarbeitet werden")
            
            # Fallback: Manueller Parse-Versuch
            processor = CryptetSignalProcessor()
            parsed_signal = processor.formatter.parse_raw_signal(message_text)
            
            if parsed_signal:
                formatted_signal = processor.process_signal(parsed_signal)
                
                if formatted_signal:
                    fallback_message = f"""🔄 **CRYPTET FALLBACK VERARBEITUNG** 🔄

{formatted_signal}

⚠️ **Note:** Signal wurde manuell geparst (Scraping fehlgeschlagen)"""
                    
                    await self.send_telegram_message(str(self.target_group_id), fallback_message)
                    print("✅ Cryptet-Signal mit Fallback verarbeitet")
                    return True
            
            # Wenn alles fehlschlägt, informiere darüber
            error_message = f"""❌ **CRYPTET VERARBEITUNG FEHLGESCHLAGEN** ❌

📝 **Original:** {message_text}
🔗 **URLs:** {signal_data.get('urls', [])}

⚠️ **Problem:** Konnte Signal nicht automatisch verarbeiten
🔧 **Action:** Manuelle Überprüfung erforderlich"""
            
            await self.send_telegram_message(str(self.target_group_id), error_message)
            print("❌ Cryptet-Signal konnte nicht verarbeitet werden")
            return False
            
        except Exception as e:
            print(f"❌ Fehler bei Cryptet-Signal-Verarbeitung: {e}")
            error_message = f"""❌ **CRYPTET FEHLER** ❌

⚠️ **Error:** {str(e)}
📝 **Signal:** {signal_data.get('text', '')[:100]}...

🔧 **Bitte manuell überprüfen**"""
            
            await self.send_telegram_message(str(self.target_group_id), error_message)
            return False
    
    async def run_test(self) -> None:
        """Führe den kompletten Test durch"""
        try:
            print("🧪 SIGNAL FORWARDING TEST STARTET")
            print("=" * 60)
            print(f"🕐 Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Initialisierung
            if not await self.initialize():
                print("❌ Initialisierung fehlgeschlagen - Test abgebrochen")
                return
            
            # Test-Start-Nachricht senden
            start_message = f"""🧪 **SIGNAL FORWARDING TEST GESTARTET** 🧪

🕐 **Zeit:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 **Ziel:** Neueste Signale von VIP-Gruppe und Cryptet weiterleiten

📊 **Quellen:**
• VIP Group: {self.vip_group_id}
• Cryptet Channel: {self.cryptet_channel_id}

🔄 **Status:** Test läuft..."""
            
            await self.send_telegram_message(str(self.target_group_id), start_message)
            
            # 1. VIP-Signal abrufen und weiterleiten
            print("\n" + "="*60)
            vip_signal = await self.get_latest_vip_signal()
            
            vip_success = False
            if vip_signal:
                vip_success = await self.process_and_forward_vip_signal(vip_signal)
            else:
                no_vip_message = """⚠️ **KEIN VIP-SIGNAL GEFUNDEN** ⚠️

🔍 **Gesucht:** Signal-Pattern in VIP-Gruppe
📊 **Ergebnis:** Keine Signale in den letzten 10 Nachrichten

💡 **Hinweis:** Möglicherweise sind keine neuen Signale verfügbar"""
                
                await self.send_telegram_message(str(self.target_group_id), no_vip_message)
            
            # 2. Cryptet-Signal abrufen und weiterleiten
            print("\n" + "="*60)
            cryptet_signal = await self.get_latest_cryptet_signal()
            
            cryptet_success = False
            if cryptet_signal:
                cryptet_success = await self.process_and_forward_cryptet_signal(cryptet_signal)
            else:
                no_cryptet_message = """⚠️ **KEIN CRYPTET-SIGNAL GEFUNDEN** ⚠️

🔍 **Gesucht:** Cryptet-Links oder Crypto-Symbole
📊 **Ergebnis:** Keine Signale in den letzten 5 Nachrichten

💡 **Hinweis:** Möglicherweise sind keine neuen Signale verfügbar"""
                
                await self.send_telegram_message(str(self.target_group_id), no_cryptet_message)
            
            # Test-Zusammenfassung senden
            summary_message = f"""📊 **TEST-ZUSAMMENFASSUNG** 📊

🕐 **Abgeschlossen:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 **Ergebnisse:**
• VIP Signal: {'✅ Erfolgreich' if vip_success else '❌ Fehlgeschlagen/Nicht gefunden'}
• Cryptet Signal: {'✅ Erfolgreich' if cryptet_success else '❌ Fehlgeschlagen/Nicht gefunden'}

📊 **Gesamtergebnis:** {'✅ Test erfolgreich' if (vip_success or cryptet_success) else '⚠️ Keine Signale verarbeitet'}

💡 **Next Steps:** System ist bereit für Live-Betrieb"""
            
            await self.send_telegram_message(str(self.target_group_id), summary_message)
            
            print("\n" + "="*60)
            print("🏁 TEST ABGESCHLOSSEN")
            print(f"VIP Signal: {'✅' if vip_success else '❌'}")
            print(f"Cryptet Signal: {'✅' if cryptet_success else '❌'}")
            
        except Exception as e:
            print(f"❌ Test-Fehler: {e}")
            
            error_message = f"""❌ **TEST FEHLER** ❌

⚠️ **Error:** {str(e)}
🕐 **Zeit:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔧 **Bitte Logs überprüfen**"""
            
            try:
                await self.send_telegram_message(str(self.target_group_id), error_message)
            except:
                pass
            
        finally:
            # Cleanup
            if self.cryptet_automation:
                await self.cryptet_automation.shutdown()
            
            await self.client.disconnect()
            print("✅ Alle Verbindungen geschlossen")

async def main():
    """Hauptfunktion"""
    tester = SignalForwardingTester()
    await tester.run_test()

if __name__ == "__main__":
    print("🧪 SIGNAL FORWARDING TEST")
    print("Testet das Abrufen und Weiterleiten von Signalen aus VIP-Gruppe und Cryptet")
    print()
    
    asyncio.run(main())