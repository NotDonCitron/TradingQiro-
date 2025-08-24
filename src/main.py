# feat(main): FastAPI application with health checks and bot orchestration
from __future__ import annotations
import asyncio
import os
import signal
import socket
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
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

        # Run pre-startup diagnostics if enabled
        if os.getenv("ENABLE_STARTUP_DIAGNOSTICS", "true").lower() == "true":
            print("🔍 Running pre-startup diagnostics...")
            try:
                from src.utils.console_diagnostics import ConsoleDiagnosticEngine
                diagnostic_engine = ConsoleDiagnosticEngine()
                diagnostic_results = await diagnostic_engine.run_full_diagnosis()

                # Check for critical issues
                critical_issues = [r for r in diagnostic_results if r.status == "critical"]
                if critical_issues:
                    print("🚨 Critical issues detected during startup!")
                    for issue in critical_issues:
                        print(f"  • {issue.message}")
                    print("❌ Aborting startup due to critical issues")
                    raise RuntimeError("Critical issues detected during startup diagnostics")

                # Log diagnostic results
                await app_state["audit_logger"].log("startup_diagnostics_completed", {
                    "total_checks": len(diagnostic_results),
                    "critical_issues": len(critical_issues),
                    "warnings": len([r for r in diagnostic_results if r.status == "warning"])
                })

            except ImportError:
                print("⚠️  Diagnostic system not available, continuing without pre-startup checks")
            except Exception as e:
                print(f"⚠️  Diagnostic check failed: {str(e)}, continuing with startup")

        print("✅ Pre-startup diagnostics completed")
        
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
            
            if cryptet_enabled:
                cryptet_success = await app_state["cryptet_automation"].initialize()
            else:
                pass
                
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
        chat_id = metadata.get("chat_id")
        
        # Chat ID Normalisierung - sowohl positive als auch negative IDs unterstützen
        normalized_chat_id = None
        if chat_id:
            if chat_id == 2299206473 or chat_id == -1002299206473:
                normalized_chat_id = -1002299206473  # VIP Group
            elif chat_id == 1804143400 or chat_id == -1001804143400:
                normalized_chat_id = -1001804143400  # Cryptet Channel
        
        # Check if it's a signal from -1002299206473 (VIP Club) that should be forwarded
        signal_forwarded = False
        if app_state["signal_forwarder"] and normalized_chat_id == -1002299206473:
            # Erstelle normalisierte Metadaten für den Signal Forwarder
            normalized_metadata = metadata.copy()
            normalized_metadata["chat_id"] = normalized_chat_id
            signal_forwarded = await app_state["signal_forwarder"].process_message(message, normalized_metadata)
        
        # Only apply Cryptet automation for messages from @cryptet_com channel (-1001804143400)
        cryptet_processed = False
        if app_state["cryptet_automation"] and normalized_chat_id == -1001804143400:
            normalized_metadata = metadata.copy()
            normalized_metadata["chat_id"] = normalized_chat_id
            cryptet_processed = await app_state["cryptet_automation"].process_telegram_message(message, normalized_metadata)
        
        # If not processed as Cryptet signal and not forwarded, process as normal signal
        if not cryptet_processed and not signal_forwarded:
            # Process signal 
            order_id = await app_state["task_executor"].process_signal(message, metadata)
    
    except Exception:
        pass

async def send_telegram_message(chat_id: str, message: str) -> None:
    """Send message to Telegram chat via Telethon connector."""
    try:
        if app_state["telethon_connector"] and app_state["telethon_connector"].client:
            # Send message using Telethon client
            await app_state["telethon_connector"].client.send_message(int(chat_id), message)
    except Exception:
        pass

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    if app_state["metrics"]:
        # Update system metrics before export
        app_state["metrics"].update_system_uptime()
        app_state["metrics"].set_gauge("app_healthy", 1 if app_state["healthy"] else 0)
        app_state["metrics"].set_gauge("app_ready", 1 if app_state["ready"] else 0)
        
        return app_state["metrics"].get_metrics()
    return "# No metrics available\n"

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
    
    # Verwende dieselbe Logik wie handle_telegram_message
    try:
        await handle_telegram_message(message, metadata)
        return {"status": "success", "message": "Signal processed via normal flow"}
    except Exception as e:
        return {"status": "failed", "reason": str(e)}

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

