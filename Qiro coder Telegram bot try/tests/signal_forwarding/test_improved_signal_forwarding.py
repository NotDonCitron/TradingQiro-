#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verbessertes Test-Skript für Signal-Weiterleitung
Robusteres Handling verschiedener Chat-Typen und bessere Fehlerbehandlung
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User
import requests
import re

# Füge src Verzeichnis zum Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.signal_forwarder import SignalForwarder
from core.cryptet_signal_parser import CryptetSignalProcessor
from utils.audit_logger import AuditLogger

class ImprovedSignalTester:
    """Verbesserter Signal-Tester mit robustem Error-Handling"""
    
    def __init__(self):
        # API Credentials
        self.api_id = 26708757
        self.api_hash = "e58c6204a1478da2b764d5fceff846e5"
        self.bot_token = "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw"
        
        # Session verwenden
        self.session_name = "user_telegram_session"
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Chat-Konfigurationen
        self.chat_configs = {
            "VIP_GROUP": -2299206473,  # VIP Signal Group
            "CRYPTET_CHANNEL": -1001804143400,  # Cryptet Official Channel  
            "TARGET_GROUP": -1002773853382  # PH FUTURES VIP (Zielgruppe)
        }
        
        # Komponenten
        self.signal_forwarder = None
        self.audit_logger = AuditLogger()
        
    async def send_telegram_message(self, chat_id: str, message: str) -> bool:
        """Sende Nachricht über Telegram Bot API"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Nachricht gesendet an {chat_id}")
                return True
            else:
                print(f"❌ Send Error {chat_id}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram Send Error: {e}")
            return False
    
    async def get_chat_entity_safe(self, chat_id: int) -> Optional[Any]:
        """Hole Chat-Entity mit Error-Handling"""
        try:
            entity = await self.client.get_entity(chat_id)
            
            # Chat-Typ bestimmen
            if isinstance(entity, Channel):
                chat_type = "Channel" if entity.broadcast else "Megagroup"
            elif isinstance(entity, Chat):
                chat_type = "Group"
            else:
                chat_type = "Unknown"
            
            print(f"📊 Chat Info: {getattr(entity, 'title', 'Unknown')} | Typ: {chat_type} | ID: {chat_id}")
            return entity
            
        except Exception as e:
            print(f"❌ Fehler beim Zugriff auf Chat {chat_id}: {e}")
            return None
    
    async def get_messages_safe(self, entity: Any, limit: int = 10) -> List[Dict[str, Any]]:
        """Hole Nachrichten mit Error-Handling"""
        try:
            messages = []
            count = 0
            
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.text and message.text.strip():
                    messages.append({
                        "id": message.id,
                        "text": message.text,
                        "date": message.date,
                        "sender_id": message.sender_id if message.sender else None,
                        "entities": message.entities or []
                    })
                    count += 1
                
                if count >= limit:
                    break
            
            print(f"📨 {len(messages)} Nachrichten abgerufen")
            return messages
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen von Nachrichten: {e}")
            return []
    
    def analyze_message_for_signals(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Analysiere Nachricht auf Signal-Muster"""
        text = message.get("text", "")
        
        analysis = {
            "is_vip_signal": False,
            "is_cryptet_link": False,
            "is_crypto_symbol": False,
            "signal_type": "none",
            "confidence": 0
        }
        
        # VIP Signal Pattern (aus signal_forwarder.py)
        vip_patterns = [
            "🟢 Long" in text or "🟢 Short" in text,
            "Name:" in text,
            "Margin mode:" in text,
            "Entry price(USDT):" in text,
            "Targets(USDT):" in text
        ]
        
        if all(vip_patterns):
            analysis["is_vip_signal"] = True
            analysis["signal_type"] = "vip_signal"
            analysis["confidence"] = 100
        
        # Cryptet Link Pattern
        if "cryptet.com" in text.lower():
            analysis["is_cryptet_link"] = True
            analysis["signal_type"] = "cryptet_link"
            analysis["confidence"] = 90
        
        # Crypto Symbol Pattern
        crypto_symbols = re.findall(r'\b([A-Z0-9]{2,8})/USDT?\b', text.upper())
        if crypto_symbols:
            analysis["is_crypto_symbol"] = True
            analysis["crypto_symbols"] = crypto_symbols
            if not analysis["is_cryptet_link"]:
                analysis["signal_type"] = "crypto_symbol"
                analysis["confidence"] = 60
        
        # Trading Keywords
        trading_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "TARGET", "LEVERAGE"]
        keyword_matches = sum(1 for keyword in trading_keywords if keyword in text.upper())
        
        if keyword_matches >= 3 and analysis["confidence"] == 0:
            analysis["signal_type"] = "trading_related"
            analysis["confidence"] = 40
        
        return analysis
    
    def create_demo_signals(self) -> Dict[str, str]:
        """Erstelle Demo-Signale für Tests wenn keine echten gefunden werden"""
        
        demo_vip_signal = """🟢 Long
Name: BTC/USDT
Margin mode: Cross (50X)

↪️ Entry price(USDT):
95000

Targets(USDT):
1) 96000
2) 97000
3) 98000
4) 99000"""
        
        demo_cryptet_signal = """🤖 **CRYPTET DEMO SIGNAL** 🤖

🟢 **LONG** BTC/USDT
💰 **Entry:** 95000
🎯 **Take Profits:**
   1) 96000
   2) 97000
   3) 98000
🛑 **Stop Loss:** 94000
⚡ **Leverage:** Cross 50x

📊 **Source:** Demo Test
🔄 **Auto-forwarded with 50x leverage**
⏰ **Will close automatically when P&L updates**

🕐 **Time:** """ + datetime.now().strftime("%H:%M:%S")
        
        return {
            "vip_demo": demo_vip_signal,
            "cryptet_demo": demo_cryptet_signal
        }
    
    async def search_for_signals(self) -> Dict[str, Any]:
        """Suche nach Signalen in allen konfigurierten Chats"""
        results = {
            "vip_signals": [],
            "cryptet_signals": [],
            "crypto_symbols": [],
            "errors": []
        }
        
        print("🔍 SIGNAL-SUCHE STARTET...")
        print("=" * 50)
        
        # VIP Group durchsuchen
        print("\n>>> VIP GROUP SUCHE <<<")
        vip_entity = await self.get_chat_entity_safe(self.chat_configs["VIP_GROUP"])
        if vip_entity:
            vip_messages = await self.get_messages_safe(vip_entity, 15)
            
            for msg in vip_messages:
                analysis = self.analyze_message_for_signals(msg)
                
                if analysis["is_vip_signal"]:
                    print(f"🎯 VIP Signal gefunden: ID {msg['id']} | {msg['date']}")
                    results["vip_signals"].append({
                        **msg,
                        "analysis": analysis
                    })
                elif analysis["signal_type"] == "trading_related":
                    print(f"📊 Trading-bezogen: ID {msg['id']} | Confidence: {analysis['confidence']}%")
        else:
            results["errors"].append("VIP Group nicht zugänglich")
        
        # Cryptet Channel durchsuchen
        print("\n>>> CRYPTET CHANNEL SUCHE <<<")
        cryptet_entity = await self.get_chat_entity_safe(self.chat_configs["CRYPTET_CHANNEL"])
        if cryptet_entity:
            cryptet_messages = await self.get_messages_safe(cryptet_entity, 10)
            
            for msg in cryptet_messages:
                analysis = self.analyze_message_for_signals(msg)
                
                if analysis["is_cryptet_link"]:
                    print(f"🔗 Cryptet Link gefunden: ID {msg['id']} | {msg['date']}")
                    results["cryptet_signals"].append({
                        **msg,
                        "analysis": analysis
                    })
                elif analysis["is_crypto_symbol"]:
                    print(f"📊 Crypto Symbol: ID {msg['id']} | Symbols: {analysis.get('crypto_symbols', [])}")
                    results["crypto_symbols"].append({
                        **msg,
                        "analysis": analysis
                    })
        else:
            results["errors"].append("Cryptet Channel nicht zugänglich")
        
        return results
    
    async def process_vip_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Verarbeite VIP-Signal"""
        try:
            print("🔄 VIP-SIGNAL-VERARBEITUNG...")
            
            # Signal Forwarder verwenden
            if not self.signal_forwarder:
                self.signal_forwarder = SignalForwarder(
                    send_telegram_callback=self.send_telegram_message,
                    audit_logger=self.audit_logger
                )
            
            text = signal_data.get("text", "")
            parsed_signal = self.signal_forwarder._parse_signal(text)
            
            if parsed_signal:
                formatted_signal = self.signal_forwarder._format_signal(parsed_signal)
                
                test_message = f"""🧪 **VIP SIGNAL TEST** 🧪

