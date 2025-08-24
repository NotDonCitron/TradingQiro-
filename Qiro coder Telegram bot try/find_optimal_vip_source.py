#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEZIFISCHER VIP-SIGNAL-GRUPPEN FINDER
Findet die korrekte VIP-Signal-Gruppe (-2299206473) oder die beste Alternative
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError, ChatAdminRequiredError, PeerIdInvalidError
import requests
import re

class SpecificVIPFinder:
    """Findet die spezifische VIP-Signal-Gruppe"""
    
    def __init__(self):
        # API Credentials
        self.api_id = 26708757
        self.api_hash = "e58c6204a1478da2b764d5fceff846e5"
        self.bot_token = "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw"
        
        # Session verwenden
        self.session_name = "user_telegram_session"
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Zielgruppen
        self.original_vip_id = -2299206473  # Ursprünglich gewünschte VIP-Gruppe
        self.cryptet_channel_id = -1001804143400  # Cryptet Official Channel
        self.target_group_id = -1002773853382  # PH FUTURES VIP (Ziel - nicht Quelle!)
    
    async def send_message(self, message: str) -> bool:
        """Sende Nachricht an Zielgruppe"""
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
            print(f"❌ Send Error: {e}")
            return False
    
    def analyze_signal_quality(self, messages: List[str]) -> Dict[str, Any]:
        """Analysiere Qualität der Trading-Signale in einer Gruppe"""
        if not messages:
            return {"score": 0, "signals": 0, "quality": "low"}
        
        signal_count = 0
        quality_indicators = {
            "crypto_pairs": 0,
            "leverage_info": 0,
            "entry_points": 0,
            "take_profits": 0,
            "stop_loss": 0,
            "direction_clear": 0,
            "recent_activity": 0
        }
        
        for text in messages:
            if not text:
                continue
                
            text_lower = text.lower()
            
            # Krypto-Paare
            if re.search(r'[A-Z]{2,8}/USDT', text):
                quality_indicators["crypto_pairs"] += 1
                signal_count += 1
            
            # Leverage-Informationen
            if re.search(r'leverage|cross|isolated|\d+x', text_lower):
                quality_indicators["leverage_info"] += 1
            
            # Entry Points
            if re.search(r'entry|enter|buy.*at|sell.*at', text_lower):
                quality_indicators["entry_points"] += 1
            
            # Take Profit
            if re.search(r'take.*profit|tp|target', text_lower):
                quality_indicators["take_profits"] += 1
            
            # Stop Loss
            if re.search(r'stop.*loss|sl|stop', text_lower):
                quality_indicators["stop_loss"] += 1
            
            # Klare Richtung
            if re.search(r'\b(long|short|buy|sell)\b', text_lower):
                quality_indicators["direction_clear"] += 1
        
        # Berechne Gesamtscore
        total_score = sum(quality_indicators.values())
        
        # Qualitätsbewertung
        if total_score >= 15 and signal_count >= 3:
            quality = "excellent"
        elif total_score >= 10 and signal_count >= 2:
            quality = "good"
        elif total_score >= 5 and signal_count >= 1:
            quality = "fair"
        else:
            quality = "poor"
        
        return {
            "score": total_score,
            "signals": signal_count,
            "quality": quality,
            "indicators": quality_indicators
        }
    
    async def test_specific_vip_id(self) -> Optional[Dict[str, Any]]:
        """Teste die ursprünglich gewünschte VIP-Gruppe"""
        print(f"\n🎯 TESTE URSPRÜNGLICHE VIP-GRUPPE: {self.original_vip_id}")
        print("=" * 50)
        
        try:
            # Versuche direkten Zugriff
            entity = await self.client.get_entity(self.original_vip_id)
            print(f"✅ Direkter Zugriff erfolgreich!")
            print(f"   Titel: {getattr(entity, 'title', 'Unknown')}")
            print(f"   Typ: {type(entity).__name__}")
            
            # Teste Nachrichten-Zugriff
            messages = []
            async for message in self.client.iter_messages(entity, limit=20):
                if message.text and message.text.strip():
                    messages.append(message.text)
            
            if messages:
                print(f"✅ Kann Nachrichten lesen: {len(messages)} verfügbar")
                
                # Analysiere Signal-Qualität
                analysis = self.analyze_signal_quality(messages)
                
                return {
                    "id": self.original_vip_id,
                    "title": getattr(entity, 'title', 'Unknown'),
                    "entity": entity,
                    "accessible": True,
                    "message_count": len(messages),
                    "analysis": analysis,
                    "recent_messages": messages[:5]
                }
            else:
                print(f"⚠️ Zugriff möglich, aber keine Nachrichten")
                return None
                
        except Exception as e:
            print(f"❌ Zugriff fehlgeschlagen: {e}")
            return None
    
    async def find_best_signal_source(self) -> Optional[Dict[str, Any]]:
        """Finde die beste verfügbare Signal-Quelle"""
        print("\n🔍 SUCHE BESTE SIGNAL-QUELLE")
        print("=" * 40)
        
        candidate_groups = []
        
        # Durchsuche alle verfügbaren Dialogs
        async for dialog in self.client.iter_dialogs():
            # Überspringe die Zielgruppe (sie ist nicht die Quelle)
            if dialog.id == self.target_group_id:
                continue
            
            # Überspringe private Chats
            if dialog.is_user:
                continue
            
            try:
                # Prüfe letzte 15 Nachrichten auf Trading-Signale
                messages = []
                async for message in self.client.iter_messages(dialog.entity, limit=15):
                    if message.text and message.text.strip():
                        messages.append(message.text)
                
                # Analysiere Signal-Qualität
                analysis = self.analyze_signal_quality(messages)
                
                # Nur Gruppen mit guten Signalen berücksichtigen
                if analysis["signals"] >= 2 and analysis["score"] >= 8:
                    candidate_groups.append({
                        "id": dialog.id,
                        "title": dialog.title,
                        "entity": dialog.entity,
                        "analysis": analysis,
                        "message_count": len(messages),
                        "recent_messages": messages[:3]
                    })
                    
                    print(f"📊 Kandidat: {dialog.title}")
                    print(f"   ID: {dialog.id}")
                    print(f"   Qualität: {analysis['quality']} (Score: {analysis['score']}, Signale: {analysis['signals']})")
                
            except Exception as e:
                # Überspringe unzugängliche Gruppen
                continue
        
        if candidate_groups:
            # Sortiere nach Qualität
            candidate_groups.sort(key=lambda x: (x['analysis']['score'], x['analysis']['signals']), reverse=True)
            
            print(f"\n✅ {len(candidate_groups)} Signal-Quellen gefunden")
            print("🏆 Beste Kandidaten:")
            for i, group in enumerate(candidate_groups[:3], 1):
                print(f"   {i}. {group['title']} (Score: {group['analysis']['score']})")
            
            return candidate_groups[0]  # Beste Option
        
        return None
    
    async def configure_signal_source(self, source_info: Dict[str, Any]) -> bool:
        """Konfiguriere die gefundene Signal-Quelle"""
        try:
            print(f"\n⚙️ KONFIGURIERE SIGNAL-QUELLE: {source_info['title']}")
            
            # Erstelle .env Konfiguration
            env_content = f"""# Telegram Bot Konfiguration (VIP-Quelle konfiguriert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
TELEGRAM_API_ID=26708757
TELEGRAM_API_HASH=e58c6204a1478da2b764d5fceff846e5
TELEGRAM_BOT_TOKEN=8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw

# Überwachte Chats (Optimierte Konfiguration)
MONITORED_CHAT_IDS={source_info['id']},{self.cryptet_channel_id}

# Gruppenspezifische Konfigurationen
VIP_GROUP_ID={source_info['id']}
CRYPTET_CHANNEL_ID={self.cryptet_channel_id}
TARGET_GROUP_ID={self.target_group_id}

# System-Konfiguration  
CRYPTET_ENABLED=true
TRADING_ENABLED=false
LOG_LEVEL=INFO

# Signal-Quelle Info (automatisch optimiert)
VIP_GROUP_TITLE={source_info['title']}
VIP_SIGNAL_QUALITY={source_info['analysis']['quality']}
VIP_SIGNAL_SCORE={source_info['analysis']['score']}
"""
            
            # Schreibe .env Datei
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            print("✅ .env Datei aktualisiert")
            return True
            
        except Exception as e:
            print(f"❌ Konfigurationsfehler: {e}")
            return False
    
    async def send_configuration_report(self, source_info: Dict[str, Any]) -> None:
        """Sende Konfigurationsbericht"""
        analysis = source_info['analysis']
        
        # Qualitäts-Emoji
        quality_emoji = {
            "excellent": "🔥",
            "good": "✅",
            "fair": "⚠️",
            "poor": "❌"
        }
        
        emoji = quality_emoji.get(analysis['quality'], "❓")
        
        report = f"""🎯 **VIP-SIGNAL-QUELLE KONFIGURIERT!** {emoji}

📊 **Signal-Quelle:** {source_info['title']}
🆔 **Gruppen-ID:** {source_info['id']}
🔥 **Qualität:** {analysis['quality'].upper()} (Score: {analysis['score']})

📈 **Signal-Analyse:**
• Signale erkannt: {analysis['signals']}
• Crypto-Paare: {analysis['indicators']['crypto_pairs']}
• Leverage-Info: {analysis['indicators']['leverage_info']}
• Entry-Points: {analysis['indicators']['entry_points']}
• Take-Profits: {analysis['indicators']['take_profits']}
• Stop-Loss: {analysis['indicators']['stop_loss']}

✅ **Konfiguration:**
• .env Datei aktualisiert
• MONITORED_CHAT_IDS gesetzt
• System bereit für Signale

🚀 **Status:** VIP-Pipeline optimal konfiguriert!

💡 **Empfehlung:** System neu starten um Konfiguration zu laden."""

        await self.send_message(report)
        
        # Zeige Beispiel-Signale
        if source_info.get('recent_messages'):
            example_msg = f"""📋 **BEISPIEL-SIGNALE VON {source_info['title']}:**

```
{source_info['recent_messages'][0][:300]}{'...' if len(source_info['recent_messages'][0]) > 300 else ''}
```

🔄 **System bereit:** Warten auf neue Signale..."""
            
            await self.send_message(example_msg)
    
    async def run_specific_vip_search(self) -> None:
        """Führe spezifische VIP-Gruppen-Suche durch"""
        print("🚀 SPEZIFISCHE VIP-SIGNAL-GRUPPEN SUCHE")
        print("=" * 60)
        
        try:
            # Start-Nachricht
            start_msg = f"""🎯 **VIP-SIGNAL-GRUPPEN OPTIMIERUNG** 🎯

🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}
🎯 **Ziel:** Beste VIP-Signal-Quelle finden und konfigurieren
🔍 **Methode:** Intelligente Signal-Qualitäts-Analyse

🔄 **Status:** Suche nach optimaler Signal-Quelle..."""
            
            await self.send_message(start_msg)
            
            # 1. Telegram starten
            await self.client.start()
            me = await self.client.get_me()
            print(f"✅ Telegram verbunden: {me.first_name}")
            
            # 2. Teste ursprüngliche VIP-Gruppe
            original_result = await self.test_specific_vip_id()
            
            if original_result and original_result['analysis']['quality'] in ['good', 'excellent']:
                print("🎯 Ursprüngliche VIP-Gruppe ist optimal!")
                await self.configure_signal_source(original_result)
                await self.send_configuration_report(original_result)
                return
            
            # 3. Suche nach der besten Alternative
            best_source = await self.find_best_signal_source()
            
            if best_source:
                print(f"✅ Beste Signal-Quelle gefunden: {best_source['title']}")
                await self.configure_signal_source(best_source)
                await self.send_configuration_report(best_source)
            else:
                # Keine guten Signal-Quellen gefunden
                error_msg = """⚠️ **KEINE OPTIMALE SIGNAL-QUELLE GEFUNDEN** ⚠️

🔍 **Problem:** Keine Gruppen mit hochwertigen Trading-Signalen erkannt
📊 **Kriterien:** Mindestens 2 Signale mit Score ≥ 8 erforderlich

💡 **Empfehlungen:**
1. Hochwertige VIP-Signal-Gruppe beitreten
2. Gruppe mit regelmäßigen Crypto-Trading-Signalen suchen
3. Manuelle Konfiguration der gewünschten Gruppe

🔧 **Alternative:** Nur Cryptet-Automation verwenden"""
                
                await self.send_message(error_msg)
                
        except Exception as e:
            error_msg = f"""❌ **VIP-SUCHE FEHLER** ❌

⚠️ **Error:** {str(e)}
🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}

💡 **Empfehlung:** Manuelle Diagnose erforderlich"""
            
            print(f"❌ VIP-Suche Fehler: {e}")
            await self.send_message(error_msg)
            
        finally:
            await self.client.disconnect()
            print("✅ VIP-Suche abgeschlossen")

async def main():
    """Hauptfunktion"""
    finder = SpecificVIPFinder()
    await finder.run_specific_vip_search()

if __name__ == "__main__":
    print("🎯 SPEZIFISCHE VIP-SIGNAL-GRUPPEN SUCHE")
    print("Findet die beste VIP-Signal-Quelle durch intelligente Analyse")
    print()
    
    asyncio.run(main())