#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST: SPEZIFISCHE VIP-GRUPPE -1002299206473
Testet Zugriff auf die gewünschte VIP-Gruppe und konfiguriert das System entsprechend
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from telethon import TelegramClient
import httpx
import re
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class SpecificVIPGroupTester:
    """Testet die spezifische VIP-Gruppe -1002299206473"""
    
    def __init__(self):
        # API Credentials
        self.api_id = int(os.getenv("TELEGRAM_API_ID", "26708757"))
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "e58c6204a1478da2b764d5fceff846e5")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw")
        
        # Session
        self.session_name = "user_telegram_session"
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Spezifische Gruppen-IDs
        self.target_vip_group_id = -1002299206473  # Gewünschte VIP-Gruppe
        self.cryptet_channel_id = -1001804143400   # Cryptet Official Channel
        self.target_group_id = -1002773853382      # Zielgruppe (PH FUTURES VIP)
    
    def clean_text_for_telegram(self, text: str) -> str:
        """Bereinige Text für Telegram"""
        if not text:
            return ""
        
        # Entferne problematische Zeichen
        text = text.replace("`", "'")
        text = text.replace("*", "•")
        text = text.replace("_", "-")
        text = text.replace("[", "(")
        text = text.replace("]", ")")
        
        # Begrenzt Textlänge
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        return text
    
    async def send_message_safe(self, chat_id: str, message: str) -> bool:
        """Sende Nachricht sicher"""
        try:
            url = "https://api.telegram.org/bot{}/sendMessage".format(self.bot_token)
            data = {
                "chat_id": chat_id,
                "text": self.clean_text_for_telegram(message),
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=15)
            
            if response.status_code == 200:
                print("✅ Nachricht gesendet an {}".format(chat_id))
                return True
            else:
                print("❌ Send Error {}: {}".format(chat_id, response.text))
                return False
                
        except Exception as e:
            print("❌ Send Error: {}".format(e))
            return False
    
    async def test_vip_group_access(self) -> Dict[str, Any]:
        """Teste Zugriff auf spezifische VIP-Gruppe"""
        print("\n🎯 TESTE SPEZIFISCHE VIP-GRUPPE: {}".format(self.target_vip_group_id))
        print("=" * 50)
        
        try:
            # Versuche Entity zu bekommen
            entity = await self.client.get_entity(self.target_vip_group_id)
            print("✅ Entity-Zugriff erfolgreich!")
            print("   Titel: {}".format(getattr(entity, 'title', 'Unknown')))
            print("   Typ: {}".format(type(entity).__name__))
            
            # Teste Nachrichten-Zugriff
            messages = []
            signals = []
            message_count = 0
            
            async for message in self.client.iter_messages(entity, limit=15):
                message_count += 1
                if message.text and message.text.strip():
                    msg_data = {
                        "id": message.id,
                        "text": message.text,
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S") if message.date else "Unknown"
                    }
                    messages.append(msg_data)
                    
                    # Prüfe auf Trading-Signale
                    if re.search(r'[A-Z]{2,8}/USDT', message.text):
                        signals.append(msg_data)
                        date_str = message.date.strftime('%H:%M:%S') if message.date else 'Unknown'
                        print("📊 Signal gefunden: ID {} - {}".format(message.id, date_str))
            
            print("✅ Nachrichten-Zugriff erfolgreich!")
            print("   Total: {} Nachrichten".format(message_count))
            print("   Mit Text: {} Nachrichten".format(len(messages)))
            print("   Trading-Signale: {} gefunden".format(len(signals)))
            
            return {
                "accessible": True,
                "title": getattr(entity, 'title', 'Unknown'),
                "message_count": message_count,
                "text_messages": len(messages),
                "signals_found": len(signals),
                "recent_signals": signals[:3],  # Die 3 neuesten Signale
                "all_messages": messages[:5]    # Die 5 neuesten Nachrichten
            }
            
        except Exception as e:
            print("❌ Zugriffsfehler: {}".format(e))
            return {
                "accessible": False,
                "error": str(e)
            }
    
    async def test_cryptet_access(self) -> Dict[str, Any]:
        """Teste Cryptet-Kanal-Zugriff"""
        print("\n🔍 TESTE CRYPTET-KANAL: {}".format(self.cryptet_channel_id))
        print("=" * 40)
        
        try:
            entity = await self.client.get_entity(self.cryptet_channel_id)
            print("✅ Cryptet-Zugriff erfolgreich!")
            print("   Titel: {}".format(getattr(entity, 'title', 'Unknown')))
            
            # Prüfe letzte Nachrichten
            message_count = 0
            cryptet_links = 0
            recent_messages = []
            
            async for message in self.client.iter_messages(entity, limit=10):
                message_count += 1
                if message.text:
                    text_preview = message.text[:100] + "..." if len(message.text) > 100 else message.text
                    recent_messages.append({
                        "id": message.id,
                        "text": text_preview,
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S") if message.date else "Unknown"
                    })
                    
                    if 'cryptet.com' in message.text.lower():
                        cryptet_links += 1
            
            print("   Nachrichten: {}".format(message_count))
            print("   Cryptet-Links: {}".format(cryptet_links))
            
            return {
                "accessible": True,
                "title": getattr(entity, 'title', 'Unknown'),
                "message_count": message_count,
                "cryptet_links": cryptet_links,
                "recent_messages": recent_messages[:3]
            }
            
        except Exception as e:
            print("❌ Cryptet-Zugriffsfehler: {}".format(e))
            return {
                "accessible": False,
                "error": str(e)
            }
    
    async def update_configuration(self, vip_result: Dict[str, Any], cryptet_result: Dict[str, Any]) -> bool:
        """Aktualisiere Konfiguration für die spezifischen Gruppen"""
        try:
            print("\n⚙️ AKTUALISIERE KONFIGURATION")
            print("=" * 30)
            
            if vip_result.get("accessible") and cryptet_result.get("accessible"):
                # Beide Quellen zugänglich - ideale Konfiguration
                config_content = f"""# Telegram Bot Konfiguration (Spezifische VIP-Gruppe: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
TELEGRAM_API_ID=26708757
TELEGRAM_API_HASH=e58c6204a1478da2b764d5fceff846e5
TELEGRAM_BOT_TOKEN=8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw

# Überwachte Chats (NUR gewünschte Quellen)
MONITORED_CHAT_IDS={self.target_vip_group_id},{self.cryptet_channel_id}

# Gruppenspezifische Konfigurationen (Exakte Wunsch-Konfiguration)
VIP_GROUP_ID={self.target_vip_group_id}
CRYPTET_CHANNEL_ID={self.cryptet_channel_id}
TARGET_GROUP_ID={self.target_group_id}

# System-Konfiguration  
CRYPTET_ENABLED=true
TRADING_ENABLED=false
LOG_LEVEL=INFO

# VIP-Gruppe Info (Spezifische Gruppe)
VIP_GROUP_TITLE={vip_result['title']}
VIP_GROUP_ACCESSIBLE=true
VIP_SIGNALS_FOUND={vip_result['signals_found']}

# Cryptet-Kanal Info
CRYPTET_CHANNEL_TITLE={cryptet_result['title']}
CRYPTET_ACCESSIBLE=true
CRYPTET_LINKS_FOUND={cryptet_result['cryptet_links']}

# Database (optional)
# DATABASE_URL=sqlite:///trading_bot.db"""
                
                status = "✅ PERFEKTE KONFIGURATION - Beide Quellen zugänglich"
                
            elif vip_result.get("accessible"):
                # Nur VIP-Gruppe zugänglich
                config_content = f"""# Telegram Bot Konfiguration (NUR VIP-Gruppe: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
TELEGRAM_API_ID=26708757
TELEGRAM_API_HASH=e58c6204a1478da2b764d5fceff846e5
TELEGRAM_BOT_TOKEN=8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw

# Überwachte Chats (NUR VIP-Gruppe)
MONITORED_CHAT_IDS={self.target_vip_group_id}

# Gruppenspezifische Konfigurationen
VIP_GROUP_ID={self.target_vip_group_id}
CRYPTET_CHANNEL_ID={self.cryptet_channel_id}
TARGET_GROUP_ID={self.target_group_id}

# System-Konfiguration (Cryptet deaktiviert)
CRYPTET_ENABLED=false
TRADING_ENABLED=false
LOG_LEVEL=INFO

# VIP-Gruppe Info
VIP_GROUP_TITLE={vip_result['title']}
VIP_GROUP_ACCESSIBLE=true
VIP_SIGNALS_FOUND={vip_result['signals_found']}

# Cryptet-Status
CRYPTET_ACCESSIBLE=false
CRYPTET_ERROR={cryptet_result.get('error', 'Not accessible')}"""
                
                status = "⚠️ TEILWEISE KONFIGURATION - Nur VIP-Gruppe zugänglich"
                
            else:
                # Keine der gewünschten Quellen zugänglich
                config_content = f"""# Telegram Bot Konfiguration (FEHLER - Keine Quelle zugänglich: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
TELEGRAM_API_ID=26708757
TELEGRAM_API_HASH=e58c6204a1478da2b764d5fceff846e5
TELEGRAM_BOT_TOKEN=8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw

# FEHLER: Keine überwachten Chats verfügbar
MONITORED_CHAT_IDS=

# Gruppenspezifische Konfigurationen (Nicht zugänglich)
VIP_GROUP_ID={self.target_vip_group_id}
CRYPTET_CHANNEL_ID={self.cryptet_channel_id}
TARGET_GROUP_ID={self.target_group_id}

# System-Konfiguration (Alle Quellen deaktiviert)
CRYPTET_ENABLED=false
TRADING_ENABLED=false
LOG_LEVEL=INFO

# Fehler-Status
VIP_GROUP_ACCESSIBLE=false
VIP_ERROR={vip_result.get('error', 'Not accessible')}
CRYPTET_ACCESSIBLE=false
CRYPTET_ERROR={cryptet_result.get('error', 'Not accessible')}"""
                
                status = "❌ FEHLER-KONFIGURATION - Keine Quelle zugänglich"
            
            # Schreibe .env Datei
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            print(f"✅ .env Datei aktualisiert")
            print(f"Status: {status}")
            
            return True
            
        except Exception as e:
            print(f"❌ Konfigurationsfehler: {e}")
            return False
    
    async def run_specific_test(self) -> None:
        """Führe spezifischen VIP-Gruppen-Test durch"""
        print("🚀 SPEZIFISCHE VIP-GRUPPEN-KONFIGURATION")
        print("=" * 60)
        print(f"🎯 Gewünschte VIP-Gruppe: {self.target_vip_group_id}")
        print(f"🔗 Cryptet-Kanal: {self.cryptet_channel_id}")
        
        try:
            # Start-Nachricht
            start_msg = f"""🎯 SPEZIFISCHE VIP-KONFIGURATION GESTARTET

Zeit: {datetime.now().strftime('%H:%M:%S')}
Gewünschte VIP-Gruppe: {self.target_vip_group_id}
Cryptet-Kanal: {self.cryptet_channel_id}

Status: Teste Zugriff auf gewünschte Quellen..."""
            
            await self.send_message_safe(str(self.target_group_id), start_msg)
            
            # 1. Telegram starten
            await self.client.start()
            me = await self.client.get_me()
            print(f"✅ Telegram verbunden: {me.first_name}")
            
            # 2. Teste spezifische VIP-Gruppe
            vip_result = await self.test_vip_group_access()
            
            # 3. Teste Cryptet-Kanal
            cryptet_result = await self.test_cryptet_access()
            
            # 4. Aktualisiere Konfiguration
            config_success = await self.update_configuration(vip_result, cryptet_result)
            
            # 5. Sende Ergebnisbericht
            await self.send_final_report(vip_result, cryptet_result, config_success)
            
        except Exception as e:
            error_msg = f"""❌ SPEZIFISCHE VIP-KONFIGURATION FEHLER

Error: {str(e)}
Zeit: {datetime.now().strftime('%H:%M:%S')}

Empfehlung: Manuelle Diagnose erforderlich"""
            
            print(f"❌ Fehler: {e}")
            await self.send_message_safe(str(self.target_group_id), error_msg)
            
        finally:
            await self.client.disconnect()
            print("✅ Spezifischer Test abgeschlossen")
    
    async def send_final_report(self, vip_result: Dict[str, Any], cryptet_result: Dict[str, Any], config_success: bool) -> None:
        """Sende Abschlussbericht"""
        
        # Status-Emojis
        vip_emoji = "✅" if vip_result.get("accessible") else "❌"
        cryptet_emoji = "✅" if cryptet_result.get("accessible") else "❌"
        config_emoji = "✅" if config_success else "❌"
        
        # Gesamtstatus
        if vip_result.get("accessible") and cryptet_result.get("accessible"):
            overall_status = "🎉 PERFEKT - Beide gewünschten Quellen verfügbar!"
            overall_emoji = "🎉"
        elif vip_result.get("accessible"):
            overall_status = "✅ TEILWEISE - VIP-Gruppe verfügbar, Cryptet Problem"
            overall_emoji = "✅"
        else:
            overall_status = "❌ PROBLEM - Gewünschte VIP-Gruppe nicht zugänglich"
            overall_emoji = "❌"
        
        report = f"""{overall_status}

🎯 SPEZIFISCHE VIP-KONFIGURATION ABGESCHLOSSEN

Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

GEWÜNSCHTE QUELLEN:
{vip_emoji} VIP-Gruppe ({self.target_vip_group_id}): {'ZUGÄNGLICH' if vip_result.get('accessible') else 'NICHT ZUGÄNGLICH'}"""

        if vip_result.get("accessible"):
            report += f"""
• Titel: {vip_result['title']}
• Nachrichten: {vip_result['text_messages']} verfügbar
• Trading-Signale: {vip_result['signals_found']} gefunden"""
        else:
            report += f"""
• Fehler: {vip_result.get('error', 'Unknown error')}"""

        report += f"""

{cryptet_emoji} Cryptet-Kanal ({self.cryptet_channel_id}): {'ZUGÄNGLICH' if cryptet_result.get('accessible') else 'NICHT ZUGÄNGLICH'}"""

        if cryptet_result.get("accessible"):
            report += f"""
• Titel: {cryptet_result['title']}
• Nachrichten: {cryptet_result['message_count']} verfügbar
• Cryptet-Links: {cryptet_result['cryptet_links']} gefunden"""
        else:
            report += f"""
• Fehler: {cryptet_result.get('error', 'Unknown error')}"""

        report += f"""

{config_emoji} SYSTEM-KONFIGURATION: {'AKTUALISIERT' if config_success else 'FEHLER'}

NÄCHSTE SCHRITTE:"""

        if vip_result.get("accessible") and cryptet_result.get("accessible"):
            report += f"""
✅ Beide gewünschten Quellen sind verfügbar!
✅ .env Datei wurde optimal konfiguriert
✅ System bereit für Signal-Empfang

🚀 Empfehlung: System neu starten um Konfiguration zu laden"""
        
        elif vip_result.get("accessible"):
            report += f"""
✅ VIP-Gruppe ist verfügbar und konfiguriert
⚠️ Cryptet-Problem separat lösen
✅ System kann nur VIP-Signale empfangen

🚀 Empfehlung: System mit VIP-only Konfiguration starten"""
            
        else:
            report += f"""
❌ Gewünschte VIP-Gruppe nicht zugänglich
💡 Mögliche Lösungen:
1. Account zur VIP-Gruppe hinzufügen
2. Berechtigungen überprüfen
3. Gruppe-ID verifizieren

🔧 Empfehlung: Manuelle VIP-Gruppen-Integration erforderlich"""

        # Zeige Beispiel-Signale wenn verfügbar
        if vip_result.get("accessible") and vip_result.get("recent_signals"):
            report += f"""

📊 BEISPIEL-SIGNALE AUS VIP-GRUPPE:
{vip_result['recent_signals'][0]['text'][:200]}{'...' if len(vip_result['recent_signals'][0]['text']) > 200 else ''}"""

        await self.send_message_safe(str(self.target_group_id), report)
        
        # Console-Zusammenfassung
        print(f"\n{overall_emoji} ERGEBNIS: {overall_status}")

async def main():
    """Hauptfunktion"""
    tester = SpecificVIPGroupTester()
    await tester.run_specific_test()

if __name__ == "__main__":
    print("🎯 SPEZIFISCHE VIP-GRUPPEN-KONFIGURATION")
    print("Konfiguriert System für exakt gewünschte Quellen:")
    print(f"  VIP-Gruppe: -1002299206473")
    print(f"  Cryptet-Kanal: -1001804143400")
    print()
    
    asyncio.run(main())