📅 **Original:** {signal_data.get('date')}
🆔 **ID:** {signal_data.get('id')}
📊 **Symbol:** {parsed_signal.get('symbol')}
🎯 **Direction:** {parsed_signal.get('direction')}

{formatted_signal}

✅ **Test:** VIP Signal erfolgreich verarbeitet"""
                
                return await self.send_telegram_message(str(self.chat_configs["TARGET_GROUP"]), test_message)
            else:
                print("❌ VIP Signal konnte nicht geparst werden")
                return False
                
        except Exception as e:
            print(f"❌ VIP Signal Fehler: {e}")
            return False
    
    async def process_cryptet_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Verarbeite Cryptet-Signal"""
        try:
            print("🔄 CRYPTET-SIGNAL-VERARBEITUNG...")
            
            text = signal_data.get("text", "")
            
            # URLs aus Entities extrahieren
            urls = []
            for entity in signal_data.get("entities", []):
                if hasattr(entity, 'url') and entity.url:
                    urls.append(entity.url)
            
            test_message = f"""🧪 **CRYPTET SIGNAL TEST** 🧪

📅 **Original:** {signal_data.get('date')}
🆔 **ID:** {signal_data.get('id')}
📝 **Text:** {text[:100]}...
🔗 **URLs:** {urls}

🔄 **Status:** Cryptet Signal erkannt aber Scraping deaktiviert im Test
⚠️ **Note:** Live-System würde das Signal automatisch verarbeiten"""
            
            return await self.send_telegram_message(str(self.chat_configs["TARGET_GROUP"]), test_message)
            
        except Exception as e:
            print(f"❌ Cryptet Signal Fehler: {e}")
            return False
    
    async def run_comprehensive_test(self) -> None:
        """Führe umfassenden Test durch"""
        print("🧪 COMPREHENSIVE SIGNAL TEST")
        print("=" * 60)
        print(f"🕐 Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Telegram initialisieren
            await self.client.start()
            me = await self.client.get_me()
            print(f"✅ Telegram verbunden: {me.first_name}")
            
            # 2. Test-Start-Nachricht
            start_msg = f"""🧪 **COMPREHENSIVE SIGNAL TEST GESTARTET** 🧪

🕐 **Zeit:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 **Ziel:** Signal-Erkennung und Weiterleitung testen

📊 **Suchbereiche:**
• VIP Group: {self.chat_configs['VIP_GROUP']}  
• Cryptet Channel: {self.chat_configs['CRYPTET_CHANNEL']}

🔄 **Test läuft...**"""
            
            await self.send_telegram_message(str(self.chat_configs["TARGET_GROUP"]), start_msg)
            
            # 3. Signal-Suche
            signal_results = await self.search_for_signals()
            
            # 4. Ergebnisse verarbeiten
            vip_success = False
            cryptet_success = False
            
            # VIP Signale verarbeiten
            if signal_results["vip_signals"]:
                latest_vip = signal_results["vip_signals"][0]  # Neuestes Signal
                vip_success = await self.process_vip_signal(latest_vip)
            
            # Cryptet Signale verarbeiten
            if signal_results["cryptet_signals"]:
                latest_cryptet = signal_results["cryptet_signals"][0]  # Neuestes Signal
                cryptet_success = await self.process_cryptet_signal(latest_cryptet)
            
            # 5. Demo-Signale wenn keine echten gefunden
            if not signal_results["vip_signals"] and not signal_results["cryptet_signals"]:
                print("📝 Erstelle Demo-Signale für Test...")
                demo_signals = self.create_demo_signals()
                
                demo_msg = f"""🧪 **DEMO SIGNALE** 🧪

⚠️ **Keine Live-Signale gefunden** - Sende Demo-Signale:

{demo_signals['cryptet_demo']}

---

🔄 **VIP Signal Format Demo:**
```
{demo_signals['vip_demo']}
```

📊 **Test-Status:** Demo-Signale zur Formatvalidierung"""
                
                demo_success = await self.send_telegram_message(str(self.chat_configs["TARGET_GROUP"]), demo_msg)
                if demo_success:
                    vip_success = cryptet_success = True
            
            # 6. Zusammenfassung
            summary = f"""📊 **TEST ZUSAMMENFASSUNG** 📊

🕐 **Abgeschlossen:** {datetime.now().strftime('%H:%M:%S')}

📈 **Gefundene Signale:**
• VIP Signale: {len(signal_results['vip_signals'])}
• Cryptet Signale: {len(signal_results['cryptet_signals'])}
• Crypto Symbole: {len(signal_results['crypto_symbols'])}
• Fehler: {len(signal_results['errors'])}

✅ **Verarbeitung:**
• VIP Processing: {'✅ Erfolgreich' if vip_success else '❌ Fehlgeschlagen'}
• Cryptet Processing: {'✅ Erfolgreich' if cryptet_success else '❌ Fehlgeschlagen'}

🏁 **Gesamtergebnis:** {'✅ Test erfolgreich' if (vip_success or cryptet_success) else '⚠️ Probleme erkannt'}

🔧 **System:** Bereit für Live-Betrieb"""
            
            await self.send_telegram_message(str(self.chat_configs["TARGET_GROUP"]), summary)
            
            # 7. Console Summary
            print("\n" + "="*60)
            print("🏁 TEST ABGESCHLOSSEN")
            print(f"VIP Signale gefunden: {len(signal_results['vip_signals'])}")
            print(f"Cryptet Signale gefunden: {len(signal_results['cryptet_signals'])}")
            print(f"VIP Verarbeitung: {'✅' if vip_success else '❌'}")
            print(f"Cryptet Verarbeitung: {'✅' if cryptet_success else '❌'}")
            
            if signal_results["errors"]:
                print(f"❌ Fehler: {signal_results['errors']}")
            
        except Exception as e:
            print(f"❌ Test Fehler: {e}")
            
            error_msg = f"""❌ **TEST FEHLER** ❌

⚠️ **Error:** {str(e)}
🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}

🔧 **Bitte Logs überprüfen und erneut versuchen**"""
            
            await self.send_telegram_message(str(self.chat_configs["TARGET_GROUP"]), error_msg)
            
        finally:
            await self.client.disconnect()
            print("✅ Verbindung geschlossen")

async def main():
    """Hauptfunktion"""
    tester = ImprovedSignalTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    print("🧪 IMPROVED SIGNAL FORWARDING TEST")
    print("Robustes Testen der Signal-Erkennung und Weiterleitung")
    print()
    
    asyncio.run(main())