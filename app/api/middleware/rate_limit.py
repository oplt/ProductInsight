"""
Rate limiting middleware for API endpoints.
"""

from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
import time
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter."""
    
    def __init__(self, redis_client=None):
        """Initialize rate limiter with Redis client."""
        self.redis = redis_client
        if not self.redis:
            try:
                import redis
                redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
                self.redis = redis.from_url(redis_url, decode_responses=True)
            except ImportError:
                logger.warning("Redis not available, using in-memory rate limiting")
                self.redis = None
        
        # In-memory fallback for development
        self._memory_store = {}
    
    def is_allowed(self, key: str, limit: int, window_seconds: int) -> tuple[bool, Dict]:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            (is_allowed, info_dict)
        """
        if self.redis:
            return self._redis_rate_limit(key, limit, window_seconds)
        else:
            return self._memory_rate_limit(key, limit, window_seconds)
    
    def _redis_rate_limit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, Dict]:
        """Redis-based sliding window rate limiting."""
        try:
            now = time.time()
            pipeline = self.redis.pipeline()
            
            # Remove expired entries
            pipeline.zremrangebyscore(key, 0, now - window_seconds)
            
            # Count current requests
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(now): now})
            
            # Set expiration
            pipeline.expire(key, window_seconds)
            
            results = pipeline.execute()
            current_count = results[1]
            
            # Check if limit exceeded
            if current_count >= limit:
                # Remove the request we just added since it's not allowed
                self.redis.zrem(key, str(now))
                
                return False, {
                    'current_count': current_count,
                    'limit': limit,
                    'window_seconds': window_seconds,
                    'retry_after': window_seconds
                }
            
            return True, {
                'current_count': current_count + 1,
                'limit': limit,
                'window_seconds': window_seconds,
                'remaining': limit - current_count - 1
            }
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {str(e)}")
            # Fallback to allow request if Redis fails
            return True, {'error': 'rate_limiter_unavailable'}
    
    def _memory_rate_limit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, Dict]:
        """In-memory sliding window rate limiting."""
        now = time.time()
        
        if key not in self._memory_store:
            self._memory_store[key] = []
        
        # Remove expired entries
        self._memory_store[key] = [
            timestamp for timestamp in self._memory_store[key]
            if timestamp > now - window_seconds
        ]
        
        current_count = len(self._memory_store[key])
        
        if current_count >= limit:
            return False, {
                'current_count': current_count,
                'limit': limit,
                'window_seconds': window_seconds,
                'retry_after': window_seconds
            }
        
        # Add current request
        self._memory_store[key].append(now)
        
        return True, {
            'current_count': current_count + 1,
            'limit': limit,
            'window_seconds': window_seconds,
            'remaining': limit - current_count - 1
        }


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limit(requests: int, per_minute: bool = True, per_hour: bool = False, 
               per_day: bool = False, key_func: Optional[callable] = None):
    """
    Rate limiting decorator.
    
    Args:
        requests: Number of requests allowed
        per_minute: Rate limit per minute (default)
        per_hour: Rate limit per hour
        per_day: Rate limit per day
        key_func: Custom function to generate rate limit key
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine time window
            if per_day:
                window_seconds = 24 * 60 * 60
                window_name = "day"
            elif per_hour:
                window_seconds = 60 * 60
                window_name = "hour"
            else:  # per_minute (default)
                window_seconds = 60
                window_name = "minute"
            
            # Generate rate limit key
            if key_func:
                rate_key = key_func()
            else:
                rate_key = get_default_rate_limit_key(f.__name__, window_name)
            
            # Check rate limit
            rate_limiter = get_rate_limiter()
            is_allowed, info = rate_limiter.is_allowed(rate_key, requests, window_seconds)
            
            if not is_allowed:
                logger.warning(f"Rate limit exceeded for key: {rate_key}")
                response = jsonify({
                    'status': 'error',
                    'message': f'Rate limit exceeded: {requests} requests per {window_name}',
                    'retry_after': info.get('retry_after', window_seconds),
                    'limit': requests,
                    'window': window_name
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(info.get('retry_after', window_seconds))
                response.headers['X-RateLimit-Limit'] = str(requests)
                response.headers['X-RateLimit-Remaining'] = str(info.get('remaining', 0))
                response.headers['X-RateLimit-Reset'] = str(int(time.time() + window_seconds))
                return response
            
            # Add rate limit headers to successful responses
            response = f(*args, **kwargs)
            
            # Add headers if response is a Flask response object
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(requests)
                response.headers['X-RateLimit-Remaining'] = str(info.get('remaining', 0))
                response.headers['X-RateLimit-Reset'] = str(int(time.time() + window_seconds))
            
            return response
        
        return decorated_function
    return decorator


def get_default_rate_limit_key(endpoint: str, window: str) -> str:
    """Generate default rate limit key."""
    # Try to get user ID
    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        # Check for API key or JWT token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('ApiKey '):
            # Extract user ID from API key (implement based on your API key format)
            user_id = "api_user"  # Placeholder
        else:
            # Fall back to IP address
            user_id = request.remote_addr
    
    return f"rate_limit:{endpoint}:{window}:{user_id}"


def api_rate_limit(requests_per_minute: int = 60):
    """Simplified rate limit decorator for API endpoints."""
    return rate_limit(requests=requests_per_minute, per_minute=True)


def strict_rate_limit(requests_per_hour: int = 100):
    """Strict rate limit for sensitive endpoints."""
    return rate_limit(requests=requests_per_hour, per_hour=True)


def user_rate_limit(requests: int, per_minute: bool = True):
    """User-specific rate limit."""
    def key_func():
        if current_user.is_authenticated:
            window = "minute" if per_minute else "hour"
            return f"user_rate_limit:{current_user.id}:{window}"
        else:
            return f"anonymous_rate_limit:{request.remote_addr}"
    
    return rate_limit(requests=requests, per_minute=per_minute, key_func=key_func)


def ip_rate_limit(requests: int, per_minute: bool = True):
    """IP-based rate limit."""
    def key_func():
        window = "minute" if per_minute else "hour"
        return f"ip_rate_limit:{request.remote_addr}:{window}"
    
    return rate_limit(requests=requests, per_minute=per_minute, key_func=key_func)


class RateLimitManager:
    """Manage rate limits for different user tiers."""
    
    # Rate limit configurations by user role
    RATE_LIMITS = {
        'anonymous': {
            'requests_per_minute': 10,
            'requests_per_hour': 100,
            'requests_per_day': 1000
        },
        'user': {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'requests_per_day': 10000
        },
        'premium': {
            'requests_per_minute': 120,
            'requests_per_hour': 2000,
            'requests_per_day': 20000
        },
        'admin': {
            'requests_per_minute': 300,
            'requests_per_hour': 5000,
            'requests_per_day': 50000
        }
    }
    
    @classmethod
    def get_user_limits(cls, user=None) -> Dict[str, int]:
        """Get rate limits for user based on their role."""
        if not user or not user.is_authenticated:
            return cls.RATE_LIMITS['anonymous']
        
        if user.is_admin():
            return cls.RATE_LIMITS['admin']
        elif user.is_premium():
            return cls.RATE_LIMITS['premium']
        else:
            return cls.RATE_LIMITS['user']
    
    @classmethod
    def adaptive_rate_limit(cls, per_minute: bool = True):
        """Adaptive rate limit based on user role."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                limits = cls.get_user_limits(current_user)
                
                if per_minute:
                    limit = limits['requests_per_minute']
                    window = 60
                    window_name = "minute"
                else:
                    limit = limits['requests_per_hour']
                    window = 3600
                    window_name = "hour"
                
                # Generate rate limit key
                if current_user.is_authenticated:
                    rate_key = f"adaptive_rate_limit:{current_user.id}:{window_name}"
                else:
                    rate_key = f"adaptive_rate_limit:{request.remote_addr}:{window_name}"
                
                # Check rate limit
                rate_limiter = get_rate_limiter()
                is_allowed, info = rate_limiter.is_allowed(rate_key, limit, window)
                
                if not is_allowed:
                    response = jsonify({
                        'status': 'error',
                        'message': f'Rate limit exceeded: {limit} requests per {window_name}',
                        'retry_after': info.get('retry_after', window)
                    })
                    response.status_code = 429
                    return response
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator
