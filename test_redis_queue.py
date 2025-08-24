#!/usr/bin/env python3
"""
Direkter Redis Queue Test - Sendet echte Signale an die Telegram Queue
"""

import redis
import json
import time
from datetime import datetime, timezone

def send_direct_telegram_signal(message_text, chat_id=-1002299206473):
    """Sendet direkt eine Nachricht an die Telegram-Queue."""
    
    # Redis-Verbindung
    r = redis.from_url("redis://localhost:6379/0")
    
    # Signal-Objekt erstellen
    signal = {
        "text": message_text,
        "chat_id": chat_id,
        "message_id": int(time.time() * 1000),
        "sender_id": 999999,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "direct_test"
    }
    
    # In die Queue einreihen
    r.lpush("telegram_messages", json.dumps(signal))
    
    print(f"📤 Signal an Queue gesendet: {message_text}")
    print(f"🔢 Queue-Position: {r.llen('telegram_messages')}")
    
    return signal

def monitor_queue_processing():
    """Überwacht die Queue-Verarbeitung in Echtzeit."""
    r = redis.from_url("redis://localhost:6379/0")
    
    print("\n🔍 QUEUE-MONITORING gestartet...")
    print("=" * 50)
    
    for i in range(30):  # 30 Sekunden monitoren
        telegram_queue = r.llen("telegram_messages")
        parsed_queue = r.llen("parsed_signals")
        
        print(f"⏱️  {i+1:2d}s | Telegram: {telegram_queue:2d} | Parsed: {parsed_queue:2d}")
        
        # Beende wenn beide Queues leer sind
        if telegram_queue == 0 and parsed_queue == 0 and i > 5:
            print("✅ Alle Queues verarbeitet!")
            break
            
        time.sleep(1)

def run_direct_redis_tests():
    """Führt direkte Redis-Queue-Tests durch."""
    print("🔥 DIREKTE REDIS QUEUE TESTS")
    print("=" * 50)
    
    test_signals = [
        "🟢 Long\nName: BTCUSDT\nMargin mode: Cross (50X)\n\n↪️ Entry price(USDT):\n65000.00\n\nTargets(USDT):\n1) 66000.00\n2) 67000.00\n3) 68000.00",
        "🔴 Short\nName: ETHUSDT\nMargin mode: Cross (20X)\n\n↪️ Entry price(USDT):\n2400.00\n\nTargets(USDT):\n1) 2350.00\n2) 2300.00",
        "BUY SOLUSDT 0.5",
        "SELL ADAUSDT 1000 at 0.35",
        "Binance, BingX Spot, Bitget Spot\n#BTC/USDT Take-Profit target 1 ✅\nProfit: 2.22% 📈\nPeriod: 1h 30m ⏰"
    ]
    
    print(f"📊 Baseline Queue-Status:")
    r = redis.from_url("redis://localhost:6379/0")
    print(f"   Telegram: {r.llen('telegram_messages')}")
    print(f"   Parsed: {r.llen('parsed_signals')}")
    
    # Sende alle Test-Signale
    for i, signal in enumerate(test_signals, 1):
        print(f"\n🧪 TEST {i}: Redis Queue Injection")
        print(f"📝 Signal: {signal[:50]}...")
        send_direct_telegram_signal(signal)
        time.sleep(0.5)  # Kurze Pause zwischen den Signalen
    
    # Überwache die Verarbeitung
    monitor_queue_processing()
    
    # Finale Queue-Status
    print(f"\n📊 Finale Queue-Status:")
    print(f"   Telegram: {r.llen('telegram_messages')}")
    print(f"   Parsed: {r.llen('parsed_signals')}")

if __name__ == "__main__":
    run_direct_redis_tests()