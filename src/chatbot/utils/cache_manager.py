
from functools import lru_cache, wraps
from typing import Callable, Any

def memory_cache(maxsize: int = 128):
    """
    Decorator for in-memory LRU caching.
    """
    def decorator(func: Callable) -> Callable:
        @lru_cache(maxsize=maxsize)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

class GlobalCache:
    """
    Simple singleton for application-wide shared state if needed.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalCache, cls).__new__(cls)
            cls._instance.data = {}
        return cls._instance

    def set(self, key: str, value: Any):
        self.data[key] = value

    def get(self, key: str) -> Any:
        return self.data.get(key)
