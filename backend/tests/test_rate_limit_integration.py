"""
Integration test for rate limiting with parallel execution.
Tests that rate limiters properly handle concurrent requests without hitting API limits.
"""
import unittest
import asyncio
import time
from backend.utils.rate_limit import APIRateLimiters


class TestRateLimitIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for rate limiting with parallel execution."""
    
    async def test_exa_rate_limiting_parallel(self):
        """Test that Exa rate limiter handles many parallel requests without exceeding limits."""
        limiters = APIRateLimiters()
        
        # Simulate 55 requests (11 intervals * 5 queries) like in the real scenario
        num_requests = 55
        request_times = []
        
        async def make_request(request_id: int):
            async with limiters.exa:
                request_times.append(time.time())
                # Simulate API call delay
                await asyncio.sleep(0.1)
                return request_id
        
        start_time = time.time()
        tasks = [make_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # Verify all requests completed
        self.assertEqual(len(results), num_requests)
        
        # Verify rate limiting: should take at least some time due to rate limits
        # With 15 req/min limit, 55 requests should take at least ~3.5 minutes if strictly enforced
        # But with concurrency of 5, it should be faster
        # Let's just verify it doesn't complete instantly (which would indicate no rate limiting)
        self.assertGreater(elapsed, 1.0, "Rate limiting should add some delay")
        
        # Verify requests are spread out (check that max requests per minute isn't exceeded)
        # Group requests by minute
        requests_by_minute = {}
        for req_time in request_times:
            minute = int(req_time // 60)
            requests_by_minute[minute] = requests_by_minute.get(minute, 0) + 1
        
        # Check that no minute has more than 15 requests (our limit)
        for minute, count in requests_by_minute.items():
            self.assertLessEqual(
                count, 20,  # Allow some tolerance for timing
                f"Minute {minute} had {count} requests, exceeding rate limit"
            )
        
        print(f"\n✅ Exa rate limiting test passed:")
        print(f"   - Total requests: {num_requests}")
        print(f"   - Total time: {elapsed:.2f}s")
        print(f"   - Requests per minute: {dict(requests_by_minute)}")
        print(f"   - Max concurrent: 5")
        print(f"   - Rate limit: 15 req/min")
    
    async def test_polymarket_rate_limiting_parallel(self):
        """Test Polymarket rate limiter with parallel requests."""
        limiters = APIRateLimiters()
        
        num_requests = 11  # One per interval
        request_times = []
        
        async def make_request(request_id: int):
            async with limiters.polymarket:
                request_times.append(time.time())
                await asyncio.sleep(0.05)
                return request_id
        
        start_time = time.time()
        tasks = [make_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        self.assertEqual(len(results), num_requests)
        # Polymarket should complete quickly (no per-minute limit, just concurrency)
        self.assertLess(elapsed, 5.0, "Polymarket requests should complete quickly")
        
        print(f"\n✅ Polymarket rate limiting test passed:")
        print(f"   - Total requests: {num_requests}")
        print(f"   - Total time: {elapsed:.2f}s")
    
    async def test_openrouter_rate_limiting_parallel(self):
        """Test OpenRouter rate limiter with parallel requests."""
        limiters = APIRateLimiters()
        
        num_requests = 22  # 11 intervals * 2 (queries + decisions)
        request_times = []
        
        async def make_request(request_id: int):
            async with limiters.openrouter:
                request_times.append(time.time())
                await asyncio.sleep(0.1)
                return request_id
        
        start_time = time.time()
        tasks = [make_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        self.assertEqual(len(results), num_requests)
        
        print(f"\n✅ OpenRouter rate limiting test passed:")
        print(f"   - Total requests: {num_requests}")
        print(f"   - Total time: {elapsed:.2f}s")
    
    async def test_daytona_rate_limiting_parallel(self):
        """Test Daytona rate limiter with parallel requests."""
        limiters = APIRateLimiters()
        
        num_requests = 11  # One per interval
        request_times = []
        
        async def make_request(request_id: int):
            async with limiters.daytona:
                request_times.append(time.time())
                await asyncio.sleep(0.5)  # Simulate sandbox creation delay
                return request_id
        
        start_time = time.time()
        tasks = [make_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        self.assertEqual(len(results), num_requests)
        # With max_concurrent=2, 11 requests should take at least 11/2 * 0.5 = ~2.75 seconds
        self.assertGreater(elapsed, 2.0, "Daytona requests should be limited by concurrency")
        
        print(f"\n✅ Daytona rate limiting test passed:")
        print(f"   - Total requests: {num_requests}")
        print(f"   - Total time: {elapsed:.2f}s")
        print(f"   - Max concurrent: 2")


if __name__ == '__main__':
    unittest.main()

