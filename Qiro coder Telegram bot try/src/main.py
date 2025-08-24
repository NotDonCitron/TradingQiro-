# feat(main): FastAPI application with health checks and bot orchestration
from __future__ import annotations
import asyncio
import os
import signal
import socket
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import uvicorn
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env Datei
load_dotenv()

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.state_manager import StateManager
from src.core.task_executor import TaskExecutor
from src.core.reconciliation import ReconciliationJob
from src.core.cryptet_automation import CryptetAutomation
from src.core.signal_forwarder import SignalForwarder
from src.connectors.telethon_connector import TelethonConnector
from src.connectors.bingx_client import BingXClient
from src.utils.audit_logger import AuditLogger
from src.utils.metrics import MetricsCollector

# Global application state
app_state = {
    "state_manager": None,
    "task_executor": None,
    "reconciliation_job": None,
    "telethon_connector": None,
    "cryptet_automation": None,
    "signal_forwarder": None,
    "bingx_client": None,
    "audit_logger": None,
    "metrics": None,
    "healthy": False,
    "ready": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    await startup()
    
    # Setup signal handlers for graceful shutdown
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, lambda s, f: asyncio.create_task(shutdown()))
    
    try:
        yield
    finally:
        # Shutdown
        await shutdown()

app = FastAPI(
    title="Trading Bot",
    description="Asynchronous Signal Trading Bot (Telegram -> BingX)",
    version="1.0.0",
    lifespan=lifespan
)

async def startup():
    """Initialize all application components."""
    try:
        # Initialize logging
        app_state["audit_logger"] = AuditLogger(log_level=os.getenv("LOG_LEVEL", "INFO"))
        await app_state["audit_logger"].log("app_startup_begin", {})
        
        # Initialize metrics
        app_state["metrics"] = MetricsCollector()
        
        # Initialize database
        app_state["state_manager"] = StateManager()
        await app_state["state_manager"].init_models()
        
        # Initialize BingX client
        app_state["bingx_client"] = BingXClient()
        
        # Initialize task executor
        app_state["task_executor"] = TaskExecutor(
            state_manager=app_state["state_manager"],
            bingx_client=app_state["bingx_client"],
            audit_logger=app_state["audit_logger"],
            metrics=app_state["metrics"]
        )
        
        # Initialize reconciliation job
        app_state["reconciliation_job"] = ReconciliationJob(
            state_manager=app_state["state_manager"],
            bingx_client=app_state["bingx_client"],
            audit_logger=app_state["audit_logger"],
            metrics=app_state["metrics"]
        )
        
        # Initialize Telegram connector
        try:
            app_state["telethon_connector"] = TelethonConnector()
            app_state["telethon_connector"].register_message_handler(handle_telegram_message)
            await app_state["telethon_connector"].start()
            
            # Initialize Cryptet automation with Telegram callback
            app_state["cryptet_automation"] = CryptetAutomation(send_telegram_message)
            cryptet_enabled = os.getenv("CRYPTET_ENABLED", "true").lower() == "true"
            
            # Initialize Signal Forwarder
            app_state["signal_forwarder"] = SignalForwarder(send_telegram_message, app_state["audit_logger"])
            await app_state["audit_logger"].log("signal_forwarder_initialized", {})
            
            if cryptet_enabled:
                cryptet_success = await app_state["cryptet_automation"].initialize()
                if cryptet_success:
                    await app_state["audit_logger"].log("cryptet_automation_started", {})
                else:
                    await app_state["audit_logger"].log("cryptet_automation_failed", {})
            else:
                await app_state["audit_logger"].log("cryptet_automation_disabled", {})
                
        except Exception as e:
            await app_state["audit_logger"].log("telegram_init_failed", {"error": str(e)})
            # Continue without Telegram if it fails (for testing)
        
        # Start reconciliation job
        asyncio.create_task(app_state["reconciliation_job"].start())
        
        # Set application metrics
        trading_enabled = os.getenv("TRADING_ENABLED", "false").lower() == "true"
        app_state["metrics"].set_gauge("app_info", 1, {
            "version": "1.0.0",
            "trading_enabled": str(trading_enabled)
        })
        
        app_state["healthy"] = True
        app_state["ready"] = True
        
        await app_state["audit_logger"].log("app_started", {
            "version": "1.0.0",
            "trading_enabled": trading_enabled,
            "database_url": bool(os.getenv("DATABASE_URL")),
            "telegram_configured": bool(app_state["telethon_connector"])
        })
        
    except Exception as e:
        await app_state["audit_logger"].log("app_startup_failed", {"error": str(e)})
        app_state["healthy"] = False
        app_state["ready"] = False
        raise

