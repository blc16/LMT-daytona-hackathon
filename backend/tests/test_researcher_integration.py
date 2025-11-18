"""
Integration test for Researcher Agent.
Tests real LLM calls to verify query generation.
"""
import unittest
from datetime import datetime, timezone
from backend.orchestrator.researcher import Researcher
from backend.llm.client import LLMClient
from backend.config import settings

class TestResearcherIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for Researcher agent with real LLM calls."""
    
    async def test_generate_queries(self):
        """Test generating search queries for a real market."""
        print("\n" + "="*80)
        print("TEST: Researcher Agent - Query Generation")
        print("="*80)
        
        # Check API key
        if not settings.OPENROUTER_API_KEY or "your_" in settings.OPENROUTER_API_KEY:
            self.skipTest("OPENROUTER_API_KEY not set")
        
        llm_client = LLMClient()
        researcher = Researcher(llm_client)
        
        # Real market data (from Polymarket API)
        market_info = {
            "title": "Gemini 3.0 released by...?",
            "description": "This market will resolve according to the date (ET) Google's Gemini 3.0 model is made available to the general public."
        }
        
        current_price = 0.8250  # 82.50% probability
        timestamp = datetime(2025, 11, 3, 12, 0, tzinfo=timezone.utc)
        model = "openai/gpt-4o-mini"
        
        print(f"\nInput:")
        print(f"  Market Title: {market_info['title']}")
        print(f"  Market Description: {market_info['description'][:100]}...")
        print(f"  Current Price (YES probability): {current_price:.2%}")
        print(f"  Timestamp: {timestamp}")
        print(f"  Model: {model}")
        print(f"\nCalling generate_queries(market_info, current_price, timestamp, model)...")
        
        queries = await researcher.generate_queries(
            market_info=market_info,
            current_price=current_price,
            timestamp=timestamp,
            model=model
        )
        
        print(f"\n✅ Output:")
        print(f"  Number of queries generated: {len(queries)}")
        print(f"  Queries:")
        for i, query in enumerate(queries, 1):
            print(f"    {i}. {query}")
        
        # Verify
        self.assertIsInstance(queries, list)
        self.assertGreater(len(queries), 0, "Should generate at least one query")
        self.assertLessEqual(len(queries), 10, "Should not generate too many queries")
        
        # Check query quality
        for query in queries:
            self.assertIsInstance(query, str)
            self.assertGreater(len(query), 10, "Query should be meaningful")
            # Should not be generic
            self.assertNotIn("what is prediction market", query.lower())
        
        print(f"\n✅ Test PASSED: Query generation successful")
        print(f"\nAnalysis:")
        print(f"  - Generated {len(queries)} queries")
        print(f"  - All queries are strings: {all(isinstance(q, str) for q in queries)}")
        print(f"  - Average query length: {sum(len(q) for q in queries) / len(queries):.1f} characters")
        print(f"  - Queries are market-specific: {all('gemini' in q.lower() or 'google' in q.lower() for q in queries)}")

if __name__ == '__main__':
    unittest.main()

