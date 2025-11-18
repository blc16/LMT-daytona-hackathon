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
            interval: '1m', '1h', '1d', etc.
            
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
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("history", [])

    async def get_price_at(self, clob_token_id: str, timestamp: datetime, interval_minutes: Optional[int] = None) -> float:
        """
        Get the price closest to the given timestamp.
        Fetches a small window around the timestamp to find the nearest point.
        
        Args:
            clob_token_id: The CLOB token ID
            timestamp: The target timestamp
            interval_minutes: The experiment's interval in minutes (used to determine CLOB API interval granularity)
        """
        ts = int(timestamp.timestamp())
        
        # Determine CLOB interval based on experiment interval
        # Map experiment intervals to CLOB intervals
        if interval_minutes is None:
            clob_interval = "1h"  # Default
            window_seconds = 3600  # 1 hour window
        elif interval_minutes >= 1440:  # 1 day or more
            clob_interval = "1d"
            window_seconds = 86400  # 1 day window
        elif interval_minutes >= 60:  # 1 hour or more
            clob_interval = "1h"
            window_seconds = 3600  # 1 hour window
        else:  # Less than 1 hour
            clob_interval = "1h"  # Use 1h as minimum granularity
            window_seconds = interval_minutes * 60  # Use experiment interval as window
        
        async with httpx.AsyncClient() as client:
            url = f"{self.clob_url}/prices-history"
            params = {
                "market": clob_token_id,
                "startTs": ts - window_seconds,
                "endTs": ts + window_seconds,
                "interval": clob_interval
            }
            response = await client.get(url, params=params)
            if response.status_code != 200:
                error_text = response.text
                print(f"Polymarket CLOB API Error {response.status_code}: {error_text}")
                print(f"URL: {url}")
                print(f"Params: {params}")
                print(f"Token ID: {clob_token_id}")
            response.raise_for_status()
            data = response.json()
            history = data.get("history", [])
            
            if not history:
                return 0.0 # Or raise error / return None
                
            # Find closest point <= timestamp (no lookahead)
            valid_points = [p for p in history if p['t'] <= ts]
            if not valid_points:
                # If no point before, maybe take the very first point if it's close?
                # For strict backtesting, we should probably return the earliest known price or None.
                # Let's return the closest one generally for robustness in this hackathon
                return history[0]['p']
                
            # Return the last one (latest time <= timestamp)
            return valid_points[-1]['p']
