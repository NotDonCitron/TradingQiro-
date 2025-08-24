#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finale Codebase-Überprüfung für printf-style Format-String-Probleme
"""

import os
import sys
from format_string_linter import FormatStringLinter

def main():
    """Überprüfe die gesamte Projektcodebase auf Format-String-Probleme"""
    
    print("🔍 FINALE CODEBASE-ÜBERPRÜFUNG")
    print("=" * 60)
    print("Überprüft printf-style Format-String-Probleme in der gesamten Codebase")
    print()
    
    # Definiere die zu überprüfenden Verzeichnisse
    directories_to_check = [
        "src",
        "tests",
    ]
    
    # Definiere einzelne Python-Dateien im Hauptverzeichnis
    main_files = [
        "configure_specific_vip_group.py",
        "diagnose_vip_group_problem.py",
        "demo_signal.py",
        "find_cryptet_channel_id.py",
        "get_latest_signals.py",
        "login_with_telegram_code.py",
        "run.py",
        "show_recent_signals.py",
        "system_status_report.py",
        "test_all_sessions.py",
        "verify_system.py"
    ]
    
    linter = FormatStringLinter()
    total_issues = 0
    
    # Überprüfe Verzeichnisse
    for directory in directories_to_check:
        if os.path.exists(directory):
            print(f"📁 Überprüfe Verzeichnis: {directory}")
            issues = linter.check_directory(directory)
            if issues:
                print(f"   ❌ {len(issues)} Problem(e) gefunden")
                total_issues += len(issues)
            else:
                print(f"   ✅ Keine Probleme gefunden")
        else:
            print(f"   ⚠️  Verzeichnis nicht gefunden: {directory}")
        print()
    
    # Überprüfe einzelne Dateien
    print("📄 Überprüfe Haupt-Python-Dateien:")
    for file_path in main_files:
        if os.path.exists(file_path):
            print(f"   Prüfe: {file_path}")
            file_issues = linter.check_file(file_path)
            new_issues = [issue for issue in file_issues if issue.file_path == file_path]
            if new_issues:
                print(f"      ❌ {len(new_issues)} Problem(e) gefunden")
                total_issues += len(new_issues)
            else:
                print(f"      ✅ Keine Probleme")
        else:
            print(f"   ⚠️  Datei nicht gefunden: {file_path}")
    
    print()
    print("=" * 60)
    print("📊 FINAL-BERICHT")
    print("=" * 60)
    
    if total_issues == 0:
        print("🎉 AUSGEZEICHNET!")
        print("✅ Keine printf-style Format-String-Probleme in Ihrer Codebase gefunden!")
        print()
        print("Ihre Codebase ist sauber und folgt den Best Practices für String-Formatierung.")
        print("Die verwendeten f-strings und .format() Aufrufe sind korrekt implementiert.")
        
    else:
        print(f"⚠️  INSGESAMT: {total_issues} Format-String-Problem(e) gefunden")
        print()
        print("📋 DETAILLIERTER BERICHT:")
        linter.print_report()
        
        print("\n🔧 EMPFOHLENE AKTIONEN:")
        print("1. Überprüfen Sie die oben aufgelisteten Probleme")
        print("2. Führen Sie den Linter mit --fix für automatische Korrekturen aus:")
        print("   python format_string_linter.py [datei] --fix")
        print("3. Beheben Sie verbleibende Probleme manuell")
        print("4. Integrieren Sie den Linter in Ihren Entwicklungsworkflow")
        
    print()
    print("🛠️  VERFÜGBARE WERKZEUGE:")
    print("• format_string_linter.py - Hauptwerkzeug zur Problemerkennung")
    print("• example_format_problems.py - Beispiele für häufige Probleme")
    print("• FORMAT_STRING_LINTER_GUIDE.md - Vollständige Anleitung")
    
    print()
    print("💡 TIPPS FÜR DIE ZUKUNFT:")
    print("• Verwenden Sie f-strings für neue String-Formatierung")
    print("• Nutzen Sie named placeholders in .format() für bessere Lesbarkeit")
    print("• Integrieren Sie den Linter in Ihre IDE oder CI/CD Pipeline")
    print("• Führen Sie regelmäßige Code-Quality-Checks durch")
    
    return total_issues == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)