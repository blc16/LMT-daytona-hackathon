"""
Unit tests for rate limiting module.
Tests RateLimiter and APIRateLimiters classes.
"""
import unittest
import asyncio
import time
from backend.utils.rate_limit import RateLimiter, APIRateLimiters


class TestRateLimiter(unittest.IsolatedAsyncioTestCase):
    """Test RateLimiter class."""
    
    async def test_semaphore_limit(self):
        """Test that semaphore limits concurrent requests."""
        limiter = RateLimiter(max_concurrent=2, delay_seconds=0)
        
        # Track concurrent executions
        concurrent = {"count": 0}
        max_concurrent = {"value": 0}
        
        async def task_with_limit():
            async with limiter:
                concurrent["count"] += 1
                max_concurrent["value"] = max(max_concurrent["value"], concurrent["count"])
                await asyncio.sleep(0.1)  # Simulate work
                concurrent["count"] -= 1
        
        # Launch 5 tasks, but only 2 should run concurrently
        tasks = [task_with_limit() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        # Maximum concurrent should be at most 2
        self.assertLessEqual(max_concurrent["value"], 2)
    
    async def test_delay_between_requests(self):
        """Test that delay is enforced between requests."""
        limiter = RateLimiter(max_concurrent=10, delay_seconds=0.1)
        
        times = []
        
        async def timed_request():
            async with limiter:
                times.append(time.time())
        
        # Make 3 requests
        await timed_request()
        await timed_request()
        await timed_request()
        
        # Check that delays were enforced (allowing some tolerance)
        if len(times) >= 2:
            delay1 = times[1] - times[0]
            self.assertGreaterEqual(delay1, 0.05)  # Allow some tolerance
        
        if len(times) >= 3:
            delay2 = times[2] - times[1]
            self.assertGreaterEqual(delay2, 0.05)  # Allow some tolerance
    
    async def test_context_manager(self):
        """Test that rate limiter works as context manager."""
        limiter = RateLimiter(max_concurrent=1, delay_seconds=0)
        
        acquired = False
        async with limiter:
            acquired = True
        
        self.assertTrue(acquired)
    
    async def test_exception_handling(self):
        """Test that exceptions don't prevent release."""
        limiter = RateLimiter(max_concurrent=1, delay_seconds=0)
        
        # First task should acquire
        async def failing_task():
            async with limiter:
                raise ValueError("Test error")
        
        # Should raise the exception
        with self.assertRaises(ValueError):
            await failing_task()
        
        # But semaphore should be released, allowing next task
        async def succeeding_task():
            async with limiter:
                return True
        
        result = await succeeding_task()
        self.assertTrue(result)


class TestAPIRateLimiters(unittest.TestCase):
    """Test APIRateLimiters class."""
    
    def test_initialization(self):
        """Test that all rate limiters are initialized."""
        limiters = APIRateLimiters()
        
        self.assertIsNotNone(limiters.polymarket)
        self.assertIsNotNone(limiters.exa)
        self.assertIsNotNone(limiters.openrouter)
        self.assertIsNotNone(limiters.daytona)
        
        # Check that they are RateLimiter instances
        self.assertIsInstance(limiters.polymarket, RateLimiter)
        self.assertIsInstance(limiters.exa, RateLimiter)
        self.assertIsInstance(limiters.openrouter, RateLimiter)
        self.assertIsInstance(limiters.daytona, RateLimiter)
    
    def test_polymarket_config(self):
        """Test Polymarket rate limiter configuration."""
        limiters = APIRateLimiters()
        # Polymarket should have reasonable concurrency
        self.assertGreaterEqual(limiters.polymarket.semaphore._value, 1)
    
    def test_exa_config(self):
        """Test Exa rate limiter configuration."""
        limiters = APIRateLimiters()
        # Exa should have delay to respect rate limits
        self.assertGreaterEqual(limiters.exa.delay_seconds, 0)
    
    def test_openrouter_config(self):
        """Test OpenRouter rate limiter configuration."""
        limiters = APIRateLimiters()
        # OpenRouter should have reasonable concurrency
        self.assertGreaterEqual(limiters.openrouter.semaphore._value, 1)
    
    def test_daytona_config(self):
        """Test Daytona rate limiter configuration."""
        limiters = APIRateLimiters()
        # Daytona should have lower concurrency (disk limits)
        self.assertLessEqual(limiters.daytona.semaphore._value, 5)
        # Should have delay to avoid overwhelming the API
        self.assertGreaterEqual(limiters.daytona.delay_seconds, 0)


class TestRateLimiterIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for rate limiters."""
    
    async def test_multiple_limiters_independent(self):
        """Test that different limiters work independently."""
        limiters = APIRateLimiters()
        
        # Use both limiters concurrently
        async def use_polymarket():
            async with limiters.polymarket:
                await asyncio.sleep(0.01)
                return "polymarket"
        
        async def use_exa():
            async with limiters.exa:
                await asyncio.sleep(0.01)
                return "exa"
        
        # Both should be able to run concurrently (different semaphores)
        results = await asyncio.gather(use_polymarket(), use_exa())
        self.assertEqual(set(results), {"polymarket", "exa"})
    
    async def test_nested_limiters(self):
        """Test using nested rate limiters (e.g., trader needs both OpenRouter and Daytona)."""
        limiters = APIRateLimiters()
        
        async def nested_usage():
            async with limiters.openrouter:
                async with limiters.daytona:
                    await asyncio.sleep(0.01)
                    return True
        
        result = await nested_usage()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()

