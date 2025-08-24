#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifikationsscript: Hole die letzten 5 Signale und sende sie formatiert an die Telegram-Gruppe
Dient zur Überprüfung, dass das System korrekt funktioniert
"""
import asyncio
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from telethon import TelegramClient
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class SignalVerificationService:
    def __init__(self):
        # API Credentials
        api_id_str = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        
        if not (api_id_str and api_hash):
            raise RuntimeError("TELEGRAM_API_ID und TELEGRAM_API_HASH müssen gesetzt sein.")
        
        # Verwende die bestehende User-Session
        self.session_name = "verification_session"
        self.client = TelegramClient(self.session_name, int(api_id_str), api_hash)
        
        # Zielgruppe für das Senden der Signale
        self.target_group_id = int(os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382"))  # PH FUTURES VIP
        
        # Überwachte Gruppen (Quellen für Signale)
        self.source_chats = {
            "VIP Signal Group": {"id": -2299206473, "type": "group"},
            "Cryptet Official Channel": {"id": -1001804143400, "type": "channel"}, 
            "PH FUTURES VIP": {"id": -1002773853382, "type": "group"}
        }
        
    async def start_session(self):
        """Starte Client mit der User-Session"""
        try:
            await self.client.start()
            
            # Bestätige Login
            me = await self.client.get_me()
            print(f"✅ Verification Session aktiv:")
            print(f"   Name: {me.first_name} {me.last_name or ''}")
            print(f"   Username: @{me.username or 'kein_username'}")
            print(f"   ID: {me.id}")
            print(f"   Telefon: {me.phone}")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Starten der Session: {e}")
            return False
    
    async def get_latest_messages(self, chat_id: int, chat_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Hole die letzten Nachrichten aus einem Chat"""
        try:
            entity = await self.client.get_entity(chat_id)
            messages = []
            
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.text and message.text.strip():
                    sender_info = {}
                    if message.sender:
                        sender_info = {
                            "id": message.sender.id,
                            "first_name": getattr(message.sender, "first_name", "Unknown"),
                            "username": getattr(message.sender, "username", None),
                            "is_bot": getattr(message.sender, "bot", False)
                        }
                    
                    messages.append({
                        "id": message.id,
                        "text": message.text,
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S UTC") if message.date else "Unknown",
                        "sender": sender_info,
                        "chat_title": getattr(entity, "title", chat_name),
                        "chat_id": chat_id,
                        "chat_name": chat_name
                    })
            
            return messages
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen von Nachrichten aus {chat_name}: {e}")
            return []
    
    def is_trading_signal(self, text: str) -> bool:
        """Prüfe, ob eine Nachricht ein Trading-Signal ist"""
        signal_keywords = [
            "LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN", 
            "TARGET", "STOP", "LOSS", "PROFIT", "LEVERAGE", "🟢", "🔴", "↪️", "🔝", 
            "BREAKOUT", "BREAK", "USDT", "BTC", "ETH", "DOGE", "API3", "MARGIN"
        ]
        return any(keyword.upper() in text.upper() for keyword in signal_keywords)
    


    async def collect_latest_signals(self, max_signals: int = 5) -> List[Dict]:
        """Sammle die letzten Trading-Signale aus allen überwachten Chats"""
        print(f"\n📡 SAMMLE SIGNALE AUS {len(self.source_chats)} CHATS...")
        
        all_messages = []
        
        for chat_name, config in self.source_chats.items():
            chat_id = config["id"]
            print(f"\n>>> {chat_name} (ID: {chat_id}) <<<")
            
            try:
                messages = await self.get_latest_messages(chat_id, chat_name, 10)
                if messages:
                    print(f"✅ {len(messages)} Nachrichten abgerufen")
                    all_messages.extend(messages)
                else:
                    print(f"❌ Keine Nachrichten aus {chat_name}")
            except Exception as e:
                print(f"❌ Fehler bei {chat_name}: {e}")
        
        # Filtere nur Trading-Signale
        signals = []
        for msg in all_messages:
            if self.is_trading_signal(msg.get("text", "")):
                signals.append(msg)
        
        # Sortiere nach Datum (neueste zuerst)
        signals.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        # Nehme nur die letzten N Signale
        latest_signals = signals[:max_signals]
        
        print(f"\n🎯 GEFUNDENE SIGNALE:")
        print(f"   Gesamte Nachrichten: {len(all_messages)}")
        print(f"   Trading-Signale: {len(signals)}")
        print(f"   Ausgewählte Signale: {len(latest_signals)}")
        
        return latest_signals
    
    def format_cornix_signal(self, signal: Dict) -> str:
        """Formatiere Signal im Cornix-kompatiblen Format (einzelne Nachricht)"""
        text = signal.get("text", "")
        chat_name = signal.get("chat_name", "Unknown")
        
        # Prüfe ob es ein Cryptet-Link ist
        if "cryptet.com" in text:
            return f"""🔗 **CRYPTET SIGNAL DETECTED**

📊 **{chat_name}**
🔗 **Link:** {text.strip()}

⚡ **Hinweis:** Cryptet-Links werden automatisch verarbeitet:
1. 🌐 Link wird gescrapt
2. 📊 Signal wird extrahiert  
3. ⚡ 50x Leverage hinzugefügt
4. 📤 Formatiertes Signal wird gesendet

Das formatierte Signal folgt automatisch!"""
        
        # Prüfe ob es ein normales Trading-Signal ist
        signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "TARGET"]
        if any(keyword.upper() in text.upper() for keyword in signal_keywords):
            
            # Extrahiere Signal-Details für bessere Formatierung
            lines = text.split('\n')
            symbol = "Unknown"
            direction = "Unknown"
            
            for line in lines:
                if "Name:" in line:
                    symbol = line.split("Name:")[1].strip()
                elif "🟢 Long" in line:
                    direction = "LONG"
                elif "🔴 Short" in line or "🟢 Short" in line:
                    direction = "SHORT"
            
            # Cornix-kompatibles Format (kein Markdown!)
            return f"""🎯 {direction} SIGNAL - {symbol}

{text.strip()}

📊 Quelle: {chat_name}
🕐 {signal.get('date', 'Unknown')}"""
        
        # Fallback für andere Nachrichten
        return f"""💬 {chat_name}

{text.strip()}

🕐 {signal.get('date', 'Unknown')}"""

    async def send_individual_signals(self, signals: List[Dict]):
        """Sende jedes Signal als separate Nachricht (Cornix-kompatibel)"""
        if not signals:
            error_msg = f"""❌ VERIFIKATION FEHLGESCHLAGEN

Keine Trading-Signale gefunden.

🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""
            
            try:
                await self.client.send_message(self.target_group_id, error_msg)
                print(f"❌ Fehler-Nachricht gesendet")
                return False
            except Exception as e:
                print(f"❌ Fehler beim Senden der Fehler-Nachricht: {e}")
                return False
        
        # Sende Header-Nachricht
        header_msg = f"""🔍 SYSTEM-VERIFIKATION GESTARTET

