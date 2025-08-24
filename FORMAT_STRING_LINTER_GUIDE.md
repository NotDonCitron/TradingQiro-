# Format-String-Linter für Python

## Übersicht

Dieses Werkzeug erkennt und behebt automatisch häufige printf-style Format-String-Probleme in Python-Code. Es hilft dabei, Fehler zu vermeiden, die durch Mismatches zwischen Format-Spezifizierern und bereitgestellten Argumenten entstehen.

## Installation und Verwendung

### Grundlegende Verwendung

```bash
# Prüfe eine einzelne Datei
python format_string_linter.py datei.py

# Prüfe ein ganzes Verzeichnis
python format_string_linter.py src/

# Prüfe mit automatischer Korrektur (mit Bestätigung)
python format_string_linter.py datei.py --fix

# Prüfe mit automatischer Korrektur (ohne Bestätigung)
python format_string_linter.py datei.py --auto-fix
```

## Erkannte Probleme

### 1. Dictionary-Formatierung mit ungenutzten Argumenten

**❌ Fehlerhaft:**
```python
"Error %(message)s" % {"message": "something failed", "extra": "some dead code"}
```

**✅ Korrekt:**
```python
"Error %(message)s" % {"message": "something failed"}
```

### 2. .format() mit ungleicher Anzahl von Platzhaltern und Argumenten

**❌ Fehlerhaft:**
```python
"Error: User {} has not been able to access {}".format("Alice", "MyFile", "ExtraArgument")
```

**✅ Korrekt:**
```python
"Error: User {} has not been able to access {}".format("Alice", "MyFile")
```

### 3. f-strings mit eckigen statt geschweiften Klammern

**❌ Fehlerhaft:**
```python
user = "Alice"
resource = "MyFile"
message = f"Error: User [user] has not been able to access [resource]"
```

**✅ Korrekt:**
```python
user = "Alice"
resource = "MyFile"
message = f"Error: User {user} has not been able to access {resource}"
```

### 4. Logging mit fehlenden Argumenten

**❌ Fehlerhaft:**
```python
import logging
logging.error("Error: User %s has not been able to access %s", "Alice")
```

**✅ Korrekt:**
```python
import logging
logging.error("Error: User %s has not been able to access %s", "Alice", "MyFile")
```

### 5. % String-Formatierung mit falscher Anzahl Argumente

**❌ Fehlerhaft:**
```python
"Debug: %s %s %s" % ("info1", "info2")  # 3 Spezifizierer, aber nur 2 Argumente
```

**✅ Korrekt:**
```python
"Debug: %s %s %s" % ("info1", "info2", "info3")
# oder
"Debug: %s %s" % ("info1", "info2")
```

## Funktionen des Linters

### Automatische Erkennung

Der Linter verwendet sowohl AST-basierte Analyse als auch Regex-Muster, um eine umfassende Erkennung zu gewährleisten:

- **AST-Analyse**: Erkennt strukturelle Probleme in `.format()` Aufrufen, Logging-Statements und % Formatierung
- **Regex-Analyse**: Findet spezifische Muster wie f-strings mit eckigen Klammern

### Automatische Korrektur

Der Linter kann bestimmte Probleme automatisch beheben:

- ✅ **f-strings mit eckigen Klammern**: Ersetzt `[variable]` durch `{variable}`
- ⚠️ **Andere Probleme**: Erfordern manuelle Korrektur mit Lösungsvorschlägen

### Berichterstattung

Der Linter erstellt detaillierte Berichte:

```
📁 example_file.py
   Zeile 10: Dictionary-Format hat 1 Spezifizierer, aber 2 Keys
      Problem: percent_dict_mismatch
      Code: "Error %(message)s" % {"message": "failed", "extra": "unused"}
      Lösung: Prüfen Sie die Dictionary-Keys und Format-Spezifizierer
```

## Integration in Entwicklungsworkflow

### 1. Als Pre-Commit Hook

Erstellen Sie eine `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: format-string-linter
        name: Format String Linter
        entry: python format_string_linter.py
        language: system
        files: \\.py$
        args: [--auto-fix]
```

### 2. CI/CD Integration

