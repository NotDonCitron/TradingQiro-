#!/usr/bin/env python3
"""
Test-Signal-Sender für Trading Bot
Sendet verschiedene Test-Signale an die Pipeline
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"

def send_test_signal(message, metadata=None):
    """Sendet ein Test-Signal an die API."""
    if metadata is None:
        metadata = {
            "source": "test",
            "chat_id": 123456789,
            "message_id": int(time.time())
        }
    
    payload = {
        "message": message,
        "metadata": metadata
    }
    
    try:
        print(f"📤 Sende Signal: {message}")
        response = requests.post(
            f"{BASE_URL}/test/signal",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Erfolgreich: {result}")
            return True
        else:
            print(f"❌ Fehler {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def get_metrics():
    """Holt aktuelle System-Metriken."""
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.json()
            print(f"📊 Metriken: {metrics}")
            return metrics
        else:
            print(f"❌ Metrics-Fehler: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Metrics-Exception: {e}")
        return None

def run_signal_tests():
    """Führt eine Serie von Signal-Tests durch."""
    print("🧪 SIGNAL PROCESSING TESTS")
    print("=" * 50)
    
    # Baseline-Metriken
    print("\n📊 BASELINE METRIKEN:")
    baseline = get_metrics()
    
    test_signals = [
        # Einfache Trading-Signale
        "BUY BTCUSDT 0.1",
        "SELL ETHUSDT 2.5", 
        "BUY SOLUSDT 10",
        
        # Signale mit Preisen
        "BUY BTCUSDT 0.05 at 45000",
        "SELL ADAUSDT 1000 at 0.35",
        
        # Komplexere Signale
        "BUY DOGEUSDT 5000 SL 0.08 TP 0.12",
        "SELL BNBUSDT 2.0 SL 350 TP 300",
        
        # Cornix-Style Signale
        "🟢 Long\nBTC/USDT\nEntry: 45000\nTP1: 46000\nTP2: 47000\nSL: 44000",
        
        # Ungültige Signale (sollten gefiltert werden)
        "INVALID_SIGNAL_TEST",
        "Random text without trading info",
    ]
    
    successful_tests = 0
    
    for i, signal in enumerate(test_signals, 1):
        print(f"\n🧪 TEST {i}/{len(test_signals)}")
        print("-" * 30)
        
        success = send_test_signal(signal)
        if success:
            successful_tests += 1
            
        # Kurze Pause zwischen Tests
        time.sleep(1)
        
        # Metriken nach jedem 3. Test prüfen
        if i % 3 == 0:
            print(f"\n📊 ZWISCHENSTAND nach {i} Tests:")
            get_metrics()
    
    print(f"\n🎯 TEST-ZUSAMMENFASSUNG:")
    print("=" * 50)
    print(f"✅ Erfolgreiche Tests: {successful_tests}/{len(test_signals)}")
    print(f"📊 Erfolgsrate: {(successful_tests/len(test_signals)*100):.1f}%")
    
    print(f"\n📊 FINALE METRIKEN:")
    final_metrics = get_metrics()
    
    if baseline and final_metrics:
        new_signals = final_metrics.get('total_forwarded_signals', 0) - baseline.get('total_forwarded_signals', 0)
        print(f"🔥 Neue verarbeitete Signale: {new_signals}")

if __name__ == "__main__":
    run_signal_tests()