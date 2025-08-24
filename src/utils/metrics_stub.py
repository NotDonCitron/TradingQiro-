# Simple metrics stub to bypass Prometheus issues temporarily

class MetricsStub:
    """Stub metrics collector that does nothing but doesn't fail."""
    
    def increment_counter(self, metric_name: str, labels=None):
        """Do nothing."""
        pass
    
    def observe_histogram(self, metric_name: str, value: float, labels=None):
        """Do nothing."""
        pass
    
    def set_gauge(self, metric_name: str, value: float, labels=None):
        """Do nothing."""
        pass
    
    def time_function(self, metric_name: str, labels=None):
        """Return a dummy context manager."""
        return self._DummyContext()
    
    def get_metrics(self) -> str:
        """Return empty metrics."""
        return "# Metrics disabled\n"
    
    class _DummyContext:
        """Dummy context manager that does nothing."""
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass