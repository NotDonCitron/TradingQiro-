#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST: SENDE LETZTES VIP-SIGNAL
Holt das neueste Signal aus der VIP-Gruppe und leitet es weiter
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from telethon import TelegramClient
import requests
import re
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Füge src Verzeichnis zum Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.signal_forwarder import SignalForwarder
from utils.audit_logger import AuditLogger

class VIPSignalTester:
    """Testet VIP-Signal-Weiterleitung"""
    
    def __init__(self):
        # API Credentials aus .env
        self.api_id = int(os.getenv("TELEGRAM_API_ID", "26708757"))
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "e58c6204a1478da2b764d5fceff846e5")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw")
        
        # Session
        self.session_name = "user_telegram_session"
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Konfiguration aus .env
        self.vip_group_id = int(os.getenv("VIP_GROUP_ID", "-1001437466982"))
        self.target_group_id = int(os.getenv("TARGET_GROUP_ID", "-1002773853382"))
        
        # VIP-Gruppe Info
        self.vip_group_title = os.getenv("VIP_GROUP_TITLE", "VIP Group")
        
        # Komponenten
        self.signal_forwarder = None
        self.audit_logger = AuditLogger()
    
    async def send_telegram_message(self, chat_id: str, message: str) -> bool:
        """Sende Nachricht über Bot API"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=data, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ Nachricht gesendet an {chat_id}")
                return True
            else:
                print(f"❌ Send Error {chat_id}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram Send Error: {e}")
            return False
    
    def is_trading_signal(self, text: str) -> Dict[str, Any]:
        """Prüfe und bewerte Trading-Signal"""
        if not text:
            return {"is_signal": False, "confidence": 0, "type": "none"}
        
        text_lower = text.lower()
        confidence = 0
        signal_indicators = []
        
        # Crypto-Paare (sehr starker Indikator)
        crypto_match = re.search(r'([A-Z0-9]{2,8})/USDT', text)
        if crypto_match:
            confidence += 30
            signal_indicators.append(f"crypto_pair: {crypto_match.group(1)}")
        
        # Trading-Richtung
        direction_patterns = [
            (r'\b(long|buy)\b', "LONG"),
            (r'\b(short|sell)\b', "SHORT"),
            (r'🟢', "LONG"),
            (r'🔴', "SHORT")
        ]
        
        direction = None
        for pattern, dir_type in direction_patterns:
            if re.search(pattern, text_lower) or re.search(pattern, text):
                confidence += 25
                direction = dir_type
                signal_indicators.append(f"direction: {dir_type}")
                break
        
        # Leverage
        leverage_match = re.search(r'(?:leverage|cross|isolated).*?(\d+)x?|(\d+)x.*?(?:cross|isolated)', text_lower)
        if leverage_match:
            confidence += 20
            leverage = leverage_match.group(1) or leverage_match.group(2)
            signal_indicators.append(f"leverage: {leverage}x")
        
        # Entry Point
        if re.search(r'entry|enter|buy.*at|sell.*at|price.*:', text_lower):
            confidence += 15
            signal_indicators.append("entry_point")
        
        # Take Profit
        if re.search(r'take.*profit|tp|target', text_lower):
            confidence += 10
            signal_indicators.append("take_profit")
        
        # Stop Loss
        if re.search(r'stop.*loss|sl|stop', text_lower):
            confidence += 10
            signal_indicators.append("stop_loss")
        
        # Trading-Emojis
        if re.search(r'📈|📉|⬆️|⬇️|↗️|↘️', text):
            confidence += 5
            signal_indicators.append("trading_emojis")
        
        # Signal-Typ bestimmen
        if confidence >= 60:
            signal_type = "excellent_signal"
        elif confidence >= 40:
            signal_type = "good_signal"
        elif confidence >= 20:
            signal_type = "possible_signal"
        else:
            signal_type = "not_signal"
        
        return {
            "is_signal": confidence >= 40,
            "confidence": min(confidence, 100),
            "type": signal_type,
            "direction": direction,
            "indicators": signal_indicators,
            "crypto_pair": crypto_match.group(1) if crypto_match else None
        }
    
    async def get_latest_vip_signals(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Hole die neuesten Signale aus der VIP-Gruppe"""
        try:
            print(f"\n🔍 SUCHE NEUESTE VIP-SIGNALE")
            print("=" * 40)
            print(f"📊 VIP-Gruppe: {self.vip_group_title}")
            print(f"🆔 ID: {self.vip_group_id}")
            
            # Entity abrufen
            entity = await self.client.get_entity(self.vip_group_id)
            print(f"✅ Verbindung erfolgreich: {getattr(entity, 'title', 'Unknown')}")
            
            signals = []
            message_count = 0
            
            # Durchsuche die letzten Nachrichten
            async for message in self.client.iter_messages(entity, limit=limit):
                message_count += 1
                
                if message.text and message.text.strip():
                    # Analysiere Nachricht
                    signal_analysis = self.is_trading_signal(message.text)
                    
                    if signal_analysis["is_signal"]:
                        signal_data = {
                            "id": message.id,
                            "text": message.text,
                            "date": message.date,
                            "analysis": signal_analysis,
                            "sender_id": message.sender_id if message.sender else None
                        }
                        signals.append(signal_data)
                        
                        print(f"📊 Signal gefunden: ID {message.id}")
                        print(f"   Typ: {signal_analysis['type']} ({signal_analysis['confidence']}%)")
                        print(f"   Paar: {signal_analysis.get('crypto_pair', 'N/A')}")
                        print(f"   Richtung: {signal_analysis.get('direction', 'N/A')}")
                        print(f"   Zeit: {message.date.strftime('%Y-%m-%d %H:%M:%S') if message.date else 'Unknown'}")
            
            print(f"\n📊 Ergebnis: {len(signals)} Signale in {message_count} Nachrichten gefunden")
            
            # Sortiere nach Datum (neueste zuerst)
            signals.sort(key=lambda x: x["date"] if x["date"] else datetime.min, reverse=True)
            
            return signals
            
        except Exception as e:
            print(f"❌ VIP-Signal-Suche Fehler: {e}")
            return []
    
    async def format_and_send_signal(self, signal: Dict[str, Any]) -> bool:
        """Formatiere und sende Signal"""
        try:
            print(f"\n🔄 VERARBEITE SIGNAL {signal['id']}")
            print("=" * 30)
            
            # Signal Forwarder initialisieren falls nicht vorhanden
            if not self.signal_forwarder:
                self.signal_forwarder = SignalForwarder(
                    send_telegram_callback=self.send_telegram_message,
                    audit_logger=self.audit_logger
                )
            
            # Versuche Signal zu parsen und formatieren
            parsed_signal = self.signal_forwarder._parse_signal(signal["text"])
            
            if parsed_signal:
                # Signal erfolgreich geparst
                formatted_signal = self.signal_forwarder._format_signal(parsed_signal)
                
                print("✅ Signal erfolgreich geparst:")
                print(f"   Symbol: {parsed_signal.get('symbol', 'N/A')}")
                print(f"   Richtung: {parsed_signal.get('direction', 'N/A')}")
                print(f"   Leverage: {parsed_signal.get('leverage', 'N/A')}x")
                print(f"   Entry: {parsed_signal.get('entry_price', 'N/A')}")
                print(f"   Targets: {len(parsed_signal.get('targets', []))}")
                
                # Sende formatiertes Signal
                success = await self.send_telegram_message(str(self.target_group_id), formatted_signal)
                
                if success:
                    # Zusätzlicher Info-Report
                    info_msg = f"""📊 **VIP-SIGNAL WEITERGELEITET** 📊

🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}
📊 **Quelle:** {self.vip_group_title}
🆔 **Signal-ID:** {signal['id']}
🎯 **Qualität:** {signal['analysis']['type']} ({signal['analysis']['confidence']}%)
✅ **Status:** Erfolgreich formatiert und gesendet

🔄 **Formatierung:** Original → Cornix-kompatibel
📈 **Bereit für Trading!**"""
                    
                    await self.send_telegram_message(str(self.target_group_id), info_msg)
                    return True
                else:
                    print("❌ Senden des formatierten Signals fehlgeschlagen")
                    return False
            
            else:
                # Parsing fehlgeschlagen, sende Raw-Signal mit Warnung
                print("⚠️ Signal-Parsing fehlgeschlagen, sende Raw-Signal")
                
                raw_msg = f"""⚠️ **RAW VIP-SIGNAL** ⚠️

📊 **Quelle:** {self.vip_group_title}
🆔 **Signal-ID:** {signal['id']}
🕐 **Zeit:** {signal['date'].strftime('%H:%M:%S') if signal['date'] else 'Unknown'}
🎯 **Erkannt als:** {signal['analysis']['type']} ({signal['analysis']['confidence']}%)

**ORIGINAL-SIGNAL:**
```
{signal['text']}
```

⚠️ **Hinweis:** Automatische Formatierung fehlgeschlagen - manuelle Prüfung erforderlich"""
                
                success = await self.send_telegram_message(str(self.target_group_id), raw_msg)
                return success
                
        except Exception as e:
            print(f"❌ Signal-Formatierung Fehler: {e}")
            
            # Sende Fehler-Report
            error_msg = f"""❌ **SIGNAL-VERARBEITUNG FEHLER** ❌

🆔 **Signal-ID:** {signal['id']}
⚠️ **Fehler:** {str(e)}
🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}

**ORIGINAL-TEXT:**
```
{signal['text'][:300]}{'...' if len(signal['text']) > 300 else ''}
```"""
            
            await self.send_telegram_message(str(self.target_group_id), error_msg)
            return False
    
    async def run_vip_signal_test(self) -> None:
        """Führe VIP-Signal-Test durch"""
        print("🚀 VIP-SIGNAL WEITERLEITUNG TEST")
        print("=" * 50)
        
        try:
            # Start-Nachricht
            start_msg = f"""🧪 **VIP-SIGNAL TEST GESTARTET** 🧪

🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}
📊 **VIP-Quelle:** {self.vip_group_title}
🆔 **VIP-ID:** {self.vip_group_id}
🎯 **Zielgruppe:** {self.target_group_id}

🔄 **Status:** Suche nach neuestem Signal..."""
            
            await self.send_telegram_message(str(self.target_group_id), start_msg)
            
            # 1. Telegram starten
            await self.client.start()
            me = await self.client.get_me()
            print(f"✅ Telegram verbunden: {me.first_name}")
            
            # 2. Neueste VIP-Signale abrufen
            signals = await self.get_latest_vip_signals()
            
            if not signals:
                no_signals_msg = f"""⚠️ **KEINE SIGNALE GEFUNDEN** ⚠️

📊 **VIP-Gruppe:** {self.vip_group_title}
🔍 **Durchsucht:** Letzte 20 Nachrichten
❌ **Ergebnis:** Keine Trading-Signale erkannt

💡 **Mögliche Ursachen:**
• Keine aktuellen Signale verfügbar
• Signal-Format nicht erkannt
• Gruppe enthält nur Text/Diskussion

🔄 **Empfehlung:** Später erneut versuchen"""
                
                await self.send_telegram_message(str(self.target_group_id), no_signals_msg)
                return
            
            # 3. Neuestes Signal senden
            latest_signal = signals[0]
            print(f"\n🎯 SENDE NEUESTES SIGNAL: {latest_signal['id']}")
            
            success = await self.format_and_send_signal(latest_signal)
            
            # 4. Zusätzliche Signale anzeigen (falls verfügbar)
            if len(signals) > 1 and success:
                additional_msg = f"""📊 **WEITERE VIP-SIGNALE VERFÜGBAR** 📊

🔢 **Gesamt gefunden:** {len(signals)} Signale
📈 **Qualitätsverteilung:**"""
                
                quality_count = {}
                for signal in signals:
                    q_type = signal['analysis']['type']
                    quality_count[q_type] = quality_count.get(q_type, 0) + 1
                
                for quality, count in quality_count.items():
                    additional_msg += f"\n• {quality}: {count} Signale"
                
                additional_msg += f"""

🎯 **Neuestes Signal gesendet:** {latest_signal['date'].strftime('%H:%M:%S') if latest_signal['date'] else 'Unknown'}
✅ **Status:** VIP-Weiterleitung erfolgreich!"""
                
                await self.send_telegram_message(str(self.target_group_id), additional_msg)
            
            print(f"🎉 VIP-Signal-Test {'erfolgreich' if success else 'mit Problemen'} abgeschlossen")
            
        except Exception as e:
            error_msg = f"""❌ **VIP-SIGNAL TEST FEHLER** ❌

⚠️ **Error:** {str(e)}
🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}

💡 **Empfehlung:** System-Diagnose erforderlich"""
            
            print(f"❌ VIP-Signal Test Fehler: {e}")
            await self.send_telegram_message(str(self.target_group_id), error_msg)
            
        finally:
            await self.client.disconnect()
            print("✅ VIP-Signal-Test abgeschlossen")

async def main():
    """Hauptfunktion"""
    tester = VIPSignalTester()
    await tester.run_vip_signal_test()

if __name__ == "__main__":
    print("🧪 VIP-SIGNAL WEITERLEITUNG TEST")
    print("Holt das neueste VIP-Signal und leitet es weiter")
    print()
    
    asyncio.run(main())