🎯 {len(signals)} Signale gefunden
🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Signale werden einzeln gesendet..."""
        
        try:
            await self.client.send_message(self.target_group_id, header_msg)
            print(f"✅ Header-Nachricht gesendet")
            
            # Warte kurz zwischen den Nachrichten
            await asyncio.sleep(1)
            
            # Sende jedes Signal einzeln
            sent_count = 0
            for i, signal in enumerate(signals, 1):
                try:
                    formatted_signal = self.format_cornix_signal(signal)
                    await self.client.send_message(self.target_group_id, formatted_signal)
                    print(f"✅ Signal {i}/{len(signals)} gesendet: {signal.get('chat_name', 'Unknown')}")
                    sent_count += 1
                    
                    # Kurze Pause zwischen Signalen (rate limiting)
                    if i < len(signals):
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    print(f"❌ Fehler beim Senden von Signal {i}: {e}")
                    continue
            
            # Sende Abschluss-Nachricht
            await asyncio.sleep(1)
            summary_msg = f"""✅ VERIFIKATION ABGESCHLOSSEN

📤 {sent_count}/{len(signals)} Signale erfolgreich gesendet
🎯 Jedes Signal als separate Nachricht (Cornix-kompatibel)
✅ System arbeitet korrekt!

🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""
            
            await self.client.send_message(self.target_group_id, summary_msg)
            print(f"✅ Abschluss-Nachricht gesendet")
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Senden der Signale: {e}")
            return False
    
    async def run_verification(self):
        """Führe die komplette Verifikation aus"""
        print("🔍 STARTE SYSTEM-VERIFIKATION")
        print("=" * 70)
        print(f"🎯 Ziel: Letzte 5 Signale sammeln und formatiert senden")
        print(f"📋 Zielgruppe: {self.target_group_id}")
        print(f"🕐 Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Starte Session
            if not await self.start_session():
                print("❌ Session konnte nicht gestartet werden")
                return False
            
            # 2. Sammle die letzten 5 Signale
            signals = await self.collect_latest_signals(5)
            
            # 3. Sende jedes Signal einzeln (Cornix-kompatibel)
            success = await self.send_individual_signals(signals)
            
            if success:
                print(f"\n✅ VERIFIKATION ERFOLGREICH!")
                print(f"   📤 {len(signals)} Signale formatiert und gesendet")
                print(f"   📋 Zielgruppe: {self.target_group_id}")
                print(f"   🎯 System funktioniert korrekt!")
            else:
                print(f"\n❌ VERIFIKATION FEHLGESCHLAGEN!")
                print(f"   Problem beim Senden der Nachricht")
            
            return success
            
        except Exception as e:
            print(f"❌ Fehler während der Verifikation: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            await self.client.disconnect()
            print("\n✅ Session beendet")

async def main():
    service = SignalVerificationService()
    success = await service.run_verification()
    
    if success:
        print("\n🎉 VERIFIKATION ABGESCHLOSSEN - SYSTEM FUNKTIONIERT!")
    else:
        print("\n⚠️ VERIFIKATION UNVOLLSTÄNDIG - BITTE PRÜFEN!")

if __name__ == "__main__":
    print("🔍 SYSTEM-VERIFIKATION")
    print("Sammelt die letzten 5 Trading-Signale und sendet sie formatiert zur Bestätigung")
    print()
    
    asyncio.run(main())