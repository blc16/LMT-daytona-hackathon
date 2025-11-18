"""
Integration test for Polymarket Client.
Tests real API calls to verify market metadata and price fetching.
"""
import unittest
from datetime import datetime, timezone, timedelta
from backend.market.polymarket import PolymarketClient
from backend.config import settings

class TestPolymarketIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for Polymarket client with real API calls."""
    
    async def test_get_market_metadata(self):
        """Test fetching market metadata for Gemini 3.0 market."""
        print("\n" + "="*80)
        print("TEST 1: Market Metadata Fetching")
        print("="*80)
        
        client = PolymarketClient()
        market_slug = "gemini-3pt0-released-by"
        
        print(f"\nInput:")
        print(f"  Market Slug: {market_slug}")
        print(f"\nCalling get_market_metadata('{market_slug}')...")
        
        metadata = await client.get_market_metadata(market_slug)
        
        print(f"\n✅ Output (Market Metadata):")
        print(f"  Title: {metadata.get('title', 'N/A')}")
        print(f"  Description: {metadata.get('description', 'N/A')[:200]}...")
        print(f"  Number of markets: {len(metadata.get('markets', []))}")
        
        markets = metadata.get("markets", [])
        if markets:
            print(f"\n  Markets found:")
            for i, market in enumerate(markets[:5], 1):  # Show first 5
                print(f"    {i}. Question: {market.get('question', 'N/A')[:60]}...")
                print(f"       End Date: {market.get('endDateIso', 'N/A')}")
                print(f"       Active: {market.get('active', False)}")
                print(f"       Closed: {market.get('closed', False)}")
                print(f"       CLOB Token IDs: {market.get('clobTokenIds', 'N/A')}")
        
        # Verify structure
        self.assertIn("title", metadata)
        self.assertIn("markets", metadata)
        self.assertGreater(len(markets), 0, "Should have at least one market")
        
        print(f"\n✅ Test 1 PASSED: Market metadata fetched successfully")
    
    async def test_get_price_at(self):
        """Test fetching price at a specific timestamp."""
        print("\n" + "="*80)
        print("TEST 2: Price Fetching at Specific Timestamp")
        print("="*80)
        
        client = PolymarketClient()
        market_slug = "gemini-3pt0-released-by"
        
        # Get market metadata first to get token ID
        print(f"\nStep 1: Fetching market metadata...")
        metadata = await client.get_market_metadata(market_slug)
        markets = metadata.get("markets", [])
        
        if not markets:
            self.skipTest("No markets found")
        
        # Select November market specifically
        november_markets = [m for m in markets if "november" in m.get("question", "").lower()]
        if november_markets:
            # Prefer open markets, then most recent
            open_november = [m for m in november_markets if m.get("active") and not m.get("closed")]
            if open_november:
                target_market = open_november[0]
            else:
                november_markets.sort(key=lambda m: m.get("endDateIso", ""), reverse=True)
                target_market = november_markets[0]
        else:
            # Fallback: select first open market or most recent closed
            open_markets = [m for m in markets if m.get("active") and not m.get("closed")]
            if open_markets:
                target_market = open_markets[0]
            else:
                markets.sort(key=lambda m: m.get("endDateIso", ""), reverse=True)
                target_market = markets[0]
        
        # Extract token ID
        import json
        clob_ids_raw = target_market.get("clobTokenIds", [])
        if isinstance(clob_ids_raw, str):
            try:
                clob_ids = json.loads(clob_ids_raw)
                token_id = clob_ids[0] if clob_ids else None
            except json.JSONDecodeError:
                token_id = clob_ids_raw if clob_ids_raw else None
        elif isinstance(clob_ids_raw, list):
            token_id = clob_ids_raw[0] if clob_ids_raw else None
        else:
            token_id = None
        
        if not token_id:
            self.skipTest(f"Could not extract token ID from market: {target_market.get('clobTokenIds')}")
        
        print(f"\nStep 2: Extracted Token ID")
        print(f"  Token ID: {token_id}")
        print(f"  Market Question: {target_market.get('question', 'N/A')[:60]}...")
        print(f"  Market End Date: {target_market.get('endDateIso', 'N/A')}")
        
        # Use a historical timestamp (October 2025 - when market was active)
        # Market end date is 2025-10-31, so use dates before that
        test_timestamp = datetime(2025, 10, 15, 12, 0, tzinfo=timezone.utc)
        interval_minutes = 1440  # 1 day intervals
        
        print(f"\nStep 3: Fetching price")
        print(f"  Input:")
        print(f"    Token ID: {token_id}")
        print(f"    Timestamp: {test_timestamp}")
        print(f"    Interval Minutes: {interval_minutes}")
        print(f"\n  Calling get_price_at(token_id, timestamp, interval_minutes)...")
        
        # First, check what date range has data using 'max' interval
        print(f"\n  Checking available price history (using 'max' interval)...")
        try:
            all_history = await client.get_all_available_history(token_id)
            print(f"    Found {len(all_history)} total price points")
            if all_history:
                first_point = datetime.fromtimestamp(all_history[0]['t'], tz=timezone.utc)
                last_point = datetime.fromtimestamp(all_history[-1]['t'], tz=timezone.utc)
                print(f"    First price: {first_point} = {all_history[0]['p']:.4f}")
                print(f"    Last price: {last_point} = {all_history[-1]['p']:.4f}")
                
                # Use a timestamp that we know has data (use a point in the middle, but ensure it's after the first point)
                if len(all_history) > 0:
                    # Use a point that's definitely in the middle of available data
                    # Make sure it's at least 1 hour after the first point to avoid edge cases
                    first_ts = all_history[0]['t']
                    last_ts = all_history[-1]['t']
                    mid_ts = (first_ts + last_ts) // 2
                    # Ensure it's at least 1 hour after first point
                    mid_ts = max(mid_ts, first_ts + 3600)
                    test_timestamp = datetime.fromtimestamp(mid_ts, tz=timezone.utc)
                    print(f"    Using timestamp from available data: {test_timestamp}")
                    print(f"    (First available: {first_point}, Last available: {last_point})")
            else:
                print(f"    ⚠️  No price history available for this token")
        except Exception as e:
            print(f"    Could not check available history: {e}")
            import traceback
            traceback.print_exc()
        
        price = await client.get_price_at(token_id, test_timestamp, interval_minutes)
        
        print(f"\n✅ Output:")
        print(f"  Price (YES probability): {price:.4f} ({price:.2%})")
        print(f"  Price is between 0 and 1: {0.0 <= price <= 1.0}")
        
        # Verify
        self.assertIsInstance(price, float)
        self.assertGreaterEqual(price, 0.0)
        self.assertLessEqual(price, 1.0)
        
        print(f"\n✅ Test 2 PASSED: Price fetched successfully")
    
    async def test_get_price_history_range(self):
        """Test fetching price history over a time range."""
        print("\n" + "="*80)
        print("TEST 3: Price History Range Fetching")
        print("="*80)
        
        client = PolymarketClient()
        market_slug = "gemini-3pt0-released-by"
        
        # Get token ID
        metadata = await client.get_market_metadata(market_slug)
        markets = metadata.get("markets", [])
        if not markets:
            self.skipTest("No markets found")
        
        # Select November market specifically
        november_markets = [m for m in markets if "november" in m.get("question", "").lower()]
        if november_markets:
            # Prefer open markets, then most recent
            open_november = [m for m in november_markets if m.get("active") and not m.get("closed")]
            if open_november:
                target_market = open_november[0]
            else:
                november_markets.sort(key=lambda m: m.get("endDateIso", ""), reverse=True)
                target_market = november_markets[0]
        else:
            # Fallback: select first open market or most recent closed
            open_markets = [m for m in markets if m.get("active") and not m.get("closed")]
            if open_markets:
                target_market = open_markets[0]
            else:
                markets.sort(key=lambda m: m.get("endDateIso", ""), reverse=True)
                target_market = markets[0]
        
        import json
        clob_ids_raw = target_market.get("clobTokenIds", [])
        if isinstance(clob_ids_raw, str):
            try:
                clob_ids = json.loads(clob_ids_raw)
                token_id = clob_ids[0] if clob_ids else None
            except json.JSONDecodeError:
                token_id = clob_ids_raw if clob_ids_raw else None
        elif isinstance(clob_ids_raw, list):
            token_id = clob_ids_raw[0] if clob_ids_raw else None
        else:
            token_id = None
        
        if not token_id:
            self.skipTest("Could not extract token ID")
        
        # First check what dates have data
        print(f"\nStep 1: Checking available price history...")
        try:
            all_history = await client.get_all_available_history(token_id)
            if all_history:
                first_ts = datetime.fromtimestamp(all_history[0]['t'], tz=timezone.utc)
                last_ts = datetime.fromtimestamp(all_history[-1]['t'], tz=timezone.utc)
                print(f"  Available data range: {first_ts} to {last_ts} ({len(all_history)} points)")
                
                # Use a 3-day window from the available data
                if len(all_history) >= 2:
                    # Use dates from the middle of available range
                    mid_index = len(all_history) // 2
                    mid_ts = datetime.fromtimestamp(all_history[mid_index]['t'], tz=timezone.utc)
                    start_time = mid_ts - timedelta(days=1)
                    end_time = mid_ts + timedelta(days=2)
                else:
                    # Fallback to original dates
                    start_time = datetime(2025, 10, 12, 12, 0, tzinfo=timezone.utc)
                    end_time = datetime(2025, 10, 15, 12, 0, tzinfo=timezone.utc)
            else:
                print(f"  ⚠️  No price history available, using default dates")
                start_time = datetime(2025, 10, 12, 12, 0, tzinfo=timezone.utc)
                end_time = datetime(2025, 10, 15, 12, 0, tzinfo=timezone.utc)
        except Exception as e:
            print(f"  Could not check available history: {e}, using default dates")
            start_time = datetime(2025, 10, 12, 12, 0, tzinfo=timezone.utc)
            end_time = datetime(2025, 10, 15, 12, 0, tzinfo=timezone.utc)
        
        print(f"\nStep 2: Fetching price history")
        print(f"  Input:")
        print(f"    Token ID: {token_id}")
        print(f"    Start Time: {start_time}")
        print(f"    End Time: {end_time}")
        print(f"    Interval: 1h")
        print(f"\n  Calling get_market_history(token_id, start_time, end_time, interval='1h')...")
        
        history = await client.get_market_history(token_id, start_time, end_time, interval="1h")
        
        print(f"\n✅ Output:")
        print(f"  Number of price points: {len(history)}")
        
        if history:
            print(f"\n  First 5 price points:")
            for i, point in enumerate(history[:5], 1):
                timestamp = datetime.fromtimestamp(point['t'], tz=timezone.utc)
                print(f"    {i}. Time: {timestamp}, Price: {point['p']:.4f} ({point['p']:.2%})")
            
            print(f"\n  Last 5 price points:")
            for i, point in enumerate(history[-5:], -4):
                timestamp = datetime.fromtimestamp(point['t'], tz=timezone.utc)
                print(f"    {i if i > 0 else len(history) + i}. Time: {timestamp}, Price: {point['p']:.4f} ({point['p']:.2%})")
        
        # Verify
        self.assertIsInstance(history, list)
        if history:
            self.assertIn('t', history[0])
            self.assertIn('p', history[0])
        
        print(f"\n✅ Test 3 PASSED: Price history fetched successfully")

if __name__ == '__main__':
    unittest.main()

