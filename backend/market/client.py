from typing import Protocol, List, Dict, Any, Optional
from datetime import datetime

class MarketClient(Protocol):
    """Interface for interacting with prediction markets."""

    async def get_market_metadata(self, market_id: str) -> Dict[str, Any]:
        """Fetch static metadata for a market (description, expiry, rules)."""
        ...

    async def get_odds_at(self, market_id: str, timestamp: datetime) -> float:
        """
        Get the market odds (probability of YES) at a specific historical timestamp.
        Should handle interpolation or finding the nearest tick.
        """
        ...

    async def get_odds_timeseries(self, market_id: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Fetch a timeseries of odds within a window."""
        ...

