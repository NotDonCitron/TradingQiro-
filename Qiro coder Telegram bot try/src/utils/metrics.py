# Simple working metrics collector
from typing import Dict, Any, Optional

class MetricsCollector:
    """Simple metrics collector that works without conflicts."""
    
    def __init__(self):
        self.counters = {}
        self.gauges = {}
    
    def increment_counter(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        key = f"{metric_name}_{labels}" if labels else metric_name
        self.counters[key] = self.counters.get(key, 0) + 1
    
    def observe_histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a value for a histogram metric."""
        # For now, just track the latest value
        key = f"{metric_name}_{labels}" if labels else metric_name
        self.gauges[key] = value
    
    def set_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        key = f"{metric_name}_{labels}" if labels else metric_name
        self.gauges[key] = value
    
    def time_function(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager to time function execution."""
        return self._TimingContext(self, metric_name, labels)
    
    def get_metrics(self) -> str:
        """Get metrics in simple format."""
        lines = ["# Simple metrics output"]
        
        for name, value in self.counters.items():
            lines.append(f"# COUNTER {name} {value}")
        
        for name, value in self.gauges.items():
            lines.append(f"# GAUGE {name} {value}")
        
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