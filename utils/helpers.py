import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = []

    def is_allowed(self) -> bool:
        now = datetime.now()
        self.requests = [req for req in self.requests if req > now - timedelta(seconds=self.window)]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

class CacheManager:
    def __init__(self, default_timeout: int = 300):
        self.cache = {}
        self.default_timeout = default_timeout

    def set(self, key: str, value: Any, timeout: Optional[int] = None):
        timeout = timeout or self.default_timeout
        expires_at = datetime.now() + timedelta(seconds=timeout)
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at
        }

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        if datetime.now() > item['expires_at']:
            del self.cache[key]
            return None
        
        return item['value']

    def clear(self, key: Optional[str] = None):
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()

# Global instances
rate_limiter = RateLimiter(max_requests=15, window=60)
cache_manager = CacheManager(default_timeout=300)