#!/usr/bin/env python3
"""
Live System Monitoring - Verfolgt die Echtzeit-Signal-Verarbeitung
"""

import requests
import time
import redis
import json
from datetime import datetime

def monitor_live_system(duration=30):
    """Überwacht das Live-System für X Sekunden."""
    print("🔍 LIVE SYSTEM MONITORING")
    print("=" * 50)
    
    r = redis.from_url("redis://localhost:6379/0")
    
    baseline_metrics = None
    
    for second in range(duration):
        try:
            # Hole aktuelle Metriken
            response = requests.get("http://localhost:8080/metrics", timeout=2)
            metrics = response.json() if response.status_code == 200 else {}
            
            # Queue-Größen aus Redis
            tg_queue = r.llen("telegram_messages")
            parsed_queue = r.llen("parsed_signals")
            logs_count = r.llen("forwarding_logs")
            
            # Baseline setzen
            if baseline_metrics is None:
                baseline_metrics = metrics.copy()
                baseline_logs = logs_count
            
            # Berechne Deltas
            forwarded_delta = metrics.get('total_forwarded_signals', 0) - baseline_metrics.get('total_forwarded_signals', 0)
            logs_delta = logs_count - baseline_logs
            
            # Status anzeigen
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"⏱️  {timestamp} | TG: {tg_queue:2d} | Parsed: {parsed_queue:2d} | Total: {metrics.get('total_forwarded_signals', 0):2d} | +{forwarded_delta:2d} | Logs: +{logs_delta:2d}")
            
            # Teste gelegentlich ein neues Signal
            if second in [5, 15, 25]:
                test_signal = {
                    "text": f"🧪 TEST {second}s: BUY BTCUSDT 0.{second}",
                    "chat_id": -1002299206473,
                    "message_id": int(time.time() * 1000),
                    "sender_id": 999999,
                    "timestamp": datetime.now().isoformat(),
                    "source": "live_test"
                }
                r.lpush("telegram_messages", json.dumps(test_signal))
                print(f"     📤 Test-Signal gesendet: BUY BTCUSDT 0.{second}")
            
        except Exception as e:
            print(f"❌ {second:2d}s | Error: {e}")
        
        time.sleep(1)
    
    print(f"\n📊 MONITORING BEENDET")
    print(f"🔥 Neue verarbeitete Signale: {forwarded_delta}")
    print(f"📝 Neue Log-Einträge: {logs_delta}")

if __name__ == "__main__":
    monitor_live_system()