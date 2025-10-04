import json
import logging
from datetime import datetime, timedelta
import re
from typing import Any, Dict, Optional
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for API requests"""
    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = []

    def is_allowed(self) -> bool:
        """Check if request is allowed under rate limit"""
        now = datetime.now()
        # Remove requests outside the current window
        self.requests = [req for req in self.requests if req > now - timedelta(seconds=self.window)]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

    def get_retry_after(self) -> float:
        """Get seconds until next allowed request"""
        if not self.requests:
            return 0
        
        now = datetime.now()
        oldest_request = min(self.requests)
        window_end = oldest_request + timedelta(seconds=self.window)
        return max(0, (window_end - now).total_seconds())

class CacheManager:
    """Simple in-memory cache manager"""
    def __init__(self, default_timeout: int = 300):  # 5 minutes default
        self.cache = {}
        self.default_timeout = default_timeout

    def set(self, key: str, value: Any, timeout: Optional[int] = None):
        """Set cache value with timeout"""
        timeout = timeout or self.default_timeout
        expires_at = datetime.now() + timedelta(seconds=timeout)
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at
        }

    def get(self, key: str) -> Optional[Any]:
        """Get cache value if not expired"""
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        if datetime.now() > item['expires_at']:
            del self.cache[key]
            return None
        
        return item['value']

    def clear(self, key: Optional[str] = None):
        """Clear cache - specific key or all"""
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()

    def cleanup_expired(self):
        """Clean up expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, item in self.cache.items()
            if now > item['expires_at']
        ]
        for key in expired_keys:
            del self.cache[key]

def serialize_datetime(obj: Any) -> Any:
    """Serialize datetime objects to ISO format strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def prepare_response(data: Any) -> Any:
    """Convert datetime objects to ISO format strings in response data"""
    if isinstance(data, dict):
        return {k: prepare_response(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [prepare_response(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

def validate_symbol(symbol: str) -> bool:
    """Validate stock symbol format"""
    if not symbol or not isinstance(symbol, str):
        return False
    # Basic validation - symbols are usually 2-6 uppercase letters
    return bool(re.match(r'^[A-Z]{2,6}$', symbol.upper()))

async def make_http_request(url: str, headers: Optional[Dict] = None, timeout: int = 10) -> Optional[str]:
    """Make HTTP request with error handling"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=timeout) as response:
                response.raise_for_status()
                return await response.text()
    except aiohttp.ClientError as e:
        logger.error(f"HTTP request failed for {url}: {e}")
        return None
    except asyncio.TimeoutError:
        logger.error(f"HTTP request timeout for {url}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during HTTP request: {e}")
        return None

def format_currency(value: float) -> str:
    """Format currency values"""
    try:
        return f"Rs. {value:,.2f}"
    except (ValueError, TypeError):
        return "Rs. 0.00"

def format_percentage(value: float) -> str:
    """Format percentage values"""
    try:
        return f"{value:+.2f}%"
    except (ValueError, TypeError):
        return "0.00%"

def calculate_performance(stocks: list) -> Dict[str, Any]:
    """Calculate market performance metrics"""
    if not stocks:
        return {
            'total_stocks': 0,
            'avg_change': 0.0,
            'max_gainer': None,
            'max_loser': None,
            'total_market_cap': 0.0
        }
    
    changes = [s.get('change_percent', 0) for s in stocks if s.get('change_percent') is not None]
    gainers = [s for s in stocks if s.get('change_percent', 0) > 0]
    losers = [s for s in stocks if s.get('change_percent', 0) < 0]
    
    max_gainer = max(stocks, key=lambda x: x.get('change_percent', 0)) if stocks else None
    max_loser = min(stocks, key=lambda x: x.get('change_percent', 0)) if stocks else None
    
    # Mock market cap calculation (close price * volume)
    total_market_cap = sum(s.get('close_price', 0) * s.get('volume', 0) for s in stocks)
    
    return {
        'total_stocks': len(stocks),
        'avg_change': sum(changes) / len(changes) if changes else 0.0,
        'gainers_count': len(gainers),
        'losers_count': len(losers),
        'max_gainer': max_gainer,
        'max_loser': max_loser,
        'total_market_cap': total_market_cap
    }

# Global instances
rate_limiter = RateLimiter(max_requests=15, window=60)  # 15 requests per minute
cache_manager = CacheManager(default_timeout=300)  # 5 minutes cache