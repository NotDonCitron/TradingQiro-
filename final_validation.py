#!/usr/bin/env python3
"""
FINALE SYSTEM-VALIDIERUNG
Umfassender Test aller Komponenten mit detaillierter Ausgabe
"""

import requests
import redis
import json
import time
from datetime import datetime

def comprehensive_system_test():
    """Umfassender System-Test."""
    print("🎯 FINALE SYSTEM-VALIDIERUNG")
    print("=" * 60)
    
    # Test 1: API Health
    print("\n1. 🏥 API HEALTH CHECK")
    print("-" * 30)
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health: {data.get('status', 'unknown')}")
            for service, status in data.get('services', {}).items():
                print(f"   📊 {service}: {status}")
        else:
            print(f"❌ API Health failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API Health exception: {e}")
    
    # Test 2: Service Status
    print("\n2. 🔧 SERVICE STATUS")
    print("-" * 30)
    try:
        response = requests.get("http://localhost:8080/services", timeout=5)
        if response.status_code == 200:
            data = response.json()
            for service, info in data.get('services', {}).items():
                status = info.get('status', 'unknown')
                desc = info.get('description', 'No description')
                print(f"✅ {service}: {status} - {desc}")
            
            queues = data.get('queues', {})
            print(f"\n📊 Queue-Status:")
            for queue, size in queues.items():
                print(f"   📬 {queue}: {size}")
                
        else:
            print(f"❌ Service Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Service Status exception: {e}")
    
    # Test 3: Current Metrics
    print("\n3. 📊 AKTUELLE METRIKEN")
    print("-" * 30)
    try:
        response = requests.get("http://localhost:8080/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.json()
            for key, value in metrics.items():
                print(f"📈 {key}: {value}")
        else:
            print(f"❌ Metrics failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Metrics exception: {e}")
    
    # Test 4: Redis Direct Access
    print("\n4. 🔴 REDIS DIRECT ACCESS")
    print("-" * 30)
    try:
        r = redis.from_url("redis://localhost:6379/0")
        info = r.info()
        print(f"✅ Redis verbunden")
        print(f"   🔗 Verbindungen: {info.get('connected_clients', 'N/A')}")
        print(f"   💾 Memory: {info.get('used_memory_human', 'N/A')}")
        print(f"   ⏱️  Uptime: {info.get('uptime_in_seconds', 0)} Sekunden")
        
        # Queue-Größen prüfen
        tg_queue = r.llen("telegram_messages")
        parsed_queue = r.llen("parsed_signals")
        logs_queue = r.llen("forwarding_logs")
        
        print(f"\n📬 Redis Queues:")
        print(f"   📱 telegram_messages: {tg_queue}")
        print(f"   🔍 parsed_signals: {parsed_queue}")
        print(f"   📝 forwarding_logs: {logs_queue}")
        
    except Exception as e:
        print(f"❌ Redis exception: {e}")
    
    # Test 5: Signal Injection & Processing
    print("\n5. 🧪 SIGNAL PROCESSING TEST")
    print("-" * 30)
    
    try:
        r = redis.from_url("redis://localhost:6379/0")
        
        # Baseline
        baseline_logs = r.llen("forwarding_logs")
        baseline_metrics = requests.get("http://localhost:8080/metrics").json()
        baseline_total = baseline_metrics.get('total_forwarded_signals', 0)
        
        print(f"📊 Baseline: {baseline_total} verarbeitete Signale")
        
        # Test-Signal senden
        test_signal = {
            "text": "🎯 FINAL TEST: BUY BTCUSDT 0.1337",
            "chat_id": -1002299206473,
            "message_id": int(time.time() * 1000),
            "sender_id": 999999,
            "timestamp": datetime.now().isoformat(),
            "source": "final_validation"
        }
        
        print(f"📤 Sende Test-Signal...")
        r.lpush("telegram_messages", json.dumps(test_signal))
        
        # Warte und prüfe Verarbeitung
        for i in range(10):
            time.sleep(1)
            
            current_tg = r.llen("telegram_messages")
            current_parsed = r.llen("parsed_signals")
            current_logs = r.llen("forwarding_logs")
            
            print(f"   ⏱️  {i+1}s: TG={current_tg}, Parsed={current_parsed}, Logs={current_logs}")
            
            if current_tg == 0 and current_parsed == 0:
                print(f"✅ Signal verarbeitet in {i+1} Sekunden!")
                break
        else:
            print("⚠️  Signal-Verarbeitung dauert länger als erwartet...")
        
        # Finale Metriken
        final_metrics = requests.get("http://localhost:8080/metrics").json()
        final_total = final_metrics.get('total_forwarded_signals', 0)
        delta = final_total - baseline_total
        
        print(f"📊 Finale: {final_total} verarbeitete Signale (+{delta})")
        
    except Exception as e:
        print(f"❌ Signal Processing exception: {e}")
    
    # Test 6: Container Health
    print("\n6. 🐳 CONTAINER HEALTH")
    print("-" * 30)
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=trading-bot", "--format", "table {{.Names}}\\t{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    name, status = line.split('\t', 1)
                    if "healthy" in status.lower():
                        print(f"✅ {name}: {status}")
                    elif "unhealthy" in status.lower():
                        print(f"❌ {name}: {status}")
                    else:
                        print(f"⚠️  {name}: {status}")
        else:
            print(f"❌ Docker ps failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Container Health exception: {e}")
    
    print(f"\n🎉 VALIDIERUNG ABGESCHLOSSEN!")
    print("=" * 60)

if __name__ == "__main__":
    comprehensive_system_test()