import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class PolymarketClient:
    """Client for interacting with the Polymarket API (Gamma + CLOB)."""

    def __init__(self):
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.clob_url = "https://clob.polymarket.com"

    async def get_market_metadata(self, slug: str) -> Dict[str, Any]:
        """
        Fetch event metadata by slug using Gamma API.
        
        Args:
            slug: The event slug (e.g. "gemini-3pt0-released-by")
            
        Returns:
            Dict containing event details and list of specific markets (outcomes).
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.gamma_url}/events"
            params = {"slug": slug}
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                raise ValueError(f"No event found for slug: {slug}")
                
            return data[0]

    async def get_market_history(self, clob_token_id: str, start_time: datetime, end_time: datetime, interval: str = "1h") -> List[Dict[str, Any]]:
        """
        Fetch historical price data from CLOB API.
        
        Args:
            clob_token_id: The unique token ID for the specific outcome (market).
            start_time: Start datetime (UTC).
            end_time: End datetime (UTC).
            interval: '1m', '1h', '6h', '1d', '1w', or 'max' (per API docs)
            
        Returns:
            List of dicts with 't' (timestamp) and 'p' (price).
        """
        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())
        
        async with httpx.AsyncClient() as client:
            url = f"{self.clob_url}/prices-history"
            params = {
                "market": clob_token_id,
                "startTs": start_ts,
                "endTs": end_ts,
                "interval": interval
            }
            
            # For 1m intervals, add fidelity parameter (required per API docs)
            if interval == "1m":
                params["fidelity"] = 10  # Minimum fidelity for 1m is 10 minutes per API docs
            
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                error_text = response.text
                print(f"Polymarket API Error {response.status_code}: {error_text}")
                print(f"URL: {url}")
                print(f"Params: {params}")
            
            response.raise_for_status()
            data = response.json()
            history = data.get("history", [])
            
            if history:
                # Log first and last points for debugging
                first_ts = datetime.fromtimestamp(history[0]['t'], tz=timezone.utc)
                last_ts = datetime.fromtimestamp(history[-1]['t'], tz=timezone.utc)
                print(f"    Retrieved {len(history)} price points from {first_ts} to {last_ts}")
            
            return history
    
    async def get_all_available_history(self, clob_token_id: str) -> List[Dict[str, Any]]:
        """
        Get all available price history using 'max' interval.
        Useful for discovering what date range has data.
        
        Args:
            clob_token_id: The CLOB token ID
            
        Returns:
            List of all available price points
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.clob_url}/prices-history"
            params = {
                "market": clob_token_id,
                "interval": "max"  # Get all available data
            }
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            history = data.get("history", [])
            
            # Debug: log the full response if empty
            if not history:
                print(f"    ⚠️  API returned empty history. Full response: {data}")
                print(f"    Request params: {params}")
            
            return history

    async def get_price_at(self, clob_token_id: str, timestamp: datetime, interval_minutes: Optional[int] = None) -> float:
        """
        Get the price closest to the given timestamp.
        Fetches all available data and filters to find the nearest point (API window params are unreliable).
        
        Args:
            clob_token_id: The CLOB token ID
            timestamp: The target timestamp
            interval_minutes: The experiment's interval in minutes (not used, but kept for API compatibility)
        """
        ts = int(timestamp.timestamp())
        
        # Fetch all available history - API window parameters are unreliable
        # We'll filter the data ourselves for accuracy
        all_history = await self.get_all_available_history(clob_token_id)
        
        if not all_history:
            raise ValueError(
                f"No price history available for token {clob_token_id}. "
                f"Market may not have started trading yet."
            )
        
        # Find closest point <= timestamp (no lookahead - strict backtesting)
        valid_points = [p for p in all_history if p['t'] <= ts]
        
        if not valid_points:
            # Show what we have available
            earliest_point = all_history[0]
            latest_point = all_history[-1]
            earliest_dt = datetime.fromtimestamp(earliest_point['t'], tz=timezone.utc)
            latest_dt = datetime.fromtimestamp(latest_point['t'], tz=timezone.utc)
            raise ValueError(
                f"No valid price point found before timestamp {timestamp} ({ts}). "
                f"Available history range: {earliest_dt} to {latest_dt}. "
                f"All available prices are after the requested timestamp (lookahead prevention)."
            )
        
        # Return the last valid point (latest time <= timestamp)
        price = valid_points[-1]['p']
        price_time = datetime.fromtimestamp(valid_points[-1]['t'], tz=timezone.utc)
        print(f"    Found price {price:.4f} at {price_time} (requested: {timestamp})")
        return price
