"""
Test to show raw API responses from Polymarket to understand the data structure.
"""
import asyncio
import json
import httpx
from datetime import datetime, timezone

async def test_raw_api_responses():
    """Show exactly what the Polymarket API returns."""
    
    print("="*80)
    print("RAW POLYMARKET API RESPONSES")
    print("="*80)
    
    # Test 1: Gamma API - Market Metadata
    print("\n" + "="*80)
    print("1. GAMMA API - Market Metadata")
    print("="*80)
    print("URL: https://gamma-api.polymarket.com/events")
    print("Params: {'slug': 'gemini-3pt0-released-by'}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://gamma-api.polymarket.com/events",
            params={"slug": "gemini-3pt0-released-by"}
        )
        response.raise_for_status()
        data = response.json()
        
        if data:
            event = data[0]
            print(f"\n✅ Response received:")
            print(f"   Title: {event.get('title')}")
            print(f"   Description: {event.get('description', '')[:200]}...")
            print(f"   Number of markets: {len(event.get('markets', []))}")
            
            print(f"\n   Full JSON structure:")
            print(json.dumps(event, indent=2, default=str)[:2000])  # First 2000 chars
            
            print(f"\n   Markets breakdown:")
            markets = event.get('markets', [])
            for i, market in enumerate(markets, 1):
                print(f"\n   Market {i}:")
                print(f"     - question: {market.get('question')}")
                print(f"     - endDateIso: {market.get('endDateIso')}")
                print(f"     - active: {market.get('active')}")
                print(f"     - closed: {market.get('closed')}")
                print(f"     - clobTokenIds: {market.get('clobTokenIds')}")
                print(f"     - outcomePrices: {market.get('outcomePrices')}")
                print(f"     - All keys: {list(market.keys())}")
    
    # Test 2: CLOB API - Price History for November market
    print("\n" + "="*80)
    print("2. CLOB API - Price History (November Market)")
    print("="*80)
    
    # Get November market token ID
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://gamma-api.polymarket.com/events",
            params={"slug": "gemini-3pt0-released-by"}
        )
        response.raise_for_status()
        data = response.json()
        markets = data[0].get('markets', [])
        november_market = next((m for m in markets if "november" in m.get("question", "").lower()), None)
        
        if november_market:
            import json as json_lib
            clob_ids_raw = november_market.get("clobTokenIds", [])
            if isinstance(clob_ids_raw, str):
                try:
                    clob_ids = json_lib.loads(clob_ids_raw)
                    token_id = clob_ids[0] if clob_ids else None
                except:
                    token_id = clob_ids_raw if clob_ids_raw else None
            elif isinstance(clob_ids_raw, list):
                token_id = clob_ids_raw[0] if clob_ids_raw else None
            else:
                token_id = None
            
            if token_id:
                print(f"   Token ID: {token_id}")
                print(f"   Market Question: {november_market.get('question')}")
                
                # Try max interval
                print(f"\n   Fetching with interval='max'...")
                response = await client.get(
                    "https://clob.polymarket.com/prices-history",
                    params={
                        "market": token_id,
                        "interval": "max"
                    }
                )
                response.raise_for_status()
                history_data = response.json()
                history = history_data.get("history", [])
                
                print(f"   ✅ Received {len(history)} price points")
                if history:
                    first_ts = datetime.fromtimestamp(history[0]['t'], tz=timezone.utc)
                    last_ts = datetime.fromtimestamp(history[-1]['t'], tz=timezone.utc)
                    print(f"   First point: {first_ts} = {history[0]['p']:.4f}")
                    print(f"   Last point: {last_ts} = {history[-1]['p']:.4f}")
                    
                    # Show sample of points
                    print(f"\n   Sample points (first 10):")
                    for i, point in enumerate(history[:10], 1):
                        ts = datetime.fromtimestamp(point['t'], tz=timezone.utc)
                        print(f"     {i}. {ts} = {point['p']:.4f}")
                    
                    print(f"\n   Sample points (last 10):")
                    for i, point in enumerate(history[-10:], len(history)-9):
                        ts = datetime.fromtimestamp(point['t'], tz=timezone.utc)
                        print(f"     {i}. {ts} = {point['p']:.4f}")

if __name__ == '__main__':
    asyncio.run(test_raw_api_responses())

