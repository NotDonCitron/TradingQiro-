# Professional Trading Bot Metrics for Prometheus
from typing import Dict, Any, Optional
import time
from collections import defaultdict, deque

class MetricsCollector:
    """Professional metrics collector for Trading Bot monitoring."""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = {}
        self.histograms = defaultdict(lambda: deque(maxlen=1000))  # Keep last 1000 values
        self.start_time = time.time()
        
        # Trading-specific metrics
        self._init_trading_metrics()
    
    def _init_trading_metrics(self):
        """Initialize trading-specific metrics."""
        # Signal processing metrics
        self.set_gauge('signals_processed_total', 0)
        self.set_gauge('signal_processing_errors_total', 0)
        self.set_gauge('cryptet_scraping_errors_total', 0)
        self.set_gauge('telegram_message_errors_total', 0)
        self.set_gauge('trading_errors_total', 0)
        
        # System health metrics  
        self.set_gauge('telegram_connection_status', 1)  # 1=connected, 0=disconnected
        self.set_gauge('cryptet_last_signal_timestamp', time.time())
        self.set_gauge('system_uptime_seconds', 0)
        
        # Performance metrics
        self.set_gauge('signal_processing_duration_seconds', 0)
        self.set_gauge('active_trading_sessions', 0)
        
    def increment_counter(self, metric_name: str, labels: Optional[Dict[str, str]] = None, value: float = 1) -> None:
        """Increment a counter metric."""
        key = self._make_key(metric_name, labels)
        self.counters[key] += value
        
    def _make_key(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create consistent metric key."""
        if labels:
            label_str = ','.join(f'{k}="{v}"' for k, v in sorted(labels.items()))
            return f"{metric_name}{{{label_str}}}"
        return metric_name
    
    def observe_histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a value for a histogram metric."""
        key = self._make_key(metric_name, labels)
        self.histograms[key].append(value)
        # Also update as gauge for current value
        self.set_gauge(metric_name, value, labels)
    
    def set_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        key = self._make_key(metric_name, labels)
        self.gauges[key] = value
        
    def update_system_uptime(self) -> None:
        """Update system uptime metric."""
        uptime = time.time() - self.start_time
        self.set_gauge('system_uptime_seconds', uptime)
    
    def time_function(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager to time function execution."""
        return self._TimingContext(self, metric_name, labels)
    
    # Trading-specific metric helpers
    def record_signal_processed(self, signal_type: str = "unknown", success: bool = True) -> None:
        """Record signal processing event."""
        labels = {'type': signal_type, 'status': 'success' if success else 'error'}
        self.increment_counter('signals_processed_total', labels)
        
        if not success:
            self.increment_counter('signal_processing_errors_total')
    
    def record_trading_operation(self, operation: str, success: bool = True, exchange: str = "bingx") -> None:
        """Record trading operation."""
        labels = {'operation': operation, 'exchange': exchange, 'status': 'success' if success else 'error'}
        self.increment_counter('trading_operations_total', labels)
        
        if not success:
            self.increment_counter('trading_errors_total')
    
    def record_telegram_event(self, event_type: str, success: bool = True) -> None:
        """Record Telegram-related events."""
        labels = {'type': event_type, 'status': 'success' if success else 'error'}
        self.increment_counter('telegram_events_total', labels)
        
        if not success:
            self.increment_counter('telegram_message_errors_total')
    
    def record_cryptet_scraping(self, success: bool = True, signal_found: bool = False) -> None:
        """Record Cryptet scraping events."""
        labels = {'status': 'success' if success else 'error'}
        self.increment_counter('cryptet_scraping_total', labels)
        
        if not success:
            self.increment_counter('cryptet_scraping_errors_total')
        
        if signal_found:
            self.set_gauge('cryptet_last_signal_timestamp', time.time())
    
    def set_connection_status(self, service: str, connected: bool) -> None:
        """Update connection status for external services."""
        status = 1 if connected else 0
        self.set_gauge(f'{service}_connection_status', status)
    
    def record_performance_metric(self, operation: str, duration_seconds: float) -> None:
        """Record performance timing."""
        self.observe_histogram(f'{operation}_duration_seconds', duration_seconds)
        
        # Update specific gauge for monitoring
        if operation == 'signal_processing':
            self.set_gauge('signal_processing_duration_seconds', duration_seconds)
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        lines = []
        
        # Add help text for main metrics
        lines.extend([
            "# HELP signals_processed_total Total number of signals processed",
            "# TYPE signals_processed_total counter",
            "# HELP signal_processing_duration_seconds Time spent processing signals", 
            "# TYPE signal_processing_duration_seconds gauge",
            "# HELP system_uptime_seconds System uptime in seconds",
            "# TYPE system_uptime_seconds gauge",
            "# HELP telegram_connection_status Telegram connection status (1=connected, 0=disconnected)",
            "# TYPE telegram_connection_status gauge",
            "# HELP trading_errors_total Total number of trading errors",
            "# TYPE trading_errors_total counter",
            ""
        ])
        
        # Update uptime before export
        self.update_system_uptime()
        
        # Export counters
        for name, value in self.counters.items():
            lines.append(f"{name} {value}")
        
        # Export gauges
        for name, value in self.gauges.items():
            lines.append(f"{name} {value}")
        
        # Export histogram summaries (percentiles)
        for name, values in self.histograms.items():
            if values:
                sorted_values = sorted(values)
                count = len(sorted_values)
                
                # Calculate percentiles
                p50_idx = int(count * 0.50)
                p95_idx = int(count * 0.95)
                p99_idx = int(count * 0.99)
                
                lines.extend([
                    f"{name}_count {count}",
                    f"{name}_sum {sum(sorted_values)}",
                    f"{name}{{quantile=\"0.50\"}} {sorted_values[p50_idx] if p50_idx < count else 0}",
                    f"{name}{{quantile=\"0.95\"}} {sorted_values[p95_idx] if p95_idx < count else 0}",
                    f"{name}{{quantile=\"0.99\"}} {sorted_values[p99_idx] if p99_idx < count else 0}",
                ])
        
        return "\n".join(lines) + "\n"
    
    class _TimingContext:
        """Context manager for timing operations."""
        
        def __init__(self, metrics: 'MetricsCollector', metric_name: str, labels: Optional[Dict[str, str]]):
            self.metrics = metrics
            self.metric_name = metric_name
            self.labels = labels
            self.start_time = 0
        
        def __enter__(self):
            import time
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            import time
            duration = time.time() - self.start_time
            self.metrics.observe_histogram(self.metric_name, duration, self.labels)