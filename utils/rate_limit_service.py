"""
In-Memory Rate Limiting Service - Simple rate limiting without Redis
Handles rate limiting using in-memory storage with automatic cleanup
"""

import time
from typing import Dict, Tuple
from threading import Lock
from utils.env_utils import get_env_int
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Environment variables
RATE_LIMIT_WINDOW = get_env_int("RATE_LIMIT_WINDOW", 3600)

class InMemoryRateLimitService:
    """Simple in-memory rate limiting service"""
    
    def __init__(self):
        self._requests: Dict[str, list] = {}
        self._lock = Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
    
    def _cleanup_expired(self):
        """Remove expired entries to prevent memory leaks"""
        current_time = time.time()
        
        # Only cleanup every 5 minutes
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        with self._lock:
            expired_keys = []
            for key, timestamps in self._requests.items():
                # Remove timestamps older than the rate limit window
                cutoff_time = current_time - RATE_LIMIT_WINDOW
                self._requests[key] = [ts for ts in timestamps if ts > cutoff_time]
                
                # Mark empty entries for removal
                if not self._requests[key]:
                    expired_keys.append(key)
            
            # Remove empty entries
            for key in expired_keys:
                del self._requests[key]
            
            self._last_cleanup = current_time
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit entries")
    
    def is_rate_limited(self, identifier: str, limit: int, window: int) -> bool:
        """Check if identifier is rate limited"""
        try:
            current_time = time.time()
            cutoff_time = current_time - window
            
            # Cleanup expired entries periodically
            self._cleanup_expired()
            
            with self._lock:
                # Get existing requests for this identifier
                if identifier not in self._requests:
                    self._requests[identifier] = []
                
                # Remove old requests outside the window
                self._requests[identifier] = [
                    ts for ts in self._requests[identifier] 
                    if ts > cutoff_time
                ]
                
                # Check if limit exceeded
                if len(self._requests[identifier]) >= limit:
                    return True
                
                # Add current request
                self._requests[identifier].append(current_time)
                return False
                
        except Exception as e:
            logger.error(f"Rate limit check error for {identifier}: {e}")
            return False  # Fail open
    
    def get_rate_limit_info(self, identifier: str, window: int) -> Dict[str, int]:
        """Get rate limit information"""
        try:
            current_time = time.time()
            cutoff_time = current_time - window
            
            with self._lock:
                if identifier not in self._requests:
                    return {"current": 0, "remaining_time": 0}
                
                # Count valid requests
                valid_requests = [
                    ts for ts in self._requests[identifier] 
                    if ts > cutoff_time
                ]
                
                # Calculate remaining time until oldest request expires
                remaining_time = 0
                if valid_requests:
                    oldest_request = min(valid_requests)
                    remaining_time = max(0, int(window - (current_time - oldest_request)))
                
                return {
                    "current": len(valid_requests),
                    "remaining_time": remaining_time
                }
                
        except Exception as e:
            logger.error(f"Rate limit info error for {identifier}: {e}")
            return {"current": 0, "remaining_time": 0}
    
    def clear_rate_limit(self, identifier: str):
        """Clear rate limit for an identifier"""
        with self._lock:
            if identifier in self._requests:
                del self._requests[identifier]
    
    def get_stats(self) -> Dict[str, int]:
        """Get service statistics"""
        with self._lock:
            total_identifiers = len(self._requests)
            total_requests = sum(len(requests) for requests in self._requests.values())
            
            return {
                "total_identifiers": total_identifiers,
                "total_requests": total_requests,
                "last_cleanup": int(self._last_cleanup)
            }

class InMemoryCacheService:
    """Simple in-memory caching service"""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[any, float]] = {}  # key -> (value, expiry_time)
        self._lock = Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
    
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()
        
        # Only cleanup every 5 minutes
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        with self._lock:
            expired_keys = []
            for key, (value, expiry) in self._cache.items():
                if expiry > 0 and current_time > expiry:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            self._last_cleanup = current_time
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def set(self, key: str, value: any, expire: int = None) -> bool:
        """Set a value in cache with optional expiration"""
        try:
            current_time = time.time()
            expiry_time = current_time + expire if expire else 0
            
            # Cleanup expired entries periodically
            self._cleanup_expired()
            
            with self._lock:
                self._cache[key] = (value, expiry_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False
    
    def get(self, key: str, default: any = None) -> any:
        """Get a value from cache"""
        try:
            current_time = time.time()
            
            with self._lock:
                if key not in self._cache:
                    return default
                
                value, expiry = self._cache[key]
                
                # Check if expired
                if expiry > 0 and current_time > expiry:
                    del self._cache[key]
                    return default
                
                return value
                
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    return True
                return False
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            current_time = time.time()
            
            with self._lock:
                if key not in self._cache:
                    return False
                
                value, expiry = self._cache[key]
                
                # Check if expired
                if expiry > 0 and current_time > expiry:
                    del self._cache[key]
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Cache EXISTS error for key {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        try:
            with self._lock:
                current_value = 0
                if key in self._cache:
                    value, expiry = self._cache[key]
                    if isinstance(value, int):
                        current_value = value
                
                new_value = current_value + amount
                self._cache[key] = (new_value, 0)  # No expiry for counters
                return new_value
                
        except Exception as e:
            logger.error(f"Cache INCREMENT error for key {key}: {e}")
            return 0
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self._lock:
            total_keys = len(self._cache)
            expired_keys = 0
            current_time = time.time()
            
            for key, (value, expiry) in self._cache.items():
                if expiry > 0 and current_time > expiry:
                    expired_keys += 1
            
            return {
                "total_keys": total_keys,
                "expired_keys": expired_keys,
                "last_cleanup": int(self._last_cleanup)
            }

# Global instances
rate_limit_service = InMemoryRateLimitService()
cache_service = InMemoryCacheService() 