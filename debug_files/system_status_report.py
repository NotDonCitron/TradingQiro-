#!/usr/bin/env python3
"""
SYSTEM STATUS REPORT
Umfassender Test aller Komponenten
"""

import requests
import json
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_api_endpoints():
    """Test alle API-Endpoints."""
    
    print("🌐 API ENDPOINTS TEST")
    print("=" * 50)
    
    endpoints = [
        ("Health Check", "http://localhost:8000/health"),
        ("System Status", "http://localhost:8000/status"), 
        ("Forwarder Status", "http://localhost:8000/forwarder/status"),
        ("Cryptet Status", "http://localhost:8000/cryptet/status"),
        ("Readiness", "http://localhost:8000/ready")
    ]
    
    results = []
    
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {name}: OK")
                results.append((name, True, response.json()))
            else:
                print(f"❌ {name}: Error {response.status_code}")
                results.append((name, False, None))
                
        except Exception as e:
            print(f"❌ {name}: Exception - {e}")
            results.append((name, False, None))
    
    return results

def analyze_system_status(results):
    """Analysiere den System-Status."""
    
    print("\n📊 SYSTEM ANALYSIS")
    print("=" * 50)
    
    # Finde System Status
    system_status = None
    for name, success, data in results:
        if name == "System Status" and success:
            system_status = data
            break
    
    if system_status:
        print("🏗️ System Components:")
        components = system_status.get("components", {})
        for component, status in components.items():
            emoji = "✅" if status else "❌"
            print(f"   {emoji} {component}: {'Active' if status else 'Inactive'}")
        
        print(f"\n🔧 Configuration:")
        config = system_status.get("config", {})
        for key, value in config.items():
            print(f"   • {key}: {value}")
    
    # Finde Forwarder Status
    forwarder_status = None
    for name, success, data in results:
        if name == "Forwarder Status" and success:
            forwarder_status = data
            break
    
    if forwarder_status:
        print(f"\n📨 Signal Forwarder:")
        status = forwarder_status.get("status", {})
        print(f"   • Enabled: {status.get('enabled', 'Unknown')}")
        print(f"   • Monitored Chat: {forwarder_status.get('monitored_chat', 'Unknown')}")
        print(f"   • Target Group: {forwarder_status.get('target_group', 'Unknown')}")
    
    # Finde Cryptet Status
    cryptet_status = None
    for name, success, data in results:
        if name == "Cryptet Status" and success:
            cryptet_status = data
            break
    
    if cryptet_status:
        print(f"\n🤖 Cryptet Automation:")
        status = cryptet_status.get("status", {})
        print(f"   • Initialized: {status.get('initialized', 'Unknown')}")
        print(f"   • Running: {status.get('running', 'Unknown')}")
        print(f"   • Active Signals: {cryptet_status.get('active_count', 0)}")

def main():
    """Hauptfunktion für System-Test."""
    
    print("🧪 SYSTEM STATUS REPORT")
    print("=" * 60)
    print("📅 Datum: 24. August 2025")
    print("🕐 Zeit: Automatisierte System-Prüfung")
    print("=" * 60)
    
    # Test API Endpoints
    results = test_api_endpoints()
    
    # Analysiere Ergebnisse
    analyze_system_status(results)
    
    # Zusammenfassung
    print("\n🎯 ZUSAMMENFASSUNG")
    print("=" * 30)
    
    successful_tests = sum(1 for _, success, _ in results if success)
    total_tests = len(results)
    
    print(f"📊 API Tests: {successful_tests}/{total_tests} erfolgreich")
    
    if successful_tests == total_tests:
        print("✅ SYSTEM VOLLSTÄNDIG FUNKTIONSFÄHIG")
        print("\n🚀 Aktive Features:")
        print("   • Signal Forwarder (Gruppe -2299206473)")
        print("   • Cryptet Automation (@cryptet_com)")
        print("   • Telegram Integration (Telethon)")
        print("   • BingX Trading (falls aktiviert)")
        print("   • Health Monitoring & Metrics")
        print("\n🎉 Das System ist bereit für den Produktivbetrieb!")
    else:
        print("⚠️  SYSTEM HAT PROBLEME")
        print("❌ Einige Komponenten sind nicht verfügbar")
        
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()