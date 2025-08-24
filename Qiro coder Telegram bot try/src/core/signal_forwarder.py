#!/usr/bin/env python3
"""
Signal Forwarder für Telegram Gruppe -2299206473
Erkennt und leitet Signale in standardisiertem Format weiter
"""

import re
import os
from typing import Dict, Any, Optional, Callable, Awaitable
import asyncio
from src.utils.audit_logger import AuditLogger


class SignalForwarder:
    """Klasse für das Weiterleiten von Telegram-Signalen."""
    
    def __init__(self, send_telegram_callback: Callable[[str, str], Awaitable[None]], audit_logger: Optional[AuditLogger] = None):
        """
        Initialisiert den Signal Forwarder.
        
        Args:
            send_telegram_callback: Callback-Funktion zum Senden von Telegram-Nachrichten
            audit_logger: Logger für Audit-Zwecke
        """
        self.send_telegram_callback = send_telegram_callback
        self.audit_logger = audit_logger
        self.target_group_id = os.getenv("OWN_GROUP_CHAT_ID", "-1002773853382")
        
        # Pattern für Signal-Erkennung - Angepasst für das exakte Format
        self.signal_pattern = re.compile(
            r'🟢\s*(Long|Short)\s*\n'
            r'Name:\s*([A-Z0-9]+/[A-Z]+)\s*\n'
            r'Margin\s+mode:\s*Cross\s*\(([0-9.]+)X\)\s*\n'
            r'.*?'
            r'Entry\s+price\(USDT\):\s*\n'
            r'([0-9.]+)\s*\n'
            r'.*?'
            r'Targets\(USDT\):\s*\n'
            r'((?:\d+\)\s*[0-9.]+(?:\s*\n|\s+))+)',
            re.DOTALL | re.IGNORECASE
        )
    
    async def process_message(self, message: str, metadata: Dict[str, Any]) -> bool:
        """
        Verarbeitet eine Telegram-Nachricht und prüft, ob es ein Signal ist.
        
        Args:
            message: Die Telegram-Nachricht
            metadata: Metadaten der Nachricht (chat_id, etc.)
            
        Returns:
            bool: True wenn Nachricht als Signal verarbeitet wurde, False sonst
        """
        chat_id = metadata.get("chat_id")
        
        # Nur Nachrichten aus der überwachten Gruppe -2299206473 verarbeiten
        if chat_id != -2299206473:
            return False
        
        # Prüfen ob es ein Signal ist
        if not self._is_signal(message):
            if self.audit_logger:
                await self.audit_logger.log("signal_forwarder_no_signal", {
                    "chat_id": chat_id,
                    "message_preview": message[:100]
                })
            return False
        
        try:
            # Signal parsen
            signal_data = self._parse_signal(message)
            
            if signal_data:
                # Signal formatieren
                formatted_signal = self._format_signal(signal_data)
                
                # An eigene Gruppe weiterleiten
                await self.send_telegram_callback(self.target_group_id, formatted_signal)
                
                if self.audit_logger:
                    await self.audit_logger.log("signal_forwarded", {
                        "source_chat_id": chat_id,
                        "target_chat_id": self.target_group_id,
                        "symbol": signal_data.get("symbol"),
                        "direction": signal_data.get("direction")
                    })
                
                return True
            else:
                if self.audit_logger:
                    await self.audit_logger.log("signal_forwarder_parse_failed", {
                        "chat_id": chat_id,
                        "message": message
                    })
                return False
                
        except Exception as e:
            if self.audit_logger:
                await self.audit_logger.log("signal_forwarder_error", {
                    "chat_id": chat_id,
                    "error": str(e),
                    "message_preview": message[:200]
                })
            return False
    
    def _is_signal(self, message: str) -> bool:
        """
        Prüft ob eine Nachricht ein Signal enthält.
        
        Args:
            message: Die zu prüfende Nachricht
            
        Returns:
            bool: True wenn Signal erkannt wurde
        """
        # Grundlegende Checks für Signal-Format
        signal_indicators = [
            "🟢 Long" in message or "🟢 Short" in message,
            "Name:" in message,
            "Margin mode:" in message,
            "Entry price(USDT):" in message,
            "Targets(USDT):" in message
        ]
        
        return all(signal_indicators)
    
    def _parse_signal(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parst ein Signal aus der Nachricht mit robustem Line-by-Line Parsing.
        
        Args:
            message: Die Signal-Nachricht
            
        Returns:
            Dict mit Signal-Daten oder None
        """
        lines = message.split('\n')
        
        direction = None
        symbol = None
        leverage = None
        entry_price = None
        targets = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Parse Direction
            if '🟢 Long' in line:
                direction = 'LONG'
            elif '🟢 Short' in line or '🔴 Short' in line:
                direction = 'SHORT'
            
            # Parse Symbol
            elif line.startswith('Name:'):
                symbol_match = re.search(r'Name:\s*([A-Z0-9]+/[A-Z]+)', line)
                if symbol_match:
                    symbol = symbol_match.group(1)
            
            # Parse Leverage
            elif 'Margin mode:' in line and 'Cross' in line:
                leverage_match = re.search(r'\(([0-9.]+)X\)', line)
                if leverage_match:
                    leverage = float(leverage_match.group(1))
            
            # Parse Entry Price
            elif 'Entry price(USDT):' in line:
                # Next line should contain the price
                if i + 1 < len(lines):
                    price_line = lines[i + 1].strip()
                    try:
                        entry_price = float(price_line)
                    except ValueError:
                        pass
            
            # Parse Targets
            elif 'Targets(USDT):' in line:
                # Parse subsequent target lines
                j = i + 1
                while j < len(lines):
                    target_line = lines[j].strip()
                    target_match = re.search(r'\d+\)\s*([0-9.]+)', target_line)
                    if target_match:
                        target_price = float(target_match.group(1))
                        targets.append(target_price)
                    elif '🔝 unlimited' in target_line:
                        # End of targets
                        break
                    elif target_line == '' or not target_match:
                        # Empty line or no more targets
                        break
                    j += 1
            
            i += 1
        
        # Validate that we have all required fields
        if all([direction, symbol, leverage, entry_price]):
            return {
                "symbol": symbol,
                "direction": direction,
                "leverage": leverage,
                "entry_price": entry_price,
                "targets": targets,
                "source": "telegram_group",
                "source_chat_id": -2299206473
            }
        
        return None
    
    def _format_signal(self, signal_data: Dict[str, Any]) -> str:
        """
        Formatiert Signal-Daten zu einer Cornix-kompatiblen Telegram-Nachricht.
        
        Args:
            signal_data: Die Signal-Daten
            
        Returns:
            Cornix-kompatible formatierte Nachricht
        """
        symbol = signal_data["symbol"]
        direction = signal_data["direction"]
        leverage = signal_data["leverage"]
        entry_price = signal_data["entry_price"]
        targets = signal_data["targets"]
        
        # Helper function to format numbers cleanly
        def format_price(price):
            if isinstance(price, float) and price.is_integer():
                return str(int(price))
            return str(price)
        
        # Cornix-kompatibles Format - exakt wie das Original
        direction_emoji = "🟢" if direction == "LONG" else "🔴"
        direction_text = "Long" if direction == "LONG" else "Short"
        
        message = f"{direction_emoji} {direction_text}\n"
        message += f"Name: {symbol}\n"
        message += f"Margin mode: Cross ({format_price(leverage)}X)\n\n"
        
        message += "↪️ Entry price(USDT):\n"
        message += f"{format_price(entry_price)}\n\n"
        
        message += "Targets(USDT):\n"
        for i, target in enumerate(targets, 1):
            message += f"{i}) {format_price(target)}\n"
        
        # Kein automatisches "unlimited" hinzufügen - nur echte Targets weiterleiten
        
        return message
    
    def get_status(self) -> Dict[str, Any]:
        """
        Gibt den aktuellen Status des Forwarders zurück.
        
        Returns:
            Status-Informationen
        """
        return {
            "enabled": True,
            "target_group_id": self.target_group_id,
            "monitored_chat_id": -2299206473,
            "pattern_configured": bool(self.signal_pattern)
        }