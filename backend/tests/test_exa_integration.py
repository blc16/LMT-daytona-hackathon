import unittest
from datetime import datetime, timezone, timedelta
from backend.search.exa import ExaSearchClient
from backend.config import settings

class TestExaIntegration(unittest.IsolatedAsyncioTestCase):

    async def test_real_search_time_filtering(self):
        """
        Integration test to verify Exa search with time filtering.
        Requires EXA_API_KEY in .env
        """
        if not settings.EXA_API_KEY or "your_" in settings.EXA_API_KEY:
            self.skipTest("EXA_API_KEY not set")

        client = ExaSearchClient()
        
        # Search for something with a known clear timeline, e.g., "ChatGPT 4 release"
        query = "ChatGPT 4 release date"
        
        # Date BEFORE GPT-4 launch (Launch was March 14, 2023)
        # Set cutoff to Jan 1, 2023. We should NOT see news about it being "released today".
        cutoff_date = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        print(f"\nSearching Exa for '{query}' before {cutoff_date}...")
        results = await client.search(query, cutoff_date, limit=3)
        
        print(f"Found {len(results)} results.")
        for res in results:
            print(f"- [{res.published_date}] {res.title}")
            
            # Basic validation: published_date should be <= cutoff_date
            if res.published_date:
                pub_dt = datetime.fromisoformat(res.published_date.replace("Z", "+00:00"))
                self.assertLessEqual(pub_dt, cutoff_date, f"Result {res.id} leaked from future!")
                
        # Now search AFTER release
        cutoff_date_future = datetime(2023, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
        print(f"\nSearching Exa for '{query}' before {cutoff_date_future}...")
        results_future = await client.search(query, cutoff_date_future, limit=3)
        
        # We expect at least one result to be from March 2023
        has_march_news = False
        for res in results_future:
            print(f"- [{res.published_date}] {res.title}")
            if res.published_date:
                pub_dt = datetime.fromisoformat(res.published_date.replace("Z", "+00:00"))
                if pub_dt > datetime(2023, 3, 1, tzinfo=timezone.utc):
                    has_march_news = True
        
        self.assertTrue(has_march_news, "Should have found news about GPT-4 release after launch date.")

if __name__ == '__main__':
    unittest.main()

