#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIP-GRUPPEN PROBLEM DIAGNOSE & LÖSUNG
Umfassendes Script zur Behebung des VIP-Gruppen-Zugriffsproblems
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError, ChatAdminRequiredError, PeerIdInvalidError
from telethon.tl.types import Channel, Chat, User

class VIPGroupDiagnoser:
    """Diagnostiziert und löst VIP-Gruppen-Zugriffsprobleme"""
    
    def __init__(self):
        # API Credentials (hardcodiert für Diagnose)
        self.api_id = 26708757
        self.api_hash = "e58c6204a1478da2b764d5fceff846e5"
        self.bot_token = "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw"
        
        # Session verwenden
        self.session_name = "user_telegram_session"
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Zielgruppen
        self.vip_group_id = -2299206473  # VIP Signal Group (Problem)
        self.cryptet_channel_id = -1001804143400  # Cryptet Official Channel
        self.target_group_id = -1002773853382  # PH FUTURES VIP (Ziel)
        
        # Diagnose-Ergebnisse
        self.diagnosis_results = {
            "session_status": False,
            "vip_access": False,
            "membership_status": False,
            "permission_level": None,
            "error_details": [],
            "recommendations": []
        }
    
    async def send_report_message(self, message: str) -> bool:
        """Sende Diagnosebericht an Zielgruppe"""
        try:
            import requests
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
    
    async def test_session_status(self) -> bool:
        """Teste Session-Status"""
        try:
            await self.client.start()
            me = await self.client.get_me()
            
            self.diagnosis_results["session_status"] = True
            
            print(f"✅ Session erfolgreich:")
            print(f"   Name: {me.first_name} {me.last_name or ''}")
            print(f"   Username: @{me.username or 'kein_username'}")
            print(f"   ID: {me.id}")
            print(f"   Telefon: {me.phone or 'nicht verfügbar'}")
            print(f"   Bot: {getattr(me, 'bot', False)}")
            
            return True
            
        except Exception as e:
            self.diagnosis_results["error_details"].append(f"Session Error: {e}")
            print(f"❌ Session Fehler: {e}")
            return False
    
    async def test_vip_group_access(self) -> Optional[Any]:
        """Teste VIP-Gruppen-Zugriff mit verschiedenen Methoden"""
        print("\n🔍 VIP-GRUPPEN ZUGRIFF DIAGNOSE")
        print("=" * 50)
        
        methods = [
            ("Direkt get_entity", self._try_direct_entity),
            ("Via get_dialogs", self._try_via_dialogs),
            ("Via iter_dialogs", self._try_via_iter_dialogs),
            ("Mit PeerChannel", self._try_peer_channel)
        ]
        
        for method_name, method_func in methods:
            print(f"\n📡 {method_name}...")
            try:
                result = await method_func()
                if result:
                    print(f"✅ {method_name} erfolgreich!")
                    self.diagnosis_results["vip_access"] = True
                    return result
                else:
                    print(f"❌ {method_name} fehlgeschlagen")
            except Exception as e:
                error_msg = f"{method_name} Error: {str(e)}"
                print(f"❌ {error_msg}")
                self.diagnosis_results["error_details"].append(error_msg)
        
        return None
    
    async def _try_direct_entity(self) -> Optional[Any]:
        """Versuch 1: Direkter Entity-Zugriff"""
        try:
            entity = await self.client.get_entity(self.vip_group_id)
            print(f"   Typ: {type(entity).__name__}")
            print(f"   Titel: {getattr(entity, 'title', 'Unknown')}")
            print(f"   ID: {entity.id}")
            return entity
        except Exception:
            return None
    
    async def _try_via_dialogs(self) -> Optional[Any]:
        """Versuch 2: Über get_dialogs"""
        try:
            dialogs = await self.client.get_dialogs()
            for dialog in dialogs:
                if dialog.id == self.vip_group_id:
                    print(f"   Gefunden in Dialogs: {dialog.title}")
                    return dialog.entity
            return None
        except Exception:
            return None
    
    async def _try_via_iter_dialogs(self) -> Optional[Any]:
        """Versuch 3: Über iter_dialogs"""
        try:
            async for dialog in self.client.iter_dialogs():
                if dialog.id == self.vip_group_id:
                    print(f"   Gefunden via iter_dialogs: {dialog.title}")
                    return dialog.entity
            return None
        except Exception:
            return None
    
    async def _try_peer_channel(self) -> Optional[Any]:
        """Versuch 4: Mit PeerChannel"""
        try:
            from telethon.tl.types import PeerChannel
            # VIP-Gruppe hat negative ID, konvertiere zu Channel-ID
            channel_id = abs(self.vip_group_id) - 1000000000000
            peer = PeerChannel(channel_id)
            entity = await self.client.get_entity(peer)
            print(f"   PeerChannel erfolgreich: {getattr(entity, 'title', 'Unknown')}")
            return entity
        except Exception:
            return None
    
    async def check_membership_status(self, entity: Any) -> Dict[str, Any]:
        """Prüfe Mitgliedschaft und Berechtigungen"""
        try:
            print("\n👥 MITGLIEDSCHAFT & BERECHTIGUNGEN")
            print("=" * 40)
            
            # Versuche Teilnehmer zu bekommen
            try:
                participants = await self.client.get_participants(entity, limit=1)
                print(f"✅ Kann Teilnehmer abrufen: {len(participants)} Teilnehmer verfügbar")
                
                # Prüfe eigene Mitgliedschaft
                me = await self.client.get_me()
                my_participant = None
                
                try:
                    my_participant = await self.client.get_participants(entity, search=me.username or str(me.id), limit=1)
                    if my_participant:
                        print(f"✅ Mitgliedschaft bestätigt")
                        self.diagnosis_results["membership_status"] = True
                    else:
                        print(f"❌ Keine Mitgliedschaft gefunden")
                        self.diagnosis_results["recommendations"].append("Account muss zur VIP-Gruppe hinzugefügt werden")
                except Exception as e:
                    print(f"⚠️ Mitgliedschaftsprüfung fehlgeschlagen: {e}")
                
            except Exception as e:
                print(f"❌ Kann keine Teilnehmer abrufen: {e}")
                self.diagnosis_results["recommendations"].append("Keine Berechtigung zum Lesen der Teilnehmerliste")
            
            # Versuche Nachrichten zu lesen
            try:
                messages = []
                async for message in self.client.iter_messages(entity, limit=3):
                    if message.text:
                        messages.append({
                            "id": message.id,
                            "text": message.text[:100] + "..." if len(message.text) > 100 else message.text,
                            "date": message.date.strftime("%Y-%m-%d %H:%M:%S") if message.date else "Unknown"
                        })
                
                if messages:
                    print(f"✅ Kann Nachrichten lesen: {len(messages)} aktuelle Nachrichten")
                    self.diagnosis_results["permission_level"] = "read_messages"
                    return {"can_read": True, "messages": messages}
                else:
                    print(f"⚠️ Keine Nachrichten verfügbar")
                    return {"can_read": False, "messages": []}
                    
            except Exception as e:
                print(f"❌ Kann keine Nachrichten lesen: {e}")
                self.diagnosis_results["error_details"].append(f"Read Messages Error: {e}")
                self.diagnosis_results["recommendations"].append("Keine Berechtigung zum Lesen von Nachrichten")
                return {"can_read": False, "error": str(e)}
                
        except Exception as e:
            print(f"❌ Membership Check Error: {e}")
            self.diagnosis_results["error_details"].append(f"Membership Check Error: {e}")
            return {"error": str(e)}
    
    async def test_environment_config(self) -> Dict[str, Any]:
        """Teste Umgebungskonfiguration"""
        print("\n⚙️ UMGEBUNGSKONFIGURATION")
        print("=" * 30)
        
        config_status = {
            "api_credentials": False,
            "bot_token": False,
            "monitored_chats": False,
            "session_file": False
        }
        
        # API Credentials
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        if api_id and api_hash:
            print(f"✅ API Credentials konfiguriert")
            config_status["api_credentials"] = True
        else:
            print(f"⚠️ API Credentials fehlen in Umgebungsvariablen")
        
        # Bot Token
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if bot_token:
            print(f"✅ Bot Token konfiguriert")
            config_status["bot_token"] = True
        else:
            print(f"⚠️ Bot Token fehlt")
        
        # Monitored Chats
        monitored_chats = os.getenv("MONITORED_CHAT_IDS", "")
        if monitored_chats:
            chat_list = [int(x.strip()) for x in monitored_chats.split(",") if x.strip()]
            print(f"✅ Überwachte Chats: {chat_list}")
            
            if self.vip_group_id in chat_list:
                print(f"✅ VIP-Gruppe ({self.vip_group_id}) ist überwacht")
                config_status["monitored_chats"] = True
            else:
                print(f"❌ VIP-Gruppe ({self.vip_group_id}) NICHT in überwachten Chats!")
                self.diagnosis_results["recommendations"].append(f"VIP-Gruppe {self.vip_group_id} zu MONITORED_CHAT_IDS hinzufügen")
        else:
            print(f"⚠️ Keine überwachten Chats konfiguriert")
        
        # Session File
        session_file = f"{self.session_name}.session"
        if os.path.exists(session_file):
            print(f"✅ Session-Datei vorhanden: {session_file}")
            config_status["session_file"] = True
        else:
            print(f"❌ Session-Datei fehlt: {session_file}")
            self.diagnosis_results["recommendations"].append("Session-Datei erstellen oder wiederherstellen")
        
        return config_status
    
    async def generate_diagnosis_report(self) -> str:
        """Generiere umfassenden Diagnosebericht"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Status-Emojis
        session_emoji = "✅" if self.diagnosis_results["session_status"] else "❌"
        vip_emoji = "✅" if self.diagnosis_results["vip_access"] else "❌"
        membership_emoji = "✅" if self.diagnosis_results["membership_status"] else "❌"
        
        report = f"""🔍 **VIP-GRUPPEN DIAGNOSE BERICHT** 🔍

