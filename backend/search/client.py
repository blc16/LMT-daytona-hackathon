from typing import Protocol, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class SearchSnippet(BaseModel):
    id: str
    title: str
    url: str
    text: str
    published_date: str
    score: float

class SearchClient(Protocol):
    """Interface for searching web content."""

    async def search(self, query: str, time_upper_bound: datetime, limit: int = 5) -> List[SearchSnippet]:
        """
        Perform a search where all results must be published <= time_upper_bound.
        This prevents future leakage in backtests.
        """
        ...

