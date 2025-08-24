# feat(utils): structured audit logger for comprehensive operation tracking
from __future__ import annotations
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import os

class AuditLogger:
    """Structured logging for audit trail and monitoring."""
    
    def __init__(self, logger_name: str = "trading_bot_audit", log_level: str = "INFO"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Remove existing handlers to avoid duplication
        self.logger.handlers.clear()
        
        # Console handler with JSON formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(self._get_json_formatter())
        self.logger.addHandler(handler)
        
        # Optional file handler if LOG_FILE is set
        log_file = os.getenv("LOG_FILE")
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(self._get_json_formatter())
            self.logger.addHandler(file_handler)
    
    def _get_json_formatter(self) -> logging.Formatter:
        """Get JSON formatter for structured logging."""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                
                # Add extra fields if present
                if hasattr(record, 'extra_fields'):
                    log_entry.update(record.extra_fields)
                
                # Add exception info if present
                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)
                
                return json.dumps(log_entry, default=str)
        
        return JSONFormatter()
    
    async def log(self, event_type: str, data: Dict[str, Any], level: str = "INFO", console_output: bool = True) -> None:
        """Log an audit event with structured data."""
        log_data = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Add system context
        log_data["system_info"] = {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
            "working_directory": os.getcwd()
        }

        # Create log record with extra fields
        record = logging.LogRecord(
            name=self.logger.name,
            level=getattr(logging, level.upper(), logging.INFO),
            pathname="",
            lineno=0,
            msg=f"[{event_type}] {self._format_event_message(event_type, data)}",
            args=(),
            exc_info=None
        )
        # Add extra fields using setattr to avoid type checking issues
        setattr(record, 'extra_fields', log_data)

        self.logger.handle(record)

        # Also print to console for immediate visibility of important events
        if console_output and level in ["ERROR", "CRITICAL"]:
            status_emoji = {"ERROR": "❌", "CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "ℹ️"}
            emoji = status_emoji.get(level, "📝")
            print(f"{emoji} [{event_type}] {self._format_event_message(event_type, data)}")
    
    def _format_event_message(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format a human-readable message for the event."""
        messages = {
            "signal_received": f"Signal received from chat {data.get('chat_id', 'unknown')}",
            "signal_duplicate": f"Duplicate signal ignored: {data.get('signal_id', 'unknown')}",
            "signal_parse_failed": f"Failed to parse signal: {data.get('message', 'unknown')}",
            "order_created": f"Order {data.get('order_id', 'unknown')} created for {data.get('signal', {}).get('symbol', 'unknown')}",
            "order_submitted": f"Order {data.get('order_id', 'unknown')} submitted to exchange (ID: {data.get('broker_order_id', 'unknown')})",
            "order_submission_failed": f"Order {data.get('order_id', 'unknown')} submission failed: {data.get('error', 'unknown error')}",
            "order_execution_error": f"Order {data.get('order_id', 'unknown')} execution error: {data.get('error', 'unknown')}",
            "order_status_reconciled": f"Order {data.get('order_id', 'unknown')} status updated: {data.get('old_status', 'unknown')} -> {data.get('new_status', 'unknown')}",
            "position_updated": f"Position for {data.get('symbol', 'unknown')} updated: {data.get('old_size', 'unknown')} -> {data.get('new_size', 'unknown')}",
            "reconciliation_job_started": "Reconciliation job started",
            "reconciliation_job_stopped": "Reconciliation job stopped",
            "reconciliation_error": f"Reconciliation error: {data.get('error', 'unknown')}",
            "exchange_api_call": f"Exchange API call: {data.get('method', 'unknown')} {data.get('endpoint', 'unknown')}",
            "exchange_api_error": f"Exchange API error: {data.get('error', 'unknown')}",
            "circuit_breaker_opened": "Circuit breaker opened due to failures",
            "circuit_breaker_closed": "Circuit breaker closed after recovery",
            "app_started": f"Trading bot started (version: {data.get('version', 'unknown')}, trading: {data.get('trading_enabled', 'unknown')})",
            "app_startup_begin": "Trading bot startup initiated",
            "app_startup_failed": f"Trading bot startup failed: {data.get('error', 'unknown')}",
            "app_stopped": "Trading bot stopped",
            "health_check": f"Health check: {data.get('status', 'unknown')}",
        }
        
        return messages.get(event_type, f"Event: {event_type}")
    
    async def log_error(self, event_type: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error event with exception details."""
        data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        await self.log(event_type, data, level="ERROR")
    
    async def log_performance(self, operation: str, duration: float, context: Optional[Dict[str, Any]] = None) -> None:
        """Log performance metrics."""
        data = {
            "operation": operation,
            "duration_seconds": round(duration, 4),
            "context": context or {}
        }
        await self.log("performance_metric", data)
    
    async def log_api_call(self, method: str, endpoint: str, status_code: int, duration: float, 
                          request_data: Optional[Dict[str, Any]] = None, 
                          response_data: Optional[Dict[str, Any]] = None) -> None:
        """Log external API calls for debugging and monitoring."""
        data = {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_seconds": round(duration, 4),
            "request_data": request_data or {},
            "response_data": response_data or {}
        }
        
        level = "ERROR" if status_code >= 400 else "INFO"
        await self.log("exchange_api_call", data, level=level)
