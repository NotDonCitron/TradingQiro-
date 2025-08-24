#!/usr/bin/env python3
"""
24/7 Health Monitor für Trading Bot
Überwacht den Bot-Status und startet ihn bei Problemen neu
"""

import requests
import time
import subprocess
import sys
from datetime import datetime
import logging

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/health-monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self):
        self.bot_url = "http://localhost:8080"
        self.check_interval = 30  # Sekunden
        self.restart_threshold = 3  # Fehlgeschlagene Checks vor Restart
        self.failed_checks = 0
        
    def check_health(self):
        """Prüft den Health Status des Bots"""
        try:
            # Health Check
            response = requests.get(f"{self.bot_url}/health", timeout=10)
            if response.status_code == 200:
                self.failed_checks = 0
                return True
            else:
                logger.warning(f"Health Check failed: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Health Check error: {e}")
            return False
    
    def restart_bot(self):
        """Startet den Bot Container neu"""
        try:
            logger.info("🔄 Restarting trading bot container...")
            
            # Restart Docker Container
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.production.yml", "restart"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Bot successfully restarted")
                self.failed_checks = 0
                return True
            else:
                logger.error(f"❌ Restart failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Restart error: {e}")
            return False
    
    def get_bot_status(self):
        """Holt erweiterte Bot-Status-Informationen"""
        try:
            response = requests.get(f"{self.bot_url}/status", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    def run_monitor(self):
        """Hauptüberwachungsschleife"""
        logger.info("🎯 Starting 24/7 Health Monitor for Trading Bot")
        logger.info(f"⏱️  Check interval: {self.check_interval} seconds")
        logger.info(f"🔄 Restart threshold: {self.restart_threshold} failed checks")
        
        while True:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if self.check_health():
                    # Erfolgreicher Health Check
                    status = self.get_bot_status()
                    if status:
                        logger.info(f"✅ [{timestamp}] Bot healthy - Components: {len([k for k, v in status.get('components', {}).items() if v])}")
                    else:
                        logger.info(f"✅ [{timestamp}] Bot healthy")
                else:
                    # Fehlgeschlagener Health Check
                    self.failed_checks += 1
                    logger.warning(f"⚠️  [{timestamp}] Health check failed ({self.failed_checks}/{self.restart_threshold})")
                    
                    if self.failed_checks >= self.restart_threshold:
                        logger.error(f"❌ [{timestamp}] Too many failed checks - initiating restart")
                        
                        if self.restart_bot():
                            # Nach Restart 60 Sekunden warten
                            logger.info("⏳ Waiting 60 seconds after restart...")
                            time.sleep(60)
                        else:
                            logger.error("❌ Restart failed - waiting before retry...")
                            time.sleep(120)  # 2 Minuten bei Restart-Fehler
                
                # Warte bis zum nächsten Check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(60)  # Bei Fehler 1 Minute warten

if __name__ == "__main__":
    monitor = HealthMonitor()
    monitor.run_monitor()