# Webhook endpoints for Alertmanager
@app.post("/webhook/alert")
async def webhook_alert(request: Request):
    """Generic webhook endpoint for Alertmanager alerts."""
    try:
        alert_data = await request.json()
        
        # Log alert for debugging
        if app_state["audit_logger"]:
            await app_state["audit_logger"].log("alertmanager_webhook", {
                "alerts_count": len(alert_data.get("alerts", [])),
                "status": alert_data.get("status", "unknown")
            })
        
        return {"status": "received"}
    except Exception as e:
        if app_state["audit_logger"]:
            await app_state["audit_logger"].log("webhook_error", {"error": str(e)})
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/webhook/critical-alert")
async def webhook_critical_alert(request: Request):
    """Webhook endpoint for critical alerts with Telegram notification."""
    try:
        alert_data = await request.json()
        
        # Format critical alert message
        alerts = alert_data.get("alerts", [])
        if alerts:
            for alert in alerts:
                alert_name = alert.get("labels", {}).get("alertname", "Unknown Alert")
                summary = alert.get("annotations", {}).get("summary", "No summary")
                description = alert.get("annotations", {}).get("description", "No description")
                
                message = f"🚨 **KRITISCHER ALERT**\n\n" \
                         f"**Alert:** {alert_name}\n" \
                         f"**Summary:** {summary}\n" \
                         f"**Beschreibung:** {description}\n" \
                         f"**Zeit:** {alert.get('startsAt', 'Unknown')}"
                
                # Send to Telegram if available
                if app_state["telethon_connector"]:
                    try:
                        await send_telegram_message(message)
                    except Exception as e:
                        print(f"Failed to send critical alert to Telegram: {e}")
        
        # Log critical alert
        if app_state["audit_logger"]:
            await app_state["audit_logger"].log("critical_alert_received", {
                "alerts_count": len(alerts),
                "alert_names": [a.get("labels", {}).get("alertname") for a in alerts]
            })
        
        return {"status": "critical_alert_processed"}
    except Exception as e:
        if app_state["audit_logger"]:
            await app_state["audit_logger"].log("critical_webhook_error", {"error": str(e)})
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/webhook/warning-alert")
async def webhook_warning_alert(request: Request):
    """Webhook endpoint for warning alerts."""
    try:
        alert_data = await request.json()
        
        # Log warning alert (don't spam Telegram with warnings)
        if app_state["audit_logger"]:
            alerts = alert_data.get("alerts", [])
            await app_state["audit_logger"].log("warning_alert_received", {
                "alerts_count": len(alerts),
                "alert_names": [a.get("labels", {}).get("alertname") for a in alerts]
            })
        
        return {"status": "warning_alert_logged"}
    except Exception as e:
        if app_state["audit_logger"]:
            await app_state["audit_logger"].log("warning_webhook_error", {"error": str(e)})
        raise HTTPException(status_code=400, detail=str(e))

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

@app.get("/diagnostics/run")
async def run_diagnostics():
    """Run console diagnostics and return results."""
    try:
        from src.utils.console_diagnostics import ConsoleDiagnosticEngine
        engine = ConsoleDiagnosticEngine()
        results = await engine.run_full_diagnosis()
        report = engine.generate_report()
        return report
    except ImportError:
        raise HTTPException(status_code=503, detail="Diagnostic system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic error: {str(e)}")

@app.post("/diagnostics/resolve")
async def resolve_issues():
    """Automatically resolve detected issues."""
    try:
        from src.utils.console_diagnostics import ConsoleDiagnosticEngine
        from src.utils.error_resolver import ErrorResolver

        # First run diagnostics
        diagnostic_engine = ConsoleDiagnosticEngine()
        diagnostic_results = await diagnostic_engine.run_full_diagnosis()

        # Then attempt resolutions
        resolver = ErrorResolver()
        resolution_results = await resolver.resolve_diagnostic_results(diagnostic_results)

        return {
            "diagnostics": diagnostic_engine.generate_report(),
            "resolutions": resolver.generate_resolution_report()
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Diagnostic or resolution system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resolution error: {str(e)}")

@app.get("/diagnostics/health")
async def diagnostics_health():
    """Check if diagnostic system is available and healthy."""
    try:
        from src.utils.console_diagnostics import ConsoleDiagnosticEngine
        from src.utils.error_resolver import ErrorResolver

        return {
            "diagnostic_system": True,
            "error_resolver": True,
            "status": "healthy"
        }
    except ImportError as e:
        return {
            "diagnostic_system": False,
            "error_resolver": False,
            "status": "unavailable",
            "error": f"Import error: {str(e)}"
        }
    except Exception as e:
        return {
            "diagnostic_system": False,
            "error_resolver": False,
            "status": "error",
            "error": str(e)
        }

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
