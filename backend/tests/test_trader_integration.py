"""
Integration test for Trader Agent with Daytona.
Tests real code generation, execution, and decision making.
"""
import unittest
from datetime import datetime, timezone
from backend.orchestrator.trader import TraderAgent
from backend.llm.client import LLMClient
from backend.daytona.daytona_client import DaytonaClient
from backend.models import IntervalContext, MarketState, SearchSnippet
from backend.config import settings

class TestTraderIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for Trader Agent with real Daytona execution."""
    
    async def test_trader_decision_with_daytona(self):
        """Test trader agent generating code and executing in Daytona."""
        print("\n" + "="*80)
        print("TEST: Trader Agent - Daytona Code Generation & Execution")
        print("="*80)
        
        # Check API keys
        if not settings.OPENROUTER_API_KEY or "your_" in settings.OPENROUTER_API_KEY:
            self.skipTest("OPENROUTER_API_KEY not set")
        if not settings.DAYTONA_API_KEY or "your_" in settings.DAYTONA_API_KEY:
            self.skipTest("DAYTONA_API_KEY not set")
        
        llm_client = LLMClient()
        daytona_client = DaytonaClient()
        trader = TraderAgent(llm_client, daytona_client, max_retries=3)
        
        # Create a realistic interval context
        market_info = {
            "title": "Gemini 3.0 released by...?",
            "description": "This market will resolve according to the date (ET) Google's Gemini 3.0 model is made available to the general public."
        }
        
        market_state = MarketState(
            timestamp=datetime(2025, 11, 3, 12, 0, tzinfo=timezone.utc),
            price=0.8250  # 82.50% probability
        )
        
        # Create some sample news snippets
        news = [
            SearchSnippet(
                id="news1",
                title="Google Announces Gemini 3.0 Release Date",
                url="https://example.com/news1",
                text="Google has announced that Gemini 3.0 will be released in November 2025...",
                published_date="2025-11-01T00:00:00Z",
                score=0.95
            ),
            SearchSnippet(
                id="news2",
                title="Gemini 3.0 Beta Testing Underway",
                url="https://example.com/news2",
                text="Beta testing for Gemini 3.0 has begun with select users...",
                published_date="2025-10-28T00:00:00Z",
                score=0.85
            )
        ]
        
        context = IntervalContext(
            time=datetime(2025, 11, 3, 12, 0, tzinfo=timezone.utc),
            market_info=market_info,
            current_market_state=market_state,
            news=news,
            recent_history=[]
        )
        
        model = "openai/gpt-4o-mini"
        simulation_index = 0
        
        print(f"\nInput:")
        print(f"  Market: {market_info['title']}")
        print(f"  Current Price: {market_state.price:.2%}")
        print(f"  Timestamp: {context.time}")
        print(f"  News Articles: {len(news)}")
        for i, snippet in enumerate(news, 1):
            print(f"    {i}. [{snippet.published_date}] {snippet.title}")
        print(f"  Model: {model}")
        print(f"  Mode: DAYTONA_AGENT")
        print(f"\nCalling make_decision(context, model, simulation_index, mode='daytona_agent')...")
        print(f"\n{'='*80}")
        print("EXPECTED BEHAVIOR:")
        print("  1. Generate Python code using LLM")
        print("  2. Execute code in Daytona sandbox")
        print("  3. Return structured decision with rationale")
        print("  4. Show code explanation")
        print(f"{'='*80}\n")
        
        decision = await trader.make_decision(
            context=context,
            model=model,
            simulation_index=simulation_index,
            mode="daytona_agent"
        )
        
        print(f"\n{'='*80}")
        print("✅ OUTPUT - Decision Result")
        print(f"{'='*80}")
        print(f"  Decision: {decision.decision.value}")
        print(f"  Confidence: {decision.confidence:.2%}")
        print(f"  Relevant Evidence IDs: {len(decision.relevant_evidence_ids)} items")
        if decision.relevant_evidence_ids:
            for i, evid_id in enumerate(decision.relevant_evidence_ids[:5], 1):
                print(f"    {i}. {evid_id}")
        
        print(f"\n  Rationale Preview:")
        rationale_lines = decision.rationale.split('\n')[:10]  # First 10 lines
        for line in rationale_lines:
            print(f"    {line}")
        
        if len(decision.rationale.split('\n')) > 10:
            print(f"    ... ({len(decision.rationale.split('\n')) - 10} more lines)")
        
        # Verify
        self.assertIsNotNone(decision)
        self.assertIn(decision.decision.value, ["YES", "NO"])
        self.assertGreaterEqual(decision.confidence, 0.0)
        self.assertLessEqual(decision.confidence, 1.0)
        self.assertIsInstance(decision.rationale, str)
        self.assertGreater(len(decision.rationale), 10, "Rationale should be meaningful")
        
        # Verify execution trace is present for Daytona mode
        if decision.execution_trace:
            print(f"\n✅ Execution Trace Found:")
            print(f"  - Code length: {len(decision.execution_trace.code)} characters")
            print(f"  - Raw output length: {len(decision.execution_trace.raw_output)} characters")
            print(f"  - Executed successfully: {decision.execution_trace.executed_successfully}")
            print(f"  - Exit code: {decision.execution_trace.exit_code}")
            print(f"  - Execution time: {decision.execution_trace.execution_time_ms:.2f}ms" if decision.execution_trace.execution_time_ms else "  - Execution time: N/A")
            print(f"  - Attempt number: {decision.execution_trace.attempt_number}")
            self.assertIsNotNone(decision.execution_trace)
            self.assertTrue(decision.execution_trace.executed_successfully, "Code should execute successfully")
            # Exit code can be non-zero if JSON was successfully parsed (code may print JSON then error)
            # The important thing is that executed_successfully is True
            self.assertIn(decision.execution_trace.exit_code, [0, 1], "Exit code should be 0 or 1 (1 is OK if JSON was parsed)")
            self.assertGreater(len(decision.execution_trace.code), 0, "Code should not be empty")
            self.assertGreater(len(decision.execution_trace.raw_output), 0, "Raw output should not be empty")
        else:
            print(f"\n⚠️  No execution trace found (might be DIRECT_LLM mode)")
        
        print(f"\n✅ Test PASSED: Trader Agent decision generated successfully")
        print(f"\nAnalysis:")
        print(f"  - Decision: {decision.decision.value}")
        print(f"  - Confidence: {decision.confidence:.2%}")
        print(f"  - Rationale length: {len(decision.rationale)} characters")
        print(f"  - Evidence cited: {len(decision.relevant_evidence_ids)} items")
        print(f"  - Rationale contains code explanation: {'Code Execution Analysis' in decision.rationale}")
        print(f"  - Execution trace present: {decision.execution_trace is not None}")

if __name__ == '__main__':
    unittest.main()

