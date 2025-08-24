#!/usr/bin/env python3
"""
Port Usage Finder - Findet Prozesse die bestimmte Ports verwenden
Hilfreich um Port-Konflikte zu lösen
"""

import subprocess
import sys
import argparse
from typing import List, Dict, Any

def find_processes_using_port(port: int) -> List[Dict[str, Any]]:
    """Findet alle Prozesse die einen bestimmten Port verwenden."""
    processes = []
    
    try:
        if sys.platform == "win32":
            # Windows: netstat verwenden
            result = subprocess.run(
                ["netstat", "-ano"], 
                capture_output=True, 
                text=True, 
                encoding='cp1252'  # Windows Codepage für Deutschland
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            address = parts[1]
                            
                            # Versuche Prozessname zu finden
                            try:
                                tasklist_result = subprocess.run(
                                    ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"],
                                    capture_output=True,
                                    text=True,
                                    encoding='cp1252'
                                )
                                
                                if tasklist_result.returncode == 0:
                                    lines = tasklist_result.stdout.strip().split('\n')
                                    if len(lines) > 1:
                                        # Parse CSV output
                                        process_line = lines[1].replace('"', '').split(',')
                                        process_name = process_line[0] if process_line else "Unknown"
                                    else:
                                        process_name = "Unknown"
                                else:
                                    process_name = "Unknown"
                                    
                            except Exception:
                                process_name = "Unknown"
                            
                            processes.append({
                                "pid": pid,
                                "name": process_name,
                                "address": address,
                                "port": port
                            })
        else:
            # Linux/macOS: lsof verwenden
            result = subprocess.run(
                ["lsof", "-i", f":{port}"], 
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
        print(f"Fehler beim Suchen nach Prozessen: {e}")
    
    return processes

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
        print(f"Fehler beim Beenden des Prozesses {pid}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Findet und beendet Prozesse die bestimmte Ports verwenden")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port zu überprüfen (Standard: 8080)")
    parser.add_argument("--kill", "-k", action="store_true", help="Gefundene Prozesse beenden")
    parser.add_argument("--force", "-f", action="store_true", help="Erzwinge das Beenden (nur mit --kill)")
    
    args = parser.parse_args()
    
    print(f"🔍 Suche nach Prozessen die Port {args.port} verwenden...")
    
    processes = find_processes_using_port(args.port)
    
    if not processes:
        print(f"✅ Keine Prozesse gefunden die Port {args.port} verwenden")
        return
    
    print(f"\n📋 Gefundene Prozesse für Port {args.port}:")
    print("-" * 60)
    print(f"{'PID':<8} {'Name':<20} {'Adresse':<25}")
    print("-" * 60)
    
    for proc in processes:
        print(f"{proc['pid']:<8} {proc['name']:<20} {proc['address']:<25}")
    
    if args.kill:
        print(f"\n⚠️  Beende {len(processes)} Prozess(e)...")
        
        for proc in processes:
            print(f"Beende Prozess {proc['pid']} ({proc['name']})...")
            success = kill_process(proc['pid'], args.force)
            
            if success:
                print(f"✅ Prozess {proc['pid']} erfolgreich beendet")
            else:
                print(f"❌ Fehler beim Beenden von Prozess {proc['pid']}")
                if not args.force:
                    print("💡 Versuche es mit --force für erzwungenes Beenden")
    else:
        print(f"\n💡 Verwende --kill um die Prozesse zu beenden")
        print(f"💡 Verwende --force --kill für erzwungenes Beenden")

if __name__ == "__main__":
    main()