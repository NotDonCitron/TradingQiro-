#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIVE CRYPTET SYSTEM STARTER
Startet das verbesserte System für kontinuierlichen Betrieb
"""

import asyncio
import os
import sys
from datetime import datetime
import subprocess

def check_requirements():
    """Prüfe System-Anforderungen"""
    print("🔍 SYSTEM-ANFORDERUNGEN PRÜFEN")
    print("=" * 40)
    
    # Python-Version
    python_version = sys.version_info
    print(f"✅ Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Erforderliche Dateien
    required_files = [
        ".env",
        "cookies.txt", 
        "user_telegram_session.session",
        "src/main.py"
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - FEHLT!")
            missing_files.append(file)
    
    # Erforderliche Dependencies
    try:
        import telethon
        print(f"✅ Telethon: {telethon.__version__}")
    except ImportError:
        print("❌ Telethon - NICHT INSTALLIERT!")
        missing_files.append("telethon")
    
    try:
        import selenium
        print(f"✅ Selenium: {selenium.__version__}")
    except ImportError:
        print("❌ Selenium - NICHT INSTALLIERT!")
        missing_files.append("selenium")
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("✅ ChromeDriverManager")
    except ImportError:
        print("❌ webdriver-manager - NICHT INSTALLIERT!")
        missing_files.append("webdriver-manager")
    
    if missing_files:
        print(f"\n❌ FEHLENDE ANFORDERUNGEN: {missing_files}")
        print("Bitte installiere die fehlenden Komponenten vor dem Start!")
        return False
    
    print("\n✅ ALLE ANFORDERUNGEN ERFÜLLT!")
    return True

def show_system_status():
    """Zeige System-Status"""
    print("\n🎯 LIVE CRYPTET SYSTEM STATUS")
    print("=" * 40)
    
    # Environment-Variablen prüfen
    env_vars = [
        "TELEGRAM_API_ID",
        "TELEGRAM_API_HASH", 
        "TELEGRAM_BOT_TOKEN",
        "OWN_GROUP_CHAT_ID",
        "CRYPTET_ENABLED",
        "MONITORED_CHAT_IDS"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Sensible Daten maskieren
            if "TOKEN" in var or "HASH" in var:
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NICHT GESETZT!")
    
    print(f"\n📊 ÜBERWACHTE CHATS:")
    monitored = os.getenv("MONITORED_CHAT_IDS", "")
    if monitored:
        chat_ids = [id.strip() for id in monitored.split(",")]
        for chat_id in chat_ids:
            if chat_id == "-1001804143400":
                print(f"   🔗 {chat_id} (Cryptet Official Channel)")
            elif chat_id == "-2299206473":
                print(f"   📊 {chat_id} (VIP Signal Group)")
            else:
                print(f"   📡 {chat_id}")
    else:
        print("   ⚠️ Keine Chats konfiguriert")
    
    target_group = os.getenv("OWN_GROUP_CHAT_ID")
    if target_group:
        print(f"\n🎯 ZIELGRUPPE: {target_group}")
    else:
        print("\n❌ ZIELGRUPPE: Nicht konfiguriert!")

def show_live_instructions():
    """Zeige Live-Betrieb Anweisungen"""
    print("\n🚀 LIVE-BETRIEB ANWEISUNGEN")
    print("=" * 40)
    print("Das System wird jetzt kontinuierlich laufen und:")
    print("• 📡 Cryptet-Kanal überwachen (-1001804143400)")
    print("• 🔗 Cryptet-Links automatisch erkennen")  
    print("• 🌐 Webseite scrapen und Signal extrahieren")
    print("• 🎯 Cornix-Format mit Cross 50x erstellen")
    print("• 📤 Signal an deine Gruppe weiterleiten")
    print()
    print("📋 KONTROLLE:")
    print("• STRG+C zum Stoppen")
    print("• Logs in der Konsole verfolgen")
    print("• Browser läuft im Hintergrund")
    print()
    print("🌐 API-ENDPUNKTE (während Betrieb):")
    print("• http://localhost:8080/health - System-Status")
    print("• http://localhost:8080/cryptet/status - Cryptet-Status") 
    print("• http://localhost:8080/status - Vollständiger Status")
    print()
    print("🎯 Bei neuen Cryptet-Signalen siehst du:")
    print("1. Telegram-Message erkannt")
    print("2. URL extrahiert")  
    print("3. Browser-Scraping startet")
    print("4. Signal geparst")
    print("5. Cornix-Format erstellt")
    print("6. Signal weitergeleitet")

async def start_live_system():
    """Starte das Live-System"""
    print("\n🚀 STARTE LIVE CRYPTET SYSTEM")
    print("=" * 40)
    print(f"🕐 Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Wechsle ins src-Verzeichnis und starte main.py
        print("▶️ Starte src/main.py...")
        
        # Verwende das Python aus der aktuellen Umgebung
        python_executable = sys.executable
        
        # Starte das Hauptsystem
        result = subprocess.run([
            python_executable, "src/main.py"
        ], cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ System ordnungsgemäß beendet")
        else:
            print(f"❌ System mit Fehlercode beendet: {result.returncode}")
            
    except KeyboardInterrupt:
        print("\n⏹️ System durch Benutzer gestoppt (STRG+C)")
    except Exception as e:
        print(f"\n❌ System-Fehler: {e}")

def main():
    """Hauptfunktion"""
    print("🤖 LIVE CRYPTET SYSTEM STARTER")
    print("=" * 50)
    print("Verbesserte Pipeline: Telegram → Scraping → Cornix → Forward")
    print()
    
    # 1. Anforderungen prüfen
    if not check_requirements():
        print("\n❌ System kann nicht gestartet werden!")
        print("💡 Bitte installiere die fehlenden Komponenten:")
        print("   pip install telethon selenium webdriver-manager beautifulsoup4")
        return
    
    # 2. System-Status anzeigen
    show_system_status()
    
    # 3. Anweisungen anzeigen
    show_live_instructions()
    
    # 4. Bestätigung
    print("\n" + "="*50)
    print("🎯 BEREIT FÜR LIVE-BETRIEB!")
    print("Das System wird Cryptet-Signale automatisch verarbeiten.")
    print()
    
    try:
        input("👉 Drücke ENTER um das Live-System zu starten (oder STRG+C zum Abbrechen)...")
        
        # 5. System starten
        asyncio.run(start_live_system())
        
    except KeyboardInterrupt:
        print("\n👋 System-Start abgebrochen")

if __name__ == "__main__":
    main()