async def shutdown():
    """Gracefully shutdown all components."""
    try:
        await app_state["audit_logger"].log("app_shutdown_begin", {})
        
        app_state["ready"] = False
        
        # Stop reconciliation job
        if app_state["reconciliation_job"]:
            await app_state["reconciliation_job"].stop()
        
        # Stop Cryptet automation
        if app_state["cryptet_automation"]:
            await app_state["cryptet_automation"].shutdown()
        
        # Stop Telegram connector
        if app_state["telethon_connector"]:
            await app_state["telethon_connector"].stop()
        
        # Close BingX client
        if app_state["bingx_client"]:
            await app_state["bingx_client"].aclose()
        
        app_state["healthy"] = False
        
        await app_state["audit_logger"].log("app_stopped", {})
        
    except Exception as e:
        if app_state["audit_logger"]:
            await app_state["audit_logger"].log("app_shutdown_error", {"error": str(e)})

async def handle_telegram_message(message: str, metadata: Dict[str, Any]) -> None:
    """Handle incoming Telegram messages."""
    try:
        app_state["metrics"].increment_counter("signals_received_total")
        await app_state["audit_logger"].log("signal_received", {"message": message, "metadata": metadata})
        
        chat_id = metadata.get("chat_id")
        
        # Check if it's a signal from -1002299206473 (VIP Club) that should be forwarded
        signal_forwarded = False
        if app_state["signal_forwarder"] and chat_id == -1002299206473:
            signal_forwarded = await app_state["signal_forwarder"].process_message(message, metadata)
        
        # Only apply Cryptet automation for messages from @cryptet_com channel (-1001804143400)
        cryptet_processed = False
        if app_state["cryptet_automation"] and chat_id == -1001804143400:
            cryptet_processed = await app_state["cryptet_automation"].process_telegram_message(message, metadata)
        
        # If not processed as Cryptet signal and not forwarded, process as normal signal
        if not cryptet_processed and not signal_forwarded:
            # Process signal with timing
            with app_state["metrics"].time_function("signal_processing_duration"):
                order_id = await app_state["task_executor"].process_signal(message, metadata)
                
            if order_id:
                await app_state["audit_logger"].log("signal_processed_successfully", {
                    "order_id": order_id,
                    "message": message
                })
        
    except Exception as e:
        await app_state["audit_logger"].log("signal_processing_error", {
            "message": message,
            "metadata": metadata,
            "error": str(e)
        })
        app_state["metrics"].increment_counter("signals_processing_errors_total")

async def send_telegram_message(chat_id: str, message: str) -> None:
    """Send message to Telegram chat via Telethon connector."""
    try:
        if app_state["telethon_connector"] and app_state["telethon_connector"].client:
            # Send message using Telethon client
            await app_state["telethon_connector"].client.send_message(int(chat_id), message)
            await app_state["audit_logger"].log("telegram_message_sent", {
                "chat_id": chat_id,
                "message_length": len(message)
            })
        else:
            await app_state["audit_logger"].log("telegram_send_failed", {
                "error": "Telethon connector not available",
                "chat_id": chat_id
            })
    except Exception as e:
        await app_state["audit_logger"].log("telegram_send_error", {
            "error": str(e),
            "chat_id": chat_id
        })

@app.get("/health")
async def health_check():
    """Liveness probe endpoint."""
    if app_state["healthy"]:
        await app_state["audit_logger"].log("health_check", {"status": "healthy"})
        return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
    else:
        await app_state["audit_logger"].log("health_check", {"status": "unhealthy"})
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/ready")
async def readiness_check():
    """Readiness probe endpoint."""
    if app_state["ready"]:
        return {"status": "ready", "timestamp": "2024-01-01T00:00:00Z"}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return app_state["metrics"].get_metrics()

