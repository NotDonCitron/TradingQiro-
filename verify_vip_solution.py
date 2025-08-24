#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIP-GRUPPEN LÖSUNG VERIFIKATION
Überprüft ob das VIP-Gruppen-Problem erfolgreich gelöst wurde
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

class VIPSolutionVerifier:
    """Verifiziert die VIP-Gruppen-Lösung"""
    
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
        self.cryptet_channel_id = int(os.getenv("CRYPTET_CHANNEL_ID", "-1001804143400"))
        self.target_group_id = int(os.getenv("TARGET_GROUP_ID", "-1002773853382"))
        
        # Überwachte Chats aus .env
        monitored_chats_str = os.getenv("MONITORED_CHAT_IDS", "")
        self.monitored_chats = []
        if monitored_chats_str:
            try:
                self.monitored_chats = [int(chat_id.strip()) for chat_id in monitored_chats_str.split(",") if chat_id.strip()]
            except ValueError:
                print(f"⚠️ Warnung: Ungültiges MONITORED_CHAT_IDS Format: {monitored_chats_str}")
        
        # VIP-Gruppe Info aus .env
        self.vip_group_title = os.getenv("VIP_GROUP_TITLE", "Unknown VIP Group")
        self.vip_signal_quality = os.getenv("VIP_SIGNAL_QUALITY", "unknown")
        self.vip_signal_score = os.getenv("VIP_SIGNAL_SCORE", "0")
    
    async def send_report(self, message: str) -> bool:
        """Sende Verifikationsbericht"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": str(self.target_group_id),
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Report Send Error: {e}")
            return False
    
    def analyze_message_for_signals(self, text: str) -> Dict[str, Any]:
        """Analysiere Nachricht auf Trading-Signale"""
        if not text:
            return {"is_signal": False, "confidence": 0, "indicators": []}
        
        indicators = []
        confidence = 0
        
        # Crypto-Paare
        if re.search(r'[A-Z]{2,8}/USDT', text):
            indicators.append("crypto_pair")
            confidence += 25
        
        # Trading-Richtung
        if re.search(r'\b(long|short|buy|sell)\b', text, re.IGNORECASE):
            indicators.append("direction")
            confidence += 20
        
        # Leverage
        if re.search(r'leverage|cross|isolated|\d+x', text, re.IGNORECASE):
            indicators.append("leverage")
            confidence += 15
        
        # Entry Points
        if re.search(r'entry|enter|buy.*at|sell.*at', text, re.IGNORECASE):
            indicators.append("entry_point")
            confidence += 20
        
        # Take Profit
        if re.search(r'take.*profit|tp|target', text, re.IGNORECASE):
            indicators.append("take_profit")
            confidence += 15
        
        # Stop Loss
        if re.search(r'stop.*loss|sl|stop', text, re.IGNORECASE):
            indicators.append("stop_loss")
            confidence += 15
        
        # Trading-Emojis
        if re.search(r'🟢|🔴|⬆️|⬇️|↗️|↘️|📈|📉', text):
            indicators.append("trading_emojis")
            confidence += 10
        
        is_signal = confidence >= 40  # Mindestens 40% Confidence für Signal
        
        return {
            "is_signal": is_signal,
            "confidence": min(confidence, 100),
            "indicators": indicators,
            "indicator_count": len(indicators)
        }
    
    async def test_vip_group_access(self) -> Dict[str, Any]:
        """Teste VIP-Gruppen-Zugriff"""
        print(f"\n🔍 TESTE VIP-GRUPPEN-ZUGRIFF")
        print("=" * 40)
        print(f"📊 Gruppe: {self.vip_group_title}")
        print(f"🆔 ID: {self.vip_group_id}")
        print(f"🔥 Qualität: {self.vip_signal_quality} (Score: {self.vip_signal_score})")
        
        try:
            # Versuche Entity zu bekommen
            entity = await self.client.get_entity(self.vip_group_id)
            print(f"✅ Entity-Zugriff erfolgreich")
            print(f"   Titel: {getattr(entity, 'title', 'Unknown')}")
            print(f"   Typ: {type(entity).__name__}")
            
            # Teste Nachrichten-Zugriff
            messages = []
            signals = []
            message_count = 0
            
            async for message in self.client.iter_messages(entity, limit=10):
                message_count += 1
                if message.text and message.text.strip():
                    msg_data = {
                        "id": message.id,
                        "text": message.text,
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S") if message.date else "Unknown"
                    }
                    
                    # Analysiere auf Signale
                    analysis = self.analyze_message_for_signals(message.text)
                    if analysis["is_signal"]:
                        signals.append({**msg_data, "analysis": analysis})
                    
                    messages.append(msg_data)
            
            print(f"✅ Nachrichten-Zugriff erfolgreich")
            print(f"   Total: {message_count} Nachrichten")
            print(f"   Mit Text: {len(messages)} Nachrichten")
            print(f"   Signale erkannt: {len(signals)} Trading-Signale")
            
            return {
                "accessible": True,
                "message_count": message_count,
                "text_messages": len(messages),
                "signals_found": len(signals),
                "recent_signals": signals[:3],  # Die 3 neuesten Signale
                "entity_title": getattr(entity, 'title', 'Unknown')
            }
            
        except Exception as e:
            print(f"❌ Zugriffsfehler: {e}")
            return {
                "accessible": False,
                "error": str(e)
            }
    
    async def test_cryptet_channel_access(self) -> Dict[str, Any]:
        """Teste Cryptet-Kanal-Zugriff"""
        print(f"\n🔍 TESTE CRYPTET-KANAL-ZUGRIFF")
        print("=" * 40)
        print(f"🆔 Cryptet ID: {self.cryptet_channel_id}")
        
        try:
            entity = await self.client.get_entity(self.cryptet_channel_id)
            print(f"✅ Cryptet-Zugriff erfolgreich")
            print(f"   Titel: {getattr(entity, 'title', 'Unknown')}")
            
            # Prüfe letzte Nachrichten
            message_count = 0
            cryptet_links = 0
            
            async for message in self.client.iter_messages(entity, limit=5):
                message_count += 1
                if message.text and 'cryptet.com' in message.text.lower():
                    cryptet_links += 1
            
            print(f"   Nachrichten: {message_count}")
            print(f"   Cryptet-Links: {cryptet_links}")
            
            return {
                "accessible": True,
                "message_count": message_count,
                "cryptet_links": cryptet_links
            }
            
        except Exception as e:
            print(f"❌ Cryptet-Zugriffsfehler: {e}")
            return {
                "accessible": False,
                "error": str(e)
            }
    
    async def verify_configuration(self) -> Dict[str, Any]:
        """Verifiziere System-Konfiguration"""
        print(f"\n⚙️ VERIFIZIERE SYSTEM-KONFIGURATION")
        print("=" * 40)
        
        config_status = {
            "env_file_exists": os.path.exists('.env'),
            "api_credentials_set": bool(self.api_id and self.api_hash),
            "bot_token_set": bool(self.bot_token),
            "monitored_chats_configured": len(self.monitored_chats) > 0,
            "vip_group_in_monitored": self.vip_group_id in self.monitored_chats,
            "cryptet_in_monitored": self.cryptet_channel_id in self.monitored_chats,
            "session_file_exists": os.path.exists(f"{self.session_name}.session")
        }
        
        print(f"✅ .env Datei: {config_status['env_file_exists']}")
        print(f"✅ API Credentials: {config_status['api_credentials_set']}")
        print(f"✅ Bot Token: {config_status['bot_token_set']}")
        print(f"✅ Überwachte Chats: {len(self.monitored_chats)} konfiguriert")
        print(f"   - VIP-Gruppe überwacht: {config_status['vip_group_in_monitored']}")
        print(f"   - Cryptet überwacht: {config_status['cryptet_in_monitored']}")
        print(f"✅ Session-Datei: {config_status['session_file_exists']}")
        
        return config_status
    
    async def run_verification(self) -> None:
        """Führe vollständige Verifikation durch"""
        print("🚀 VIP-GRUPPEN LÖSUNG VERIFIKATION")
        print("=" * 60)
        
        try:
            # Start-Nachricht
            start_msg = f"""🔍 **VIP-GRUPPEN LÖSUNG VERIFIKATION** 🔍

🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}
🎯 **Ziel:** Überprüfung der VIP-Gruppen-Lösung

**KONFIGURIERTE SIGNAL-QUELLE:**
📊 **Gruppe:** {self.vip_group_title}
🆔 **ID:** {self.vip_group_id}
🔥 **Qualität:** {self.vip_signal_quality} (Score: {self.vip_signal_score})

🔄 **Status:** Verifikation läuft..."""
            
            await self.send_report(start_msg)
            
            # 1. Telegram starten
            await self.client.start()
            me = await self.client.get_me()
            print(f"✅ Telegram verbunden: {me.first_name}")
            
            # 2. Konfiguration verifizieren
            config_result = await self.verify_configuration()
            
            # 3. VIP-Gruppen-Zugriff testen
            vip_result = await self.test_vip_group_access()
            
            # 4. Cryptet-Kanal-Zugriff testen
            cryptet_result = await self.test_cryptet_channel_access()
            
            # 5. Ergebnis-Report
            await self.generate_final_report(config_result, vip_result, cryptet_result)
            
        except Exception as e:
            error_msg = f"""❌ **VERIFIKATION FEHLER** ❌

⚠️ **Error:** {str(e)}
🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}

💡 **Empfehlung:** Konfiguration überprüfen"""
            
            print(f"❌ Verifikation Fehler: {e}")
            await self.send_report(error_msg)
            
        finally:
            await self.client.disconnect()
            print("✅ Verifikation abgeschlossen")
    
    async def generate_final_report(self, config: Dict[str, Any], vip: Dict[str, Any], cryptet: Dict[str, Any]) -> None:
        """Generiere Abschlussbericht"""
        
        # Status-Emojis
        config_emoji = "✅" if all(config.values()) else "⚠️"
        vip_emoji = "✅" if vip.get("accessible", False) else "❌"
        cryptet_emoji = "✅" if cryptet.get("accessible", False) else "❌"
        
        # Erfolgs-Status
        vip_success = vip.get("accessible", False) and vip.get("signals_found", 0) > 0
        overall_success = vip_success and cryptet.get("accessible", False)
        
        if overall_success:
            status_header = "🎉 **VIP-PROBLEM ERFOLGREICH GELÖST!** 🎉"
            status_emoji = "🎉"
        elif vip.get("accessible", False):
            status_header = "✅ **VIP-GRUPPE ZUGÄNGLICH - TEILWEISE GELÖST** ✅"
            status_emoji = "✅"
        else:
            status_header = "❌ **VIP-PROBLEM WEITERHIN BESTEHEND** ❌"
            status_emoji = "❌"
        
        report = f"""{status_header}

