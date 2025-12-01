"""Shared rate limiter for collectors to prevent independent rate limit issues."""

import threading
from typing import Dict, Optional
from ratelimit import limits, sleep_and_retry


class SharedRateLimiter:
    """
    Thread-safe shared rate limiter per collector type.
    
    All instances of the same collector class share the same rate limit,
    preventing independent rate limiting that could cause issues when
    multiple jobs use the same collector simultaneously.
    """
    
    _limiters: Dict[str, 'SharedRateLimiter'] = {}
    _lock = threading.Lock()
    
    def __init__(self, collector_class_name: str, calls: int = 10, period: int = 60):
        """
        Initialize a shared rate limiter.
        
        Args:
            collector_class_name: Name of the collector class (e.g., 'StockCollector')
            calls: Number of calls allowed per period
            period: Period in seconds
        """
        self.collector_class_name = collector_class_name
        self.calls = calls
        self.period = period
        self._call_lock = threading.Lock()
        self._call_times = []
    
    @classmethod
    def get_limiter(
        cls,
        collector_class_name: str,
        calls: int = 10,
        period: int = 60
    ) -> 'SharedRateLimiter':
        """
        Get or create a shared rate limiter for a collector class.
        
        Args:
            collector_class_name: Name of the collector class
            calls: Number of calls allowed per period
            period: Period in seconds
            
        Returns:
            SharedRateLimiter instance for the collector class
        """
        with cls._lock:
            if collector_class_name not in cls._limiters:
                cls._limiters[collector_class_name] = SharedRateLimiter(
                    collector_class_name, calls, period
                )
            return cls._limiters[collector_class_name]
    
    def __call__(self, func):
        """
        Decorator to apply rate limiting to a function.
        
        Args:
            func: Function to wrap with rate limiting
            
        Returns:
            Wrapped function with rate limiting
        """
        @sleep_and_retry
        @limits(calls=self.calls, period=self.period)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    def update_limits(self, calls: int, period: int):
        """
        Update rate limit parameters.
        
        Args:
            calls: New number of calls allowed per period
            period: New period in seconds
        """
        with self._call_lock:
            self.calls = calls
            self.period = period

