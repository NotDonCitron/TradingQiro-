#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beispiel-Script mit printf-style Format-String-Problemen
Diese Datei demonstriert typische Probleme, die der Linter erkennen und beheben kann.
"""
import logging

# Beispiel 1: Dictionary-Formatierung mit ungenutzten Argumenten (Non-compliant)
error_message_1 = "Error %(message)s" % {"message": "something failed", "extra": "some dead code"}

# Beispiel 2: .format() mit zu vielen Argumenten (Non-compliant)  
error_message_2 = "Error: User {} has not been able to access {}".format("Alice", "MyFile", "ExtraArgument")

# Beispiel 3: f-string mit eckigen statt geschweiften Klammern (Non-compliant)
user = "Alice"
resource = "MyFile"
message = f"Error: User [user] has not been able to access {resource}"

# Beispiel 4: Logging mit fehlenden Argumenten (Non-compliant)
logging.error("Error: User %s has not been able to access %s", "Alice")

# Beispiel 5: .format() mit zu wenigen Argumenten (Non-compliant)
status_message = "Process {} completed with status {} at time {}".format("backup", "success")

# Beispiel 6: % Formatierung mit falschem Tupel (Non-compliant)
debug_info = "Debug: %s %s %s" % ("info1", "info2")

# Beispiel 7: Dictionary-Formatierung mit falschen Keys (Non-compliant)
template = "Hello %(name)s, you have %(count)d messages and %(status)s"
result = template % {"name": "John", "count": 5}  # 'status' fehlt

def demonstrate_problems():
    """Demonstriere die verschiedenen Format-String-Probleme"""
    print("=== BEISPIELE FÜR FORMAT-STRING-PROBLEME ===")
    
    # Diese Funktion würde bei Ausführung Fehler verursachen
    # aufgrund der obigen problematischen Format-Strings
    
    try:
        print(error_message_1)  # Würde funktionieren, aber 'extra' ist unnötig
        print(error_message_2)  # Würde einen TypeError verursachen
        print(message)          # Würde [user] und [resource] literal ausgeben
        print(status_message)   # Würde einen IndexError verursachen
        print(debug_info)       # Würde einen TypeError verursachen
        print(result)           # Würde einen KeyError verursachen
    except Exception as e:
        print(f"Fehler aufgetreten: {e}")

if __name__ == "__main__":
    print("⚠️  Dieses Script enthält absichtlich Format-String-Probleme!")
    print("Verwenden Sie den format_string_linter.py, um sie zu finden und zu beheben.")
    print()
    
    # Uncomment the next line to see the errors in action:
    # demonstrate_problems()