🕐 **Verifikationszeit:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**📊 SIGNAL-QUELLE STATUS:**
{vip_emoji} **VIP-Gruppe:** {self.vip_group_title}
• **Zugriff:** {'✅ Erfolgreich' if vip.get('accessible') else '❌ Fehlgeschlagen'}"""

        if vip.get("accessible"):
            report += f"""
• **Nachrichten:** {vip.get('text_messages', 0)} verfügbar
• **Trading-Signale:** {vip.get('signals_found', 0)} erkannt
• **Letzter Titel:** {vip.get('entity_title', 'Unknown')}"""
        else:
            report += f"""
• **Fehler:** {vip.get('error', 'Unknown error')}"""

        report += f"""

{cryptet_emoji} **Cryptet-Kanal:** {'✅ Zugänglich' if cryptet.get('accessible') else '❌ Nicht zugänglich'}"""

        if cryptet.get("accessible"):
            report += f"""
• **Nachrichten:** {cryptet.get('message_count', 0)} verfügbar
• **Cryptet-Links:** {cryptet.get('cryptet_links', 0)} gefunden"""

        report += f"""

{config_emoji} **System-Konfiguration:**
• **.env Datei:** {'✅' if config.get('env_file_exists') else '❌'}
• **API Credentials:** {'✅' if config.get('api_credentials_set') else '❌'}
• **Überwachte Chats:** {len(self.monitored_chats)} konfiguriert
• **VIP-Überwachung:** {'✅ Aktiv' if config.get('vip_group_in_monitored') else '❌ Nicht konfiguriert'}

**🚀 GESAMTSTATUS:**"""

        if overall_success:
            report += f"""
✅ **VIP-Gruppen-Problem vollständig gelöst!**
✅ **Beide Signal-Quellen funktional (VIP + Cryptet)**
✅ **System bereit für Signal-Empfang**

💡 **Nächster Schritt:** System neu starten um vollständige Integration zu aktivieren."""
        
        elif vip.get("accessible"):
            report += f"""
✅ **VIP-Gruppe erfolgreich zugänglich**
✅ **{vip.get('signals_found', 0)} Trading-Signale erkannt**
⚠️ **Cryptet-Kanal Problem** (separates Issue)

💡 **Empfehlung:** VIP-Signale sind verfügbar, System kann betrieben werden."""
            
        else:
            report += f"""
❌ **VIP-Gruppen-Zugriff weiterhin problematisch**
❌ **Manuelle Intervention erforderlich**

🔧 **Lösungsschritte:**
1. Account zur gewünschten VIP-Gruppe hinzufügen
2. Berechtigungen in der Gruppe überprüfen
3. Alternative hochwertige Signal-Quelle suchen
4. Konfiguration entsprechend anpassen"""

        # Zeige Beispiel-Signale wenn verfügbar
        if vip.get("accessible") and vip.get("recent_signals"):
            report += f"""

📋 **BEISPIEL-SIGNALE:**
```
{vip['recent_signals'][0]['text'][:200]}{'...' if len(vip['recent_signals'][0]['text']) > 200 else ''}
```"""

        await self.send_report(report)
        print(f"\n{status_emoji} VERIFIKATION ABGESCHLOSSEN")
        
        # Zusammenfassung in Console
        if overall_success:
            print("🎉 VIP-Problem erfolgreich gelöst! Beide Quellen funktional.")
        elif vip.get("accessible"):
            print("✅ VIP-Gruppe zugänglich, Cryptet-Problem separat.")
        else:
            print("❌ VIP-Problem weiterhin bestehend, manuelle Intervention erforderlich.")

async def main():
    """Hauptfunktion"""
    verifier = VIPSolutionVerifier()
    await verifier.run_verification()

if __name__ == "__main__":
    print("🔍 VIP-GRUPPEN LÖSUNG VERIFIKATION")
    print("Überprüft die Wirksamkeit der VIP-Gruppen-Lösung")
    print()
    
    asyncio.run(main())