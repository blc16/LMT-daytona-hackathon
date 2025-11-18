# Rate Limit Analysis and Fixes

## Issues Identified from Terminal Output

### 1. Exa API Rate Limit Violations (429 Errors)

**Problem:**
- Multiple "429 Too Many Requests" errors from Exa API
- Experiment was processing 11 intervals in parallel
- Each interval generates 5 search queries = 55 total queries
- Rate limiter was set to `max_concurrent=10` with `delay_seconds=0.15`
- Still hitting rate limits despite concurrency control

**Root Cause:**
- Exa API has a **per-minute rate limit** (typically 10-20 requests per minute)
- Our rate limiter only controlled **concurrent requests**, not **requests per minute**
- With 55 queries starting simultaneously, even with concurrency limit of 10, we were making too many requests per minute
- The delay between requests (0.15s) wasn't sufficient to stay under the per-minute limit

**Solution Implemented:**
1. Added **per-minute rate limiting** using token bucket algorithm
2. Set Exa rate limiter to:
   - `max_concurrent=5` (reduced from 10)
   - `delay_seconds=0.2` (increased from 0.15)
   - `requests_per_minute=15` (new limit)
3. Rate limiter now tracks requests in a sliding 60-second window
4. If limit is reached, waits until oldest request expires before allowing new requests

### 2. Daytona Disk Limit Issues

**Problem:**
- "Total disk limit exceeded. Maximum allowed: 30GiB" errors
- Multiple sandboxes being created concurrently

**Solution:**
- Already implemented: Reduced Daytona concurrency to `max_concurrent=2`
- Added delay of `0.5s` between requests
- This prevents too many sandboxes from being created simultaneously

## Rate Limiter Configuration

### Current Settings:

```python
# Polymarket
max_concurrent=10
delay_seconds=0.05
requests_per_minute=None  # No per-minute limit

# Exa Search
max_concurrent=5           # Reduced from 10
delay_seconds=0.2         # Increased from 0.15
requests_per_minute=15    # NEW: Per-minute limit

# OpenRouter
max_concurrent=10
delay_seconds=0.1
requests_per_minute=None  # No per-minute limit

# Daytona
max_concurrent=2          # Reduced to avoid disk limits
delay_seconds=0.5        # Increased delay
requests_per_minute=None  # No per-minute limit
```

## Expected Behavior After Fix

### Exa API Requests:
- **Before:** 55 queries starting simultaneously → many 429 errors
- **After:** 
  - Max 5 concurrent requests
  - Max 15 requests per minute
  - 55 queries will take ~3-4 minutes to complete (respecting rate limits)
  - No 429 errors expected

### Performance Impact:
- **Slower but reliable:** Experiments will take longer but won't fail due to rate limits
- **Better resource usage:** Prevents API quota exhaustion
- **Graceful degradation:** Failed requests can be retried without overwhelming the API

## Testing

Created `test_rate_limit_integration.py` to verify:
1. Exa rate limiter properly enforces per-minute limits
2. All rate limiters handle parallel execution correctly
3. No rate limit violations occur during normal operation

## Recommendations

1. **Monitor API usage:** Track rate limit errors and adjust limits if needed
2. **Consider caching:** Cache Exa search results for similar queries to reduce API calls
3. **Batch processing:** For very large experiments, consider processing intervals in smaller batches
4. **Retry logic:** Add exponential backoff for 429 errors
5. **Rate limit headers:** Check if Exa API returns rate limit headers (X-RateLimit-*) and use them dynamically

