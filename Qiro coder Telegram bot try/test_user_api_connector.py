#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Service für die User-API-Funktionalität des TelethonConnectors
"""
import asyncio
import sys
import os
from datetime import datetime

# Füge src zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from connectors.telethon_connector import TelethonConnector
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class UserApiTester:
    def __init__(self):
        self.connector = TelethonConnector()
        self.received_messages = []
        
    async def message_handler(self, message: str, metadata: dict):
        """Handler für eingehende Nachrichten"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        chat_id = metadata.get("chat_id")
        message_id = metadata.get("message_id")
        
        print(f"\n🎯 [{timestamp}] NEUE NACHRICHT:")
        print(f"   Chat ID: {chat_id}")
        print(f"   Message ID: {message_id}")
        print(f"   Inhalt: {message[:100]}{'...' if len(message) > 100 else ''}")
        
        # Speichere für spätere Analyse
        self.received_messages.append({
            "timestamp": timestamp,
            "chat_id": chat_id,
            "message_id": message_id,
            "message": message,
            "metadata": metadata
        })
        
        # Analysiere auf Trading-Signale
        signal_keywords = ["LONG", "SHORT", "BUY", "SELL", "TP", "SL", "ENTRY", "KAUFEN", "VERKAUFEN"]
        if any(keyword.upper() in message.upper() for keyword in signal_keywords):
            print("   🚨 MÖGLICHES TRADING-SIGNAL ERKANNT!")
        
    async def get_chat_info(self, chat_id: int):
        """Hole Chat-Informationen"""
        try:
            entity = await self.connector.client.get_entity(chat_id)
            return {
                "id": entity.id,
                "title": getattr(entity, "title", "Unknown"),
                "username": getattr(entity, "username", None),
                "type": type(entity).__name__,
                "participants_count": getattr(entity, "participants_count", "Unknown")
            }
        except Exception as e:
            return {"id": chat_id, "error": str(e)}
    
    async def get_recent_messages(self, chat_id: int, limit: int = 5):
        """Hole die letzten Nachrichten aus einem Chat"""
        try:
            entity = await self.connector.client.get_entity(chat_id)
            messages = []
            
            async for message in self.connector.client.iter_messages(entity, limit=limit):
                if message.text:
                    messages.append({
                        "id": message.id,
                        "text": message.text,
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S") if message.date else "Unknown",
                        "sender_id": getattr(message.sender, "id", "Unknown") if message.sender else "Unknown"
                    })
            
            return messages
        except Exception as e:
            print(f"❌ Fehler beim Abrufen von Nachrichten aus Chat {chat_id}: {e}")
            return []
    
    async def run_test(self):
        """Führe den kompletten Test aus"""
        print("🚀 STARTE USER-API CONNECTOR TEST")
        print("=" * 60)
        
        try:
            # 1. Starte Connector
            print("\n1️⃣ STARTE TELEGRAM USER CLIENT...")
            self.connector.register_message_handler(self.message_handler)
            await self.connector.start()
            
            # 2. Teste Chat-Zugriff
            print("\n2️⃣ TESTE CHAT-ZUGRIFF...")
            chat_configs = {
                "VIP Signal Group": -2299206473,
                "Cryptet Official Channel": -1001804143400,
                "PH FUTURES VIP": -1002773853382
            }
            
            for chat_name, chat_id in chat_configs.items():
                print(f"\n>>> {chat_name} (ID: {chat_id}) <<<")
                
                # Chat-Info
                chat_info = await self.get_chat_info(chat_id)
                if "error" not in chat_info:
                    print(f"✅ Chat-Info:")
                    print(f"   Titel: {chat_info.get('title')}")
                    print(f"   Typ: {chat_info.get('type')}")
                    print(f"   Username: @{chat_info.get('username', 'N/A')}")
                    print(f"   Teilnehmer: {chat_info.get('participants_count')}")
                    
                    # Letzte Nachrichten
                    messages = await self.get_recent_messages(chat_id, 3)
                    if messages:
                        print(f"📨 Letzte {len(messages)} Nachrichten:")
                        for i, msg in enumerate(messages, 1):
                            preview = msg["text"][:50] + "..." if len(msg["text"]) > 50 else msg["text"]
                            print(f"   {i}. [{msg['date']}] {preview}")
                    else:
                        print("❌ Keine Nachrichten abgerufen")
                else:
                    print(f"❌ Fehler: {chat_info.get('error')}")
            
            # 3. Live-Monitoring (kurz)
            print("\n3️⃣ STARTE LIVE-MONITORING (30 Sekunden)...")
            print("💡 Senden Sie eine Testnachricht in eine der überwachten Gruppen!")
            
            await asyncio.sleep(30)
            
            # 4. Ergebnisse
            print("\n4️⃣ TEST-ERGEBNISSE:")
            print(f"   Empfangene Nachrichten: {len(self.received_messages)}")
            
            if self.received_messages:
                print("📊 EMPFANGENE NACHRICHTEN:")
                for i, msg in enumerate(self.received_messages, 1):
                    preview = msg["message"][:30] + "..." if len(msg["message"]) > 30 else msg["message"]
                    print(f"   {i}. [{msg['timestamp']}] Chat {msg['chat_id']}: {preview}")
            else:
                print("⚠️ Keine Nachrichten empfangen - das ist normal, wenn keine neuen Nachrichten gesendet wurden")
            
            print("\n✅ TEST ABGESCHLOSSEN")
            
        except Exception as e:
            print(f"❌ Fehler während des Tests: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n🛑 STOPPE CONNECTOR...")
            await self.connector.stop()

async def main():
    tester = UserApiTester()
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main())