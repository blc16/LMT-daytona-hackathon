from typing import Protocol, List
from datetime import datetime
from backend.models import SearchSnippet

class SearchClient(Protocol):
    """Interface for searching web content."""

    async def search(self, query: str, time_upper_bound: datetime, limit: int = 5) -> List[SearchSnippet]:
        """
        Perform a search where all results must be published <= time_upper_bound.
        This prevents future leakage in backtests.
        """
        ...