Fügen Sie in Ihre CI/CD Pipeline ein:

```bash
# In GitHub Actions, GitLab CI, etc.
python format_string_linter.py src/ tests/
if [ $? -ne 0 ]; then
    echo "Format-String-Probleme gefunden!"
    exit 1
fi
```

### 3. IDE Integration

Für Visual Studio Code können Sie eine Task erstellen:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Format String Linter",
            "type": "shell",
            "command": "python",
            "args": ["format_string_linter.py", "${workspaceFolder}"],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        }
    ]
}
```

## Konfiguration und Erweiterung

### Anpassung der Erkennungsmuster

Sie können die Regex-Muster in der `_analyze_regex` Methode anpassen:

```python
# Beispiel: Zusätzliche f-string Muster
additional_patterns = [
    r'f["\'][^"\']*\[[a-zA-Z_][a-zA-Z0-9_]*\][^"\']*["\']',
    # Ihre eigenen Muster hier
]
```

### Erweiterung um neue Problemtypen

Neue Problemtypen können durch Erweiterung der `FormatVisitor` Klasse hinzugefügt werden:

```python
def visit_NewNodeType(self, node):
    # Ihre Logik hier
    self.generic_visit(node)
```

## Best Practices zur Vermeidung von Format-String-Problemen

### 1. Verwenden Sie f-strings für einfache Fälle

```python
# Gut
name = "Alice"
message = f"Hello {name}!"

# Weniger gut
message = "Hello {}!".format(name)
```

### 2. Verwenden Sie named placeholders für komplexe Formatierung

```python
# Gut
template = "Hello {name}, you have {count} messages"
result = template.format(name="Alice", count=5)

# Weniger gut
template = "Hello {}, you have {} messages"
result = template.format("Alice", 5)
```

### 3. Bei Logging: Verwenden Sie f-strings oder lazy evaluation

```python
# Gut (f-string)
logging.info(f"Processing user {user_id} with status {status}")

# Gut (lazy evaluation)
logging.info("Processing user %s with status %s", user_id, status)

# Schlecht
logging.info("Processing user %s with status %s" % (user_id, status))
```

### 4. Vermeiden Sie % String-Formatierung in neuem Code

```python
# Alt (vermeiden)
message = "Hello %s, you have %d messages" % (name, count)

# Modern (bevorzugt)
message = f"Hello {name}, you have {count} messages"
```

## Fehlerbehebung

### Häufige Probleme

1. **"AST parse error"**: Die Datei enthält Syntaxfehler
   - Lösung: Beheben Sie zuerst die Syntaxfehler

2. **"Encoding error"**: Die Datei verwendet ein unbekanntes Encoding
   - Lösung: Stellen Sie sicher, dass die Datei UTF-8 kodiert ist

3. **"Permission denied"**: Keine Schreibrechte für automatische Korrekturen
   - Lösung: Führen Sie den Linter mit entsprechenden Rechten aus

### Debug-Modi

Für detailliertere Ausgaben können Sie Logging aktivieren:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Beispiel-Session

```bash
$ python format_string_linter.py example_problems.py
❌ 6 Format-String-Problem(e) gefunden:

📁 example_problems.py
   Zeile 10: Dictionary-Format hat 1 Spezifizierer, aber 2 Keys
      Problem: percent_dict_mismatch
      Code: "Error %(message)s" % {"message": "failed", "extra": "unused"}
      Lösung: Prüfen Sie die Dictionary-Keys und Format-Spezifizierer

$ python format_string_linter.py example_problems.py --auto-fix
✅ Behoben: Zeile 18 in example_problems.py
✅ 1 Problem(e) behoben!
```

## Fazit

Der Format-String-Linter hilft dabei, häufige printf-style Format-String-Probleme zu erkennen und zu beheben, bevor sie zu Laufzeitfehlern führen. Durch Integration in den Entwicklungsworkflow können solche Probleme proaktiv vermieden werden.

---

**Hinweis**: Dieses Werkzeug ist ein Hilfsmittel zur Code-Qualitätssicherung. Manuelle Code-Reviews und Tests bleiben wichtig für die Gewährleistung der Korrektheit.