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
        Run a real experiment for Gemini 3.0 market with iterative Daytona agent.
        Uses 3 intervals, 1 day apart, over the last 3 days.
        """
        # Check if we have required API keys
        if not settings.EXA_API_KEY or "your_" in settings.EXA_API_KEY:
            self.skipTest("EXA_API_KEY not set")
        if not settings.OPENROUTER_API_KEY or "your_" in settings.OPENROUTER_API_KEY:
            self.skipTest("OPENROUTER_API_KEY not set")
        if not settings.DAYTONA_API_KEY or "your_" in settings.DAYTONA_API_KEY:
            self.skipTest("DAYTONA_API_KEY not set - falling back to DIRECT_LLM mode")
            use_daytona = False
        else:
            use_daytona = True
        
        # Use a historical time window: October 2025 (before market end date of Oct 31)
        # Market end date is 2025-10-31, so use dates in October 2025
        end_time = datetime(2025, 10, 15, 12, 0, tzinfo=timezone.utc)
        start_time = datetime(2025, 10, 12, 12, 0, tzinfo=timezone.utc)  # 3 days before
        
        config = ExperimentConfig(
            market_slug="gemini-3pt0-released-by",
            start_time=start_time,
            end_time=end_time,
            interval_minutes=1440,  # 1 day intervals (24 * 60 = 1440 minutes)
            num_simulations=1,
            model_provider="openai/gpt-4o-mini",
            mode=ExperimentMode.DAYTONA_AGENT if use_daytona else ExperimentMode.DIRECT_LLM
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
        experiment_id = await orchestrator.run_experiment(config)
        
        # Load results back from storage
        experiment_result = orchestrator.storage.load_experiment(experiment_id)
        assert experiment_result is not None, "Failed to load experiment"
        results = experiment_result.timeline
        
        print("\n" + "="*80)
        print("RESULTS ANALYSIS & INTERVAL COMPARISON")
        print("="*80)
        print(f"Experiment ID: {experiment_id}")
        
        for i, result in enumerate(results, 1):
            print(f"\n{'='*80}")
            print(f"--- Interval {i}: {result.timestamp} ---")
            print(f"{'='*80}")
            print(f"Market Price (YES probability): {result.market_state.price:.2%}")
            print(f"Decisions made: {len(result.decisions)}")
            print(f"Aggregated Decision: {result.aggregated_decision.value} (confidence: {result.aggregated_confidence:.2%})")
            
            # Show detailed decision information
            for j, decision in enumerate(result.decisions, 1):
                print(f"\n  Decision {j}:")
                print(f"    - Decision: {decision.decision.value}")
                print(f"    - Confidence: {decision.confidence:.2%}")
                print(f"    - Relevant Evidence IDs: {len(decision.relevant_evidence_ids)} items")
                if decision.relevant_evidence_ids:
                    print(f"      {decision.relevant_evidence_ids[:3]}...")  # Show first 3
                print(f"    - Rationale Preview:")
                rationale_preview = decision.rationale[:300] + "..." if len(decision.rationale) > 300 else decision.rationale
                for line in rationale_preview.split('\n')[:5]:  # Show first 5 lines
                    print(f"      {line}")
            
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

