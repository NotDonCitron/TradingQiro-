#!/usr/bin/env python3
"""
Port Usage Finder - Findet Prozesse die bestimmte Ports verwenden
Hilfreich um Port-Konflikte zu lösen
"""

import subprocess
import sys
import argparse
from typing import List, Dict, Any

def get_process_name_windows(pid: str) -> str:
    """Ermittelt Prozessname unter Windows."""
    try:
        tasklist_result = subprocess.run(
            ["tasklist", "/FI", "PID eq {}".format(pid), "/FO", "CSV"],
            capture_output=True,
            text=True,
            encoding='cp1252'
        )
        
        if tasklist_result.returncode == 0:
            lines = tasklist_result.stdout.strip().split('\n')
            if len(lines) > 1:
                # Parse CSV output
                process_line = lines[1].replace('"', '').split(',')
                return process_line[0] if process_line else "Unknown"
        
        return "Unknown"
    except Exception:
        return "Unknown"

def find_processes_windows(port: int) -> List[Dict[str, Any]]:
    """Findet Prozesse unter Windows die einen Port verwenden."""
    processes = []
    
    try:
        result = subprocess.run(
            ["netstat", "-ano"], 
            capture_output=True, 
            text=True, 
            encoding='cp1252'  # Windows Codepage für Deutschland
        )
        
        if result.returncode != 0:
            return processes
            
        lines = result.stdout.split('\n')
        for line in lines:
            if ":{}".format(port) in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    address = parts[1]
                    process_name = get_process_name_windows(pid)
                    
                    processes.append({
                        "pid": pid,
                        "name": process_name,
                        "address": address,
                        "port": port
                    })
    except Exception as e:
        print("Fehler beim Suchen nach Prozessen: {}".format(e))
    
    return processes

def find_processes_unix(port: int) -> List[Dict[str, Any]]:
    """Findet Prozesse unter Linux/macOS die einen Port verwenden."""
    processes = []
    
    try:
        result = subprocess.run(
            ["lsof", "-i", ":{}".format(port)], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        processes.append({
                            "pid": parts[1],
                            "name": parts[0],
                            "address": parts[8] if len(parts) > 8 else "Unknown",
                            "port": port
                        })
    except Exception as e:
        print("Fehler beim Suchen nach Prozessen: {}".format(e))
                            
    return processes

def find_processes_using_port(port: int) -> List[Dict[str, Any]]:
    """Findet alle Prozesse die einen bestimmten Port verwenden."""
    if sys.platform == "win32":
        return find_processes_windows(port)
    else:
        return find_processes_unix(port)

def kill_process(pid: str, force: bool = False) -> bool:
    """Beendet einen Prozess mit der gegebenen PID."""
    try:
        if sys.platform == "win32":
            cmd = ["taskkill", "/PID", pid]
            if force:
                cmd.append("/F")
        else:
            signal_type = "-9" if force else "-15"
            cmd = ["kill", signal_type, pid]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
        
    except Exception as e:
        print("Fehler beim Beenden des Prozesses {}: {}".format(pid, e))
        return False

def print_process_table(processes: List[Dict[str, Any]]):
    """Druckt Tabelle mit gefundenen Prozessen."""
    print("-" * 60)
    print("{:<8} {:<20} {:<25}".format('PID', 'Name', 'Adresse'))
    print("-" * 60)
    
    for proc in processes:
        print("{:<8} {:<20} {:<25}".format(proc['pid'], proc['name'], proc['address']))

def kill_processes(processes: List[Dict[str, Any]], force: bool):
    """Beendet eine Liste von Prozessen."""
    print("\n⚠️  Beende {} Prozess(e)...".format(len(processes)))
    
    for proc in processes:
        print("Beende Prozess {} ({})...".format(proc['pid'], proc['name']))
        success = kill_process(proc['pid'], force)
        
        if success:
            print("✅ Prozess {} erfolgreich beendet".format(proc['pid']))
        else:
            print("❌ Fehler beim Beenden von Prozess {}".format(proc['pid']))
            if not force:
                print("💡 Versuche es mit --force für erzwungenes Beenden")

def main():
    parser = argparse.ArgumentParser(description="Findet und beendet Prozesse die bestimmte Ports verwenden")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port zu überprüfen (Standard: 8080)")
    parser.add_argument("--kill", "-k", action="store_true", help="Gefundene Prozesse beenden")
    parser.add_argument("--force", "-f", action="store_true", help="Erzwinge das Beenden (nur mit --kill)")
    
    args = parser.parse_args()
    
    print("🔍 Suche nach Prozessen die Port {} verwenden...".format(args.port))
    
    processes = find_processes_using_port(args.port)
    
    if not processes:
        print("✅ Keine Prozesse gefunden die Port {} verwenden".format(args.port))
        return
    
    print("\n📋 Gefundene Prozesse für Port {}:".format(args.port))
    print_process_table(processes)
    
    if args.kill:
        kill_processes(processes, args.force)
    else:
        print("\n💡 Verwende --kill um die Prozesse zu beenden")
        print("💡 Verwende --force --kill für erzwungenes Beenden")

if __name__ == "__main__":
    main()