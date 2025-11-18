import unittest
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime, timezone
from backend.models import ExperimentConfig, ExperimentMode
from backend.orchestrator.core import Orchestrator

class TestOrchestrator(unittest.IsolatedAsyncioTestCase):

    async def test_orchestrator_flow(self):
        # Mock dependencies
        with patch("backend.orchestrator.core.PolymarketClient") as MockMarket, \
             patch("backend.orchestrator.core.ExaSearchClient") as MockSearch, \
             patch("backend.orchestrator.core.LLMClient") as MockLLM, \
             patch("backend.orchestrator.core.Researcher") as MockResearcher:
             
            # Setup Mocks
            market_instance = MockMarket.return_value
            market_instance.get_market_metadata = AsyncMock(return_value={
                "title": "Gemini", 
                "markets": [{"clobTokenIds": "[\"123\", \"456\"]"}]
            })
            market_instance.get_price_at = AsyncMock(return_value=0.6)
            
            researcher_instance = MockResearcher.return_value
            researcher_instance.generate_queries = AsyncMock(return_value=["q1"])
            
            search_instance = MockSearch.return_value
            search_instance.search = AsyncMock(return_value=[])
            
            # Config
            config = ExperimentConfig(
                market_slug="gemini",
                start_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc), # 2 hour window
                interval_minutes=60,
                mode=ExperimentMode.DIRECT_LLM
            )
            
            orchestrator = Orchestrator()
            # Inject mocked instances (since __init__ creates new ones, we need to mock the classes before __init__ or inject manually)
            # Actually, since we patched the classes at the module level, Orchestrator() will instantiate our Mocks.
            
            results = await orchestrator.run_experiment(config)
            
            # 10:00, 11:00, 12:00 -> 3 intervals
            self.assertEqual(len(results), 3)
            
            # Verify calls
            market_instance.get_market_metadata.assert_called_once()
            # Researcher called 3 times
            self.assertEqual(researcher_instance.generate_queries.call_count, 3)
            # Search called 3 times (once per interval for the 1 query)
            self.assertEqual(search_instance.search.call_count, 3)

if __name__ == '__main__':
    unittest.main()

