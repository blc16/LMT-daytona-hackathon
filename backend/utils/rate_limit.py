"""
Rate limiting utilities for API calls.
Uses asyncio.Semaphore to limit concurrent requests per API.
Also supports per-minute rate limiting using token bucket algorithm.
"""
import asyncio
import time
from typing import Optional
from collections import deque

class RateLimiter:
    """
    Rate limiter using semaphores to control concurrent API calls.
    Also includes optional delay between requests and per-minute rate limiting.
    """
    def __init__(self, max_concurrent: int = 5, delay_seconds: float = 0.1, 
                 requests_per_minute: Optional[int] = None):
        """
        Args:
            max_concurrent: Maximum number of concurrent requests
            delay_seconds: Minimum delay between requests (helps avoid burst rate limits)
            requests_per_minute: Optional limit on requests per minute (token bucket)
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.delay_seconds = delay_seconds
        self.last_request_time: Optional[float] = None
        
        # Token bucket for per-minute rate limiting
        self.requests_per_minute = requests_per_minute
        self.request_times: deque = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a permit for making an API call."""
        await self.semaphore.acquire()
        
        # Per-minute rate limiting (token bucket)
        if self.requests_per_minute:
            async with self._lock:
                current_time = time.time()
                # Remove requests older than 1 minute
                while self.request_times and current_time - self.request_times[0] > 60:
                    self.request_times.popleft()
                
                # If we've hit the limit, wait until we can make another request
                if len(self.request_times) >= self.requests_per_minute:
                    wait_time = 60 - (current_time - self.request_times[0])
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                        # Clean up again after waiting
                        current_time = time.time()
                        while self.request_times and current_time - self.request_times[0] > 60:
                            self.request_times.popleft()
                
                # Record this request
                self.request_times.append(time.time())
        
        # Add delay if needed (for burst protection)
        if self.delay_seconds > 0:
            current_time = time.time()
            if self.last_request_time is not None:
                elapsed = current_time - self.last_request_time
                if elapsed < self.delay_seconds:
                    await asyncio.sleep(self.delay_seconds - elapsed)
            self.last_request_time = time.time()
    
    def release(self):
        """Release a permit after API call completes."""
        self.semaphore.release()
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False  # Don't suppress exceptions


class APIRateLimiters:
    """
    Centralized rate limiters for all APIs.
    Configure limits based on each API's rate limits.
    """
    def __init__(self):
        # Polymarket: Generally allows higher concurrency, but be conservative
        self.polymarket = RateLimiter(max_concurrent=10, delay_seconds=0.05)
        
        # Exa: Check their docs, but be conservative (typically 10-20 req/min)
        # Limit to 15 requests per minute to avoid 429 errors
        # Reduced concurrency to 5 to better respect rate limits
        self.exa = RateLimiter(max_concurrent=5, delay_seconds=0.2, requests_per_minute=15)
        
        # OpenRouter: Varies by model, but generally allows good concurrency
        # Be conservative to avoid hitting limits
        self.openrouter = RateLimiter(max_concurrent=10, delay_seconds=0.1)
        
        # Daytona: Sandbox creation/execution can be slower, limit concurrency
        # Reduced to 2 to avoid disk limit issues (30GiB total limit)
        self.daytona = RateLimiter(max_concurrent=2, delay_seconds=0.5)