🕐 **Zeitstempel:** {timestamp}
🎯 **Ziel:** VIP-Gruppe ({self.vip_group_id}) Zugriffsproblem lösen

📊 **DIAGNOSE-ERGEBNISSE:**

{session_emoji} **Session-Status:** {'Funktional' if self.diagnosis_results['session_status'] else 'Fehlerhaft'}
{vip_emoji} **VIP-Zugriff:** {'Erfolgreich' if self.diagnosis_results['vip_access'] else 'Fehlgeschlagen'}  
{membership_emoji} **Mitgliedschaft:** {'Bestätigt' if self.diagnosis_results['membership_status'] else 'Nicht bestätigt'}
🔐 **Berechtigungen:** {self.diagnosis_results['permission_level'] or 'Keine'}

⚠️ **FEHLER-DETAILS:**"""

        if self.diagnosis_results["error_details"]:
            for i, error in enumerate(self.diagnosis_results["error_details"], 1):
                report += f"\n{i}. {error}"
        else:
            report += "\nKeine kritischen Fehler gefunden."

        report += "\n\n💡 **EMPFEHLUNGEN:**"
        
        if self.diagnosis_results["recommendations"]:
            for i, rec in enumerate(self.diagnosis_results["recommendations"], 1):
                report += f"\n{i}. {rec}"
        else:
            report += "\nKeine weiteren Maßnahmen erforderlich."

        # Nächste Schritte
        if not self.diagnosis_results["vip_access"]:
            report += "\n\n🔧 **NÄCHSTE SCHRITTE:**"
            report += "\n1. Account zur VIP-Gruppe hinzufügen"
            report += "\n2. MONITORED_CHAT_IDS konfigurieren"
            report += "\n3. System neu starten"
            report += "\n4. Diagnose wiederholen"

        return report
    
    async def run_full_diagnosis(self) -> None:
        """Führe vollständige Diagnose durch"""
        print("🚀 VIP-GRUPPEN PROBLEM DIAGNOSE STARTET")
        print("=" * 60)
        
        try:
            # Startmeldung senden
            start_msg = f"""🔍 **VIP-GRUPPEN DIAGNOSE GESTARTET** 🔍

🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}
🎯 **Ziel:** VIP-Gruppe ({self.vip_group_id}) Problem lösen

🔄 **Status:** Diagnose läuft..."""
            
            await self.send_report_message(start_msg)
            
            # 1. Session-Test
            print("\n1️⃣ SESSION-STATUS TEST")
            session_ok = await self.test_session_status()
            
            if not session_ok:
                error_report = await self.generate_diagnosis_report()
                await self.send_report_message(error_report)
                return
            
            # 2. Umgebungskonfiguration
            print("\n2️⃣ UMGEBUNGSKONFIGURATION TEST")
            config_status = await self.test_environment_config()
            
            # 3. VIP-Gruppen-Zugriff
            print("\n3️⃣ VIP-GRUPPEN-ZUGRIFF TEST")
            vip_entity = await self.test_vip_group_access()
            
            # 4. Mitgliedschaftstest
            if vip_entity:
                print("\n4️⃣ MITGLIEDSCHAFTSTEST")
                membership_result = await self.check_membership_status(vip_entity)
            
            # 5. Abschlussbericht
            print("\n5️⃣ ABSCHLUSSBERICHT")
            final_report = await self.generate_diagnosis_report()
            print("\n" + final_report)
            
            await self.send_report_message(final_report)
            
            # 6. Lösungsvorschlag
            if self.diagnosis_results["vip_access"]:
                solution_msg = """🎉 **LÖSUNG ERFOLGREICH!** 🎉

✅ VIP-Gruppe ist nun zugänglich!
✅ System sollte VIP-Signale empfangen können!

🚀 **Empfehlung:** System neu starten um Änderungen zu übernehmen."""
                
                await self.send_report_message(solution_msg)
            else:
                solution_msg = """🔧 **LÖSUNGSSCHRITTE** 🔧

❗ **Sofortige Maßnahmen:**
1. Account zur VIP-Gruppe hinzufügen
2. Bot-Berechtigungen in Gruppe überprüfen
3. MONITORED_CHAT_IDS konfigurieren
4. System-Neustart durchführen

📞 **Kontakt Admin:** Falls Problem weiterhin besteht"""
                
                await self.send_report_message(solution_msg)
                
        except Exception as e:
            error_msg = f"""❌ **DIAGNOSE FEHLER** ❌

⚠️ **Error:** {str(e)}
🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}

💡 **Empfehlung:** Manuelle Überprüfung erforderlich"""
            
            print(f"❌ Diagnose Fehler: {e}")
            await self.send_report_message(error_msg)
            
        finally:
            await self.client.disconnect()
            print("✅ Diagnose abgeschlossen")

async def main():
    """Hauptfunktion"""
    diagnoser = VIPGroupDiagnoser()
    await diagnoser.run_full_diagnosis()

if __name__ == "__main__":
    print("🎯 VIP-GRUPPEN PROBLEM DIAGNOSE & LÖSUNG")
    print("Identifiziert und behebt VIP-Gruppen-Zugriffsprobleme")
    print()
    
    asyncio.run(main())