#!/usr/bin/env python3
"""
Final Test - Kein automatisches "unlimited" Target
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.signal_forwarder import SignalForwarder
from src.utils.audit_logger import AuditLogger

async def mock_send_telegram(chat_id: str, message: str):
    """Mock send function."""
    print(f"📤 FINALES SIGNAL (ohne unlimited):")
    print("-" * 50)
    print(message)
    print("-" * 50)
    print()

async def test_no_unlimited():
    """Test dass unlimited nicht automatisch hinzugefügt wird."""
    
    print("🧪 FINAL TEST - KEIN AUTOMATISCHES UNLIMITED")
    print("=" * 60)
    
    # Test cases verschiedene Szenarien
    test_cases = [
        {
            "name": "Signal mit 2 Targets",
            "signal": """🟢 Long
Name: BTC/USDT
Margin mode: Cross (10.0X)

↪️ Entry price(USDT):
50000

Targets(USDT):
1) 51000
2) 52000""",
            "expected_targets": 2
        },
        {
            "name": "Signal mit 4 Targets",
            "signal": """🟢 Long
Name: ETH/USDT
Margin mode: Cross (20.0X)

↪️ Entry price(USDT):
2500

Targets(USDT):
1) 2600
2) 2700
3) 2800
4) 2900""",
            "expected_targets": 4
        },
        {
            "name": "Original Signal mit unlimited (wird gefiltert)",
            "signal": """🟢 Long
Name: API3/USDT
Margin mode: Cross (25.0X)

↪️ Entry price(USDT):
1.4619

Targets(USDT):
1) 1.4765
2) 1.4911
3) 1.5058
4) 1.5204
5) 🔝 unlimited""",
            "expected_targets": 4  # unlimited wird herausgefiltert
        }
    ]
    
    audit_logger = AuditLogger()
    signal_forwarder = SignalForwarder(mock_send_telegram, audit_logger)
    
    test_metadata = {
        "chat_id": -2299206473,
        "message_id": 12345
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📊 TEST {i}: {test_case['name']}")
        print("=" * 40)
        
        print("📥 Input Signal:")
        print(test_case['signal'])
        print()
        
        # Parse das Signal um zu überprüfen wie viele Targets erkannt werden
        signal_data = signal_forwarder._parse_signal(test_case['signal'])
        
        if signal_data:
            targets_count = len(signal_data['targets'])
            print(f"🎯 Erkannte Targets: {targets_count}")
            print(f"✅ Erwartet: {test_case['expected_targets']}")
            
            if targets_count == test_case['expected_targets']:
                print("✅ Target-Anzahl korrekt!")
            else:
                print("❌ Target-Anzahl inkorrekt!")
            print()
            
            # Formatiertes Signal anzeigen
            result = await signal_forwarder.process_message(test_case['signal'], test_metadata)
            print(f"✅ Verarbeitung erfolgreich: {result}")
        else:
            print("❌ Signal-Parsing fehlgeschlagen")
        
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_no_unlimited())