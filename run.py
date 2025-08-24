#!/usr/bin/env python3
"""
Startup script for Cryptet Trading Bot
Handles Python path setup and starts the FastAPI server
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main application
if __name__ == "__main__":
    try:
        import uvicorn
        from src.main import app
        
        # Configuration
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        reload = os.getenv("RELOAD", "false").lower() == "true"
        
        print(f"🚀 Starting Cryptet Trading Bot on {host}:{port}")
        print(f"📊 Web Dashboard: http://localhost:{port}/status")
        print(f"🤖 Cryptet Status: http://localhost:{port}/cryptet/status")
        print(f"❤️  Health Check: http://localhost:{port}/health")
        
        # Start the server
        uvicorn.run(
            "src.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)