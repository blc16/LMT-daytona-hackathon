import unittest
from datetime import datetime, timezone, timedelta
from backend.models import ExperimentConfig, ExperimentMode
from backend.orchestrator.core import Orchestrator
from backend.config import settings

class TestOrchestratorIntegration(unittest.IsolatedAsyncioTestCase):
    """
    Full integration test: Real Polymarket + Real Exa + Real LLM.
    This will help us analyze how the system works end-to-end.
    """
    
    async def test_full_experiment_flow(self):
        """
        Run a real experiment for Gemini 3.0 market.
        Uses 3 intervals, 1 hour apart, over the last 3 hours.
        """
        # Check if we have required API keys
        if not settings.EXA_API_KEY or "your_" in settings.EXA_API_KEY:
            self.skipTest("EXA_API_KEY not set")
        if not settings.OPENROUTER_API_KEY or "your_" in settings.OPENROUTER_API_KEY:
            self.skipTest("OPENROUTER_API_KEY not set")
        
        # Use a historical time window: last 3 days with 1 day intervals
        # Use current date dynamically
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=3)
        
        config = ExperimentConfig(
            market_slug="gemini-3pt0-released-by",
            start_time=start_time,
            end_time=end_time,
            interval_minutes=1440,  # 1 day intervals (24 * 60 = 1440 minutes)
            num_simulations=1,
            model_provider="openai/gpt-4o-mini",  # Using gpt-4o-mini (gpt-5-mini doesn't exist)
            mode=ExperimentMode.DIRECT_LLM
        )
        
        print("\n" + "="*80)
        print("INTEGRATION TEST: Full Orchestrator Flow")
        print("="*80)
        print(f"Market: {config.market_slug}")
        print(f"Time Window: {start_time} to {end_time}")
        print(f"Intervals: {config.interval_minutes} minutes apart")
        print(f"Model: {config.model_provider}")
        print("="*80 + "\n")
        
        orchestrator = Orchestrator()
        results = await orchestrator.run_experiment(config)
        
        print("\n" + "="*80)
        print("RESULTS ANALYSIS & INTERVAL COMPARISON")
        print("="*80)
        
        # Track news URLs across intervals to see overlap
        all_news_urls = []
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Interval {i}: {result.timestamp} ---")
            print(f"Market Price (YES probability): {result.market_state.price:.2%}")
            print(f"Decisions made: {len(result.decisions)}")
            print(f"Aggregated Decision: {result.aggregated_decision} (confidence: {result.aggregated_confidence:.2%})")
            
            # Note: We can't access news from IntervalResult directly, but we logged it during processing
            # The news is in the context that was built but not stored in the result
        
        print(f"\n{'='*80}")
        print(f"SUMMARY & COMPARISON")
        print(f"{'='*80}")
        print(f"Total intervals processed: {len(results)}")
        print(f"All intervals have market state: {all(r.market_state is not None for r in results)}")
        if len(results) > 0:
            prices = [r.market_state.price for r in results]
            print(f"Price range: {min(prices):.2%} - {max(prices):.2%}")
            print(f"Price trend: {' ↗️ Increasing' if len(prices) > 1 and prices[-1] > prices[0] else ' ↘️ Decreasing' if len(prices) > 1 and prices[-1] < prices[0] else ' ➡️ Stable'}")
        
        print(f"\n📊 INTERVAL DIFFERENCES:")
        print(f"Each interval should have different news content based on the time cutoff.")
        print(f"Check the logs above to see how news articles differ between intervals.")
        
        # Verify we got results
        self.assertGreater(len(results), 0, "Should have at least one interval result")
        # Note: We might get fewer than 3 if the time window is too recent or market data is sparse
        self.assertGreaterEqual(len(results), 1, "Should have at least one interval result")

if __name__ == '__main__':
    unittest.main()

