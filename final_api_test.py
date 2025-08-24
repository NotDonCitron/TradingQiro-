#!/usr/bin/env python3
"""
FINALE API-TESTS (ohne Redis)
Testet alle verfügbaren API-Endpunkte
"""

import requests
import json
import time

def final_api_tests():
    """Finale API-Tests."""
    print("🎯 FINALE API-TESTS")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # Test-Endpunkte
    endpoints = [
        ("Health Check", "/health", "GET"),
        ("Service Status", "/services", "GET"), 
        ("System Metrics", "/metrics", "GET"),
    ]
    
    results = {}
    
    for name, endpoint, method in endpoints:
        print(f"\n🧪 {name}")
        print("-" * 30)
        
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                
                # Spezielle Ausgaben je Endpunkt
                if endpoint == "/health":
                    print(f"   🏥 Health: {data.get('status', 'unknown')}")
                    services = data.get('services', {})
                    for service, status in services.items():
                        print(f"   📊 {service}: {status}")
                        
                elif endpoint == "/services":
                    services = data.get('services', {})
                    for service, info in services.items():
                        status = info.get('status', 'unknown')
                        print(f"   🔧 {service}: {status}")
                    
                    queues = data.get('queues', {})
                    print(f"   📬 Queues:")
                    for queue, size in queues.items():
                        print(f"      📨 {queue}: {size}")
                        
                elif endpoint == "/metrics":
                    for key, value in data.items():
                        print(f"   📈 {key}: {value}")
                
                results[name] = {"success": True, "data": data}
                
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"   Error: {response.text}")
                results[name] = {"success": False, "status": response.status_code}
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            results[name] = {"success": False, "error": str(e)}
    
    # Container-Status
    print(f"\n🐳 CONTAINER STATUS")
    print("-" * 30)
    
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            container_count = 0
            healthy_count = 0
            
            for line in lines:
                if "trading-bot" in line or "telegram" in line or "signal" in line or "redis" in line:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            name, status = parts[0], parts[1]
                            container_count += 1
                            
                            if "healthy" in status.lower() or "up" in status.lower():
                                print(f"✅ {name}: {status}")
                                healthy_count += 1
                            elif "unhealthy" in status.lower():
                                print(f"❌ {name}: {status}")
                            else:
                                print(f"⚠️  {name}: {status}")
            
            print(f"\n📊 Container-Zusammenfassung: {healthy_count}/{container_count} gesund")
            
    except Exception as e:
        print(f"❌ Container Status Error: {e}")
    
    # Zusammenfassung
    print(f"\n🎉 FINALE ZUSAMMENFASSUNG")
    print("=" * 50)
    
    success_count = sum(1 for r in results.values() if r.get('success', False))
    total_tests = len(results)
    
    print(f"✅ Erfolgreiche API-Tests: {success_count}/{total_tests}")
    print(f"📊 Erfolgsrate: {(success_count/total_tests*100):.1f}%")
    
    # Signal-Processing-Status
    if 'System Metrics' in results and results['System Metrics'].get('success'):
        metrics = results['System Metrics']['data']
        total_signals = metrics.get('total_forwarded_signals', 0)
        system_healthy = metrics.get('system_healthy', 0)
        
        print(f"🔥 Verarbeitete Signale: {total_signals}")
        print(f"💚 System-Health: {'✅ Gesund' if system_healthy == 1 else '❌ Ungesund'}")
    
    if 'Service Status' in results and results['Service Status'].get('success'):
        queues = results['Service Status']['data'].get('queues', {})
        tg_queue = queues.get('telegram_messages', 0)
        parsed_queue = queues.get('parsed_signals', 0)
        
        if tg_queue == 0 and parsed_queue == 0:
            print(f"⚡ Queue-Status: Alle Queues leer (= schnelle Verarbeitung)")
        else:
            print(f"📬 Queue-Status: TG={tg_queue}, Parsed={parsed_queue}")

if __name__ == "__main__":
    final_api_tests()