#!/usr/bin/env python3
"""
Test für verschiedene Target-Szenarien zur Cornix-Kompatibilität
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
    print(f"📤 FORMATTED SIGNAL:")
    print("-" * 50)
    print(message)
    print("-" * 50)
    print()

async def test_different_target_counts():
    """Test signals with different target counts."""
    
    print("🧪 CORNIX FORMAT COMPATIBILITY TEST")
    print("=" * 60)
    
    # Test cases mit verschiedenen Target-Anzahlen
    test_cases = [
        {
            "name": "2 Targets",
            "signal": """🟢 Long
Name: BTC/USDT
Margin mode: Cross (10.0X)

↪️ Entry price(USDT):
50000

Targets(USDT):
1) 51000
2) 52000"""
        },
        {
            "name": "3 Targets", 
            "signal": """🟢 Long
Name: ETH/USDT
Margin mode: Cross (15.0X)

↪️ Entry price(USDT):
3000

Targets(USDT):
1) 3100
2) 3200
3) 3300"""
        },
        {
            "name": "4 Targets (Original API3)",
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
5) 🔝 unlimited"""
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
        print("=" * 30)
        
        print("📥 Input Signal:")
        print(test_case['signal'])
        print()
        
        result = await signal_forwarder.process_message(test_case['signal'], test_metadata)
        print(f"✅ Process result: {result}")
        print()

if __name__ == "__main__":
    asyncio.run(test_different_target_counts())