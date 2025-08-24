#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIP-SIGNAL SENDER (Markdown-Fix)
Sendet das neueste VIP-Signal ohne Markdown-Probleme
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

class VIPSignalSender:
    """Sendet VIP-Signale ohne Markdown-Probleme"""
    
    def __init__(self):
        # API Credentials
        self.api_id = int(os.getenv("TELEGRAM_API_ID", "26708757"))
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "e58c6204a1478da2b764d5fceff846e5")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8496816723:AAHH-YVZdmoueA_cV9lcJncUyIR3N3Vizbw")
        
        # Session
        self.session_name = "user_telegram_session"
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Konfiguration
        self.vip_group_id = int(os.getenv("VIP_GROUP_ID", "-1001437466982"))
        self.target_group_id = int(os.getenv("TARGET_GROUP_ID", "-1002773853382"))
        self.vip_group_title = os.getenv("VIP_GROUP_TITLE", "VIP Group")
    
    def clean_text_for_telegram(self, text: str) -> str:
        """Bereinige Text für Telegram ohne Markdown-Probleme"""
        if not text:
            return ""
        
        # Entferne problematische Markdown-Zeichen
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
        """Sende Nachricht ohne Markdown (sicher)"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": self.clean_text_for_telegram(message),
                # Kein parse_mode für maximale Sicherheit
            }
            
            response = requests.post(url, json=data, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ Nachricht sicher gesendet an {chat_id}")
                return True
            else:
                print(f"❌ Send Error {chat_id}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Send Error: {e}")
            return False
    
    async def get_latest_signal(self) -> Optional[Dict[str, Any]]:
        """Hole das neueste Signal"""
        try:
            entity = await self.client.get_entity(self.vip_group_id)
            
            async for message in self.client.iter_messages(entity, limit=5):
                if message.text and message.text.strip():
                    # Suche nach Crypto-Paaren als Signal-Indikator
                    if re.search(r'[A-Z]{2,8}/USDT', message.text):
                        return {
                            "id": message.id,
                            "text": message.text,
                            "date": message.date,
                            "sender_id": message.sender_id if message.sender else None
                        }
            
            return None
            
        except Exception as e:
            print(f"❌ Signal-Abruf Fehler: {e}")
            return None
    
    async def send_vip_signal(self) -> None:
        """Sende das neueste VIP-Signal"""
        try:
            # Start
            await self.client.start()
            me = await self.client.get_me()
            print(f"✅ Telegram verbunden: {me.first_name}")
            
            # Start-Info
            start_info = f"""🧪 VIP-SIGNAL WEITERLEITUNGSTEST
            
Zeit: {datetime.now().strftime('%H:%M:%S')}
VIP-Quelle: {self.vip_group_title}
Status: Hole neuestes Signal..."""
            
            await self.send_message_safe(str(self.target_group_id), start_info)
            
            # Hole neuestes Signal
            signal = await self.get_latest_signal()
            
            if signal:
                print(f"📊 Signal gefunden: ID {signal['id']}")
                
                # Formatiere Signal-Info
                signal_info = f"""📊 VIP-SIGNAL WEITERGELEITET

Quelle: {self.vip_group_title}
Signal-ID: {signal['id']}
Zeit: {signal['date'].strftime('%H:%M:%S') if signal['date'] else 'Unknown'}

ORIGINAL-SIGNAL:
{signal['text']}

Status: Erfolgreich von VIP-Gruppe empfangen und weitergeleitet!"""
                
                success = await self.send_message_safe(str(self.target_group_id), signal_info)
                
                if success:
                    print("🎉 VIP-Signal erfolgreich weitergeleitet!")
                else:
                    print("❌ Weiterleitung fehlgeschlagen")
            else:
                no_signal_msg = f"""⚠️ KEINE AKTUELLEN SIGNALE
                
VIP-Gruppe: {self.vip_group_title}
Durchsucht: Letzte 5 Nachrichten
Ergebnis: Keine Trading-Signale mit Crypto-Paaren gefunden

Empfehlung: Später erneut versuchen oder längeren Zeitraum durchsuchen"""
                
                await self.send_message_safe(str(self.target_group_id), no_signal_msg)
            
        except Exception as e:
            error_msg = f"""❌ VIP-SIGNAL FEHLER

Error: {str(e)}
Zeit: {datetime.now().strftime('%H:%M:%S')}

Empfehlung: System-Diagnose erforderlich"""
            
            print(f"❌ Fehler: {e}")
            await self.send_message_safe(str(self.target_group_id), error_msg)
            
        finally:
            await self.client.disconnect()

async def main():
    sender = VIPSignalSender()
    await sender.send_vip_signal()

if __name__ == "__main__":
    print("📊 VIP-SIGNAL SENDER (Markdown-Fix)")
    print("Sendet das neueste VIP-Signal sicher weiter")
    print()
    
    asyncio.run(main())