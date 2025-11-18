from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from backend.llm.client import LLMClient

class SearchQueries(BaseModel):
    queries: List[str] = Field(..., description="A list of 3-5 specific search queries")

class Researcher:
    """
    Agent responsible for generating search queries to research the market.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def generate_queries(self, market_info: Dict[str, Any], current_price: float, timestamp: datetime, model: str = "openai/gpt-4o") -> List[str]:
        """
        Generate search queries based on the market state and time.
        """
        system_prompt = (
            "You are an expert researcher for prediction markets. "
            "Your goal is to find new information that would help a trader determine the outcome of a specific event. "
            "You will be given a market description, the current price (probability), and the current date. "
            "Generate 3-5 natural language search queries optimized for a neural search engine like Exa. "
            "Focus on recent news, events, or announcements relative to the current date that might have caused price movements or changed the probability. "
            "Do not include generic queries like 'what is prediction market'."
        )

        user_prompt = (
            f"Market: {market_info.get('title')}\n"
            f"Description: {market_info.get('description')}\n"
            f"Current Date: {timestamp.isoformat()}\n"
            f"Current Probability (YES): {current_price:.2f}\n\n"
            "Generate specific search queries to find relevant evidence. "
            "Return your response as valid JSON with this exact structure: "
            "Make sure each query is unique and gathers different information."
            '{{"queries": ["query 1", "query 2", "query 3"]}}'
        )

        result = await self.llm.generate_json(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=SearchQueries
        )
        
        return result.queries