@app.get("/status")
async def status():
    """Detailed status endpoint for debugging."""
    return {
        "healthy": app_state["healthy"],
        "ready": app_state["ready"],
        "components": {
            "state_manager": bool(app_state["state_manager"]),
            "task_executor": bool(app_state["task_executor"]),
            "reconciliation_job": bool(app_state["reconciliation_job"]),
            "telethon_connector": bool(app_state["telethon_connector"]),
            "cryptet_automation": bool(app_state["cryptet_automation"]),
            "signal_forwarder": bool(app_state["signal_forwarder"]),
            "bingx_client": bool(app_state["bingx_client"]),
            "audit_logger": bool(app_state["audit_logger"]),
            "metrics": bool(app_state["metrics"])
        },
        "config": {
            "trading_enabled": os.getenv("TRADING_ENABLED", "false"),
            "cryptet_enabled": os.getenv("CRYPTET_ENABLED", "true"),
            "bingx_testnet": os.getenv("BINGX_TESTNET", "true"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "own_group_chat_id": bool(os.getenv("OWN_GROUP_CHAT_ID"))
        }
    }

@app.post("/signal")
async def manual_signal(signal_data: Dict[str, Any]):
    """Manual signal submission endpoint for testing."""
    if not app_state["task_executor"]:
        raise HTTPException(status_code=503, detail="Task executor not available")
    
    message = signal_data.get("message", "")
    metadata = signal_data.get("metadata", {"source": "manual", "chat_id": 0, "message_id": 0})
    
    order_id = await app_state["task_executor"].process_signal(message, metadata)
    
    if order_id:
        return {"status": "success", "order_id": order_id}
    else:
        return {"status": "failed", "reason": "Signal processing failed"}

@app.get("/forwarder/status")
async def forwarder_status():
    """Get Signal Forwarder status."""
    if not app_state["signal_forwarder"]:
        raise HTTPException(status_code=503, detail="Signal forwarder not available")
    
    status = app_state["signal_forwarder"].get_status()
    
    return {
        "status": status,
        "monitored_chat": -2299206473,
        "target_group": status.get("target_group_id")
    }

@app.get("/cryptet/status")
async def cryptet_status():
    """Get Cryptet automation status."""
    if not app_state["cryptet_automation"]:
        raise HTTPException(status_code=503, detail="Cryptet automation not available")
    
    status = app_state["cryptet_automation"].get_status()
    active_signals = app_state["cryptet_automation"].get_active_signals()
    
    return {
        "status": status,
        "active_signals": active_signals,
        "active_count": len(active_signals)
    }

@app.post("/cryptet/test")
async def test_cryptet_link(data: Dict[str, Any]):
    """Test a Cryptet link for debugging."""
    if not app_state["cryptet_automation"]:
        raise HTTPException(status_code=503, detail="Cryptet automation not available")
    
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL required")
    
    result = await app_state["cryptet_automation"].test_cryptet_link(url)
    
    if result:
        return {"status": "success", "signal_data": result}
    else:
        return {"status": "failed", "reason": "Could not extract signal data"}

@app.post("/cryptet/close/{signal_id}")
async def close_cryptet_signal(signal_id: str, data: Optional[Dict[str, Any]] = None):
    """Manually close a Cryptet signal."""
    if not app_state["cryptet_automation"]:
        raise HTTPException(status_code=503, detail="Cryptet automation not available")
    
    reason = data.get("reason", "manual") if data else "manual"
    
    success = await app_state["cryptet_automation"].manual_close_signal(signal_id, reason)
    
    if success:
        return {"status": "success", "message": f"Signal {signal_id} closed"}
    else:
        return {"status": "failed", "reason": "Signal not found or already closed"}

def find_free_port(start_port: int = 8080, max_attempts: int = 10) -> int:
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free port found in range {start_port}-{start_port + max_attempts - 1}")

if __name__ == "__main__":
    # Find a free port
    default_port = int(os.getenv("PORT", "8080"))
    try:
        free_port = find_free_port(default_port)
        if free_port != default_port:
            print(f"⚠️  Port {default_port} ist besetzt. Verwende stattdessen Port {free_port}")
        else:
            print(f"✅ Verwende Port {free_port}")
        
        print(f"🌐 Server läuft auf: http://localhost:{free_port}")
        print(f"📊 Metriken verfügbar unter: http://localhost:{free_port}/metrics")
        print(f"🔍 Status-Seite: http://localhost:{free_port}/status")
        print(f"❤️  Health-Check: http://localhost:{free_port}/health")
        
        # Run with uvicorn
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=free_port,
            reload=False,
            access_log=True
        )
    except RuntimeError as e:
        print(f"❌ Fehler: {e}")
        print("💡 Versuche es mit einem anderen Port über die PORT Umgebungsvariable.")
        exit(1)