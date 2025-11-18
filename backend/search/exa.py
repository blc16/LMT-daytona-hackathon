import httpx
from datetime import datetime
from typing import List, Optional
from backend.models import SearchSnippet
from backend.config import settings

class ExaSearchClient:
    """
    Client for interacting with the Exa API (formerly Metaphor).
    Documentation: https://docs.exa.ai/reference/search
    """

    def __init__(self):
        self.base_url = "https://api.exa.ai/search"
        self.headers = {
            "x-api-key": settings.EXA_API_KEY,
            "Content-Type": "application/json"
        }

    async def search(self, query: str, time_upper_bound: datetime, limit: int = 5) -> List[SearchSnippet]:
        """
        Perform a search where all results must be published <= time_upper_bound.
        
        Args:
            query: The user's search query.
            time_upper_bound: The strict cutoff date for news.
            limit: Number of results to return.
            
        Returns:
            List of SearchSnippet objects.
        """
        # Exa expects ISO 8601 format for dates
        end_date_str = time_upper_bound.isoformat()

        payload = {
            "query": query,
            "numResults": limit,
            "endPublishedDate": end_date_str,
            "useAutoprompt": True,
            "contents": {
                "text": True  # Fetch full text content
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.base_url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            snippets = []
            for result in data.get("results", []):
                # Handle potential missing fields gracefully
                published_date = result.get("publishedDate") or ""
                
                snippet = SearchSnippet(
                    id=result.get("id", result.get("url", "")),
                    title=result.get("title", "No Title"),
                    url=result.get("url", ""),
                    text=result.get("text", "")[:1000], # Truncate text to save context window if needed
                    published_date=published_date,
                    score=result.get("score", 0.0)
                )
                snippets.append(snippet)
                
            return snippets

