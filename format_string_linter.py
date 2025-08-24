#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Format-String-Linter: Automatische Erkennung und Korrektur von printf-style Format-String-Problemen

Erkennt und behebt häufige Probleme wie:
- Ungleiche Anzahl von Format-Spezifizierern und Argumenten
- Unbenutzte Argumente in Dictionary-Formatierung
- Fehlende geschweifte Klammern in f-strings
- Inkorrekte Logging-Format-Strings
"""

import ast
import re
import os
import sys
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class FormatIssue:
    """Repräsentiert ein Format-String-Problem"""
    file_path: str
    line_number: int
    column: int
    issue_type: str
    message: str
    original_code: str
    suggested_fix: str

class FormatStringLinter:
    """Linter für printf-style Format-String-Probleme"""
    
    def __init__(self):
        self.issues: List[FormatIssue] = []
        
    def check_directory(self, directory: str) -> List[FormatIssue]:
        """Überprüfe alle Python-Dateien in einem Verzeichnis"""
        self.issues = []
        
        for root, dirs, files in os.walk(directory):
            # Ignoriere __pycache__ und .git Verzeichnisse
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.pytest_cache']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.check_file(file_path)
        
        return self.issues
    
    def check_file(self, file_path: str) -> List[FormatIssue]:
        """Überprüfe eine einzelne Python-Datei"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # AST-basierte Analyse
            tree = ast.parse(content, filename=file_path)
            self._analyze_ast(tree, file_path, lines)
            
            # Regex-basierte Analyse für komplexere Muster
            self._analyze_regex(content, file_path, lines)
            
        except Exception as e:
            print(f"Fehler beim Analysieren von {file_path}: {e}")
        
        return self.issues
    
    def _analyze_ast(self, tree: ast.AST, file_path: str, lines: List[str]):
        """AST-basierte Analyse für Format-String-Probleme"""
        
        class FormatVisitor(ast.NodeVisitor):
            def __init__(self, linter):
                self.linter = linter
                self.file_path = file_path
                self.lines = lines
            
            def visit_Call(self, node):
                # Prüfe .format() Aufrufe
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr == 'format' and
                    isinstance(node.func.value, ast.Constant) and
                    isinstance(node.func.value.value, str)):
                    
                    format_string = node.func.value.value
                    args = node.args
                    kwargs = node.keywords
                    
                    self._check_format_call(node, format_string, args, kwargs)
                
                # Prüfe logging Aufrufe
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr in ['debug', 'info', 'warning', 'error', 'critical']):
                    
                    if node.args and isinstance(node.args[0], ast.Constant):
                        format_string = node.args[0].value
                        format_args = node.args[1:]
                        self._check_logging_call(node, format_string, format_args)
                
                self.generic_visit(node)
            
            def visit_BinOp(self, node):
                # Prüfe % String-Formatierung
                if (isinstance(node.op, ast.Mod) and
                    isinstance(node.left, ast.Constant) and
                    isinstance(node.left.value, str)):
                    
                    format_string = node.left.value
                    format_args = node.right
                    
                    self._check_percent_formatting(node, format_string, format_args)
                
                self.generic_visit(node)
            
            def _check_format_call(self, node, format_string: str, args, kwargs):
                """Prüfe .format() Aufrufe auf Probleme"""
                # Zähle Platzhalter
                placeholder_count = len(re.findall(r'\{[^}]*\}', format_string))
                arg_count = len(args) + len(kwargs)
                
                if placeholder_count != arg_count:
                    line_num = node.lineno
                    original_line = self.lines[line_num - 1] if line_num <= len(self.lines) else ""
                    
                    issue = FormatIssue(
                        file_path=self.file_path,
                        line_number=line_num,
                        column=node.col_offset,
                        issue_type="format_mismatch",
                        message=f"Format-String hat {placeholder_count} Platzhalter, aber {arg_count} Argumente",
                        original_code=original_line.strip(),
                        suggested_fix=self._suggest_format_fix(format_string, args, kwargs)
                    )
                    self.linter.issues.append(issue)
            
            def _check_logging_call(self, node, format_string: str, format_args):
                """Prüfe Logging-Aufrufe auf Format-Probleme"""
                if '%' in format_string:
                    # Zähle % Spezifizierer
                    specifiers = re.findall(r'%[sdifcr%]', format_string)
                    # Entferne %% (escaped %)
                    specifiers = [s for s in specifiers if s != '%%']
                    
                    if len(specifiers) != len(format_args):
                        line_num = node.lineno
                        original_line = self.lines[line_num - 1] if line_num <= len(self.lines) else ""
                        
                        issue = FormatIssue(
                            file_path=self.file_path,
                            line_number=line_num,
                            column=node.col_offset,
                            issue_type="logging_format_mismatch",
                            message=f"Logging-Format hat {len(specifiers)} Spezifizierer, aber {len(format_args)} Argumente",
                            original_code=original_line.strip(),
                            suggested_fix=self._suggest_logging_fix(format_string, format_args)
                        )
                        self.linter.issues.append(issue)
            
            def _check_percent_formatting(self, node, format_string: str, format_args):
                """Prüfe % String-Formatierung auf Probleme"""
                # Zähle % Spezifizierer
                specifiers = re.findall(r'%\([^)]+\)[sdifcr%]|%[sdifcr%]', format_string)
                # Entferne %% (escaped %)
                specifiers = [s for s in specifiers if s != '%%']
                
                # Bestimme erwartete Anzahl Argumente
                if isinstance(format_args, ast.Dict):
                    # Dictionary-Formatierung
                    dict_keys = len(format_args.keys)
                    named_specifiers = [s for s in specifiers if s.startswith('%(')]
                    
                    if len(named_specifiers) != dict_keys:
                        line_num = node.lineno
                        original_line = self.lines[line_num - 1] if line_num <= len(self.lines) else ""
                        
                        issue = FormatIssue(
                            file_path=self.file_path,
                            line_number=line_num,
                            column=node.col_offset,
                            issue_type="percent_dict_mismatch",
                            message=f"Dictionary-Format hat {len(named_specifiers)} Spezifizierer, aber {dict_keys} Keys",
                            original_code=original_line.strip(),
                            suggested_fix="Prüfen Sie die Dictionary-Keys und Format-Spezifizierer"
                        )
                        self.linter.issues.append(issue)
                
                elif isinstance(format_args, (ast.Tuple, ast.List)):
                    # Tupel/Liste-Formatierung
                    arg_count = len(format_args.elts)
                    positional_specifiers = [s for s in specifiers if not s.startswith('%(')]
                    
                    if len(positional_specifiers) != arg_count:
                        line_num = node.lineno
                        original_line = self.lines[line_num - 1] if line_num <= len(self.lines) else ""
                        
                        issue = FormatIssue(
                            file_path=self.file_path,
                            line_number=line_num,
                            column=node.col_offset,
                            issue_type="percent_tuple_mismatch",
                            message=f"Tupel-Format hat {len(positional_specifiers)} Spezifizierer, aber {arg_count} Argumente",
                            original_code=original_line.strip(),
                            suggested_fix="Entfernen Sie überflüssige Argumente oder fügen Sie fehlende Spezifizierer hinzu"
                        )
                        self.linter.issues.append(issue)
            
            def _suggest_format_fix(self, format_string: str, args, kwargs) -> str:
                """Schlage Korrektur für .format() Probleme vor"""
                placeholder_count = len(re.findall(r'\{[^}]*\}', format_string))
                arg_count = len(args) + len(kwargs)
                
                if placeholder_count > arg_count:
                    return f"Fügen Sie {placeholder_count - arg_count} fehlende Argumente hinzu"
                else:
                    return f"Entfernen Sie {arg_count - placeholder_count} überflüssige Argumente"
            
            def _suggest_logging_fix(self, format_string: str, format_args) -> str:
                """Schlage Korrektur für Logging-Probleme vor"""
                specifiers = re.findall(r'%[sdifcr%]', format_string)
                specifiers = [s for s in specifiers if s != '%%']
                
                if len(specifiers) > len(format_args):
                    return f"Fügen Sie {len(specifiers) - len(format_args)} fehlende Argumente hinzu"
                else:
                    return f"Entfernen Sie {len(format_args) - len(specifiers)} überflüssige Argumente"
        
        visitor = FormatVisitor(self)
        visitor.visit(tree)
    
    def _analyze_regex(self, content: str, file_path: str, lines: List[str]):
        """Regex-basierte Analyse für komplexere Muster"""
        
        # Prüfe f-strings mit eckigen statt geschweiften Klammern
        fstring_square_bracket_pattern = r'f["\'][^"\']*\[[a-zA-Z_][a-zA-Z0-9_]*\][^"\']*["\']'
        
        for match in re.finditer(fstring_square_bracket_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            original_line = lines[line_num - 1] if line_num <= len(lines) else ""
            
            # Aber ignoriere String-Slicing-Operationen
            matched_text = match.group()
            if not re.search(r'\[\d+:\d*\]|\[\d*:\d+\]|\[:\d+\]|\[\d+:\]', matched_text):
                issue = FormatIssue(
                    file_path=file_path,
                    line_number=line_num,
                    column=match.start(),
                    issue_type="fstring_square_brackets",
                    message="f-string verwendet eckige statt geschweifte Klammern für Variablen",
                    original_code=original_line.strip(),
                    suggested_fix="Ersetzen Sie eckige Klammern [] durch geschweifte Klammern {} in f-strings"
                )
                self.issues.append(issue)
    
    def print_report(self):
        """Drucke einen formatierten Bericht der gefundenen Probleme"""
        if not self.issues:
            print("✅ Keine Format-String-Probleme gefunden!")
            return
        
        print(f"❌ {len(self.issues)} Format-String-Problem(e) gefunden:\n")
        
        # Gruppiere nach Dateien
        issues_by_file = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)
        
        for file_path, file_issues in issues_by_file.items():
            print(f"📁 {file_path}")
            for issue in file_issues:
                print(f"   Zeile {issue.line_number}: {issue.message}")
                print(f"      Problem: {issue.issue_type}")
                print(f"      Code: {issue.original_code}")
                print(f"      Lösung: {issue.suggested_fix}")
                print()
    
    def fix_issues(self, auto_fix: bool = False) -> int:
        """Behebe gefundene Probleme (optional automatisch)"""
        if not self.issues:
            return 0
        
        fixes_applied = 0
        
        # Gruppiere nach Dateien
        issues_by_file = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)
        
        for file_path, file_issues in issues_by_file.items():
            if not auto_fix:
                print(f"\n📁 Möchten Sie Probleme in {file_path} beheben? (y/n): ", end="")
                response = input().strip().lower()
                if response != 'y':
                    continue
            
            # Sortiere nach Zeilennummer (rückwärts für sichere Änderungen)
            file_issues.sort(key=lambda x: x.line_number, reverse=True)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for issue in file_issues:
                    if issue.issue_type == "fstring_square_brackets":
                        # Automatische Korrektur für f-string eckige Klammern
                        line_idx = issue.line_number - 1
                        if line_idx < len(lines):
                            original_line = lines[line_idx]
                            # Ersetze [variable] durch {variable} in f-strings
                            fixed_line = re.sub(
                                r'(f["\'][^"\']*)\[([a-zA-Z_][a-zA-Z0-9_]*)\]([^"\']*["\'])',
                                r'\1{\2}\3',
                                original_line
                            )
                            if fixed_line != original_line:
                                lines[line_idx] = fixed_line
                                fixes_applied += 1
                                print(f"✅ Behoben: Zeile {issue.line_number} in {file_path}")
                
                # Schreibe die korrigierte Datei zurück
                if fixes_applied > 0:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                
            except Exception as e:
                print(f"❌ Fehler beim Beheben von {file_path}: {e}")
        
        return fixes_applied

def main():
    """Hauptfunktion für Kommandozeilen-Nutzung"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Format-String-Linter für Python-Code')
    parser.add_argument('path', help='Pfad zur zu prüfenden Datei oder Verzeichnis')
    parser.add_argument('--fix', action='store_true', help='Versuche Probleme automatisch zu beheben')
    parser.add_argument('--auto-fix', action='store_true', help='Behebe Probleme automatisch ohne Nachfrage')
    
    args = parser.parse_args()
    
    linter = FormatStringLinter()
    
    if os.path.isfile(args.path):
        linter.check_file(args.path)
    elif os.path.isdir(args.path):
        linter.check_directory(args.path)
    else:
        print(f"❌ Pfad nicht gefunden: {args.path}")
        sys.exit(1)
    
    linter.print_report()
    
    if args.fix or args.auto_fix:
        fixes_applied = linter.fix_issues(auto_fix=args.auto_fix)
        print(f"\n✅ {fixes_applied} Problem(e) behoben!")

if __name__ == "__main__":
    main()