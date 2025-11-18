from datetime import datetime
from typing import List, Dict, Any
from backend.models import ExperimentConfig, IntervalResult, IntervalContext, MarketState, SearchSnippet, AgentDecision, DecisionEnum
from backend.market.polymarket import PolymarketClient
from backend.search.exa import ExaSearchClient
from backend.orchestrator.researcher import Researcher
from backend.orchestrator.trader import TraderAgent
from backend.orchestrator.storage import ExperimentStorage
from backend.llm.client import LLMClient
from backend.daytona.daytona_client import DaytonaClient
from backend.utils.time import generate_intervals

class Orchestrator:
    def __init__(self):
        self.market_client = PolymarketClient()
        self.search_client = ExaSearchClient()
        self.llm_client = LLMClient()
        self.daytona_client = DaytonaClient()
        self.researcher = Researcher(self.llm_client)
        self.trader = TraderAgent(self.llm_client, self.daytona_client)
        self.storage = ExperimentStorage()

    async def run_experiment(self, config: ExperimentConfig) -> str:
        """
        Main loop: Fetch Data -> Research -> Build Context -> (Stub) Decision.
        """
        print(f"Starting experiment for {config.market_slug}...")
        
        # 1. Fetch Static Market Metadata
        market_metadata = await self.market_client.get_market_metadata(config.market_slug)
        
        # Print market description
        market_title = market_metadata.get("title", "Unknown Market")
        market_description = market_metadata.get("description", "No description available")
        print(f"\n{'='*80}")
        print(f"MARKET INFORMATION")
        print(f"{'='*80}")
        print(f"Title: {market_title}")
        print(f"Description: {market_description[:200]}..." if len(market_description) > 200 else f"Description: {market_description}")
        print(f"{'='*80}\n")
        # Assuming single market/outcome for MVP, grab the first one or find specific one if needed.
        # For "Gemini 3.0 released by...?", there are multiple markets (Nov, Dec, etc).
        # We need to pick one. Let's grab the one that matches the end date or just the first for now.
        # Ideally config has `market_id` but we switched to slug. 
        # Let's assume the first market in the list is the main target for now or we filter by config.
        
        # Select market: prefer open markets, then most recent month
        markets = market_metadata.get("markets", [])
        if not markets:
            raise ValueError("No markets found for event")
            
        # Select November market specifically (user requirement)
        november_markets = [m for m in markets if "november" in m.get("question", "").lower()]
        if november_markets:
            # Prefer open markets, then most recent
            open_november = [m for m in november_markets if m.get("active") and not m.get("closed")]
            if open_november:
                open_november.sort(key=lambda m: m.get("endDateIso", ""), reverse=True)
                target_market = open_november[0]
            else:
                november_markets.sort(key=lambda m: m.get("endDateIso", ""), reverse=True)
                target_market = november_markets[0]
        else:
            # Fallback: try to find an open market
            open_markets = [m for m in markets if m.get("active") and not m.get("closed")]
            if open_markets:
                # Sort by end date (most recent first)
                open_markets.sort(key=lambda m: m.get("endDateIso", ""), reverse=True)
                target_market = open_markets[0]
            else:
                # No open markets, pick the most recent closed one
                markets.sort(key=lambda m: m.get("endDateIso", ""), reverse=True)
                target_market = markets[0]
            
        # We need the CLOB Token ID for price history
        # Polymarket Gamma API returns 'clobTokenIds' - could be a list or JSON string
        import json
        clob_ids_raw = target_market.get("clobTokenIds", [])
        
        # Handle both list and string formats
        if isinstance(clob_ids_raw, str):
            try:
                clob_ids = json.loads(clob_ids_raw)
            except json.JSONDecodeError:
                # Might be a single token ID string
                token_id = clob_ids_raw if clob_ids_raw else None
            else:
                token_id = clob_ids[0] if clob_ids else None
        elif isinstance(clob_ids_raw, list):
            token_id = clob_ids_raw[0] if clob_ids_raw else None
        else:
            token_id = None
            
        if not token_id:
            raise ValueError(f"Could not parse CLOB Token ID from market. Market data: {target_market.get('clobTokenIds', 'N/A')}")
        
        print(f"Selected market: {target_market.get('question', 'Unknown')}")
        print(f"Market end date: {target_market.get('endDateIso', 'Unknown')}")
        print(f"CLOB Token ID: {token_id}")
        
        results = []
        intervals = generate_intervals(config.start_time, config.end_time, config.interval_minutes)
        
        print(f"Generated {len(intervals)} intervals.")

        for interval_time in intervals:
            print(f"\n{'='*80}")
            print(f"Processing interval: {interval_time}...")
            print(f"{'='*80}")
            
            # A. Get Market State at T - FAIL HARD if this doesn't work
            print(f"  Fetching market price at {interval_time}...")
            price = await self.market_client.get_price_at(token_id, interval_time, config.interval_minutes)
            print(f"  ✅ Market Price (YES probability): {price:.2%}")
            
            market_state = MarketState(timestamp=interval_time, price=price)
            
            # B. Researcher Agent: Generate Queries
            queries = await self.researcher.generate_queries(
                market_info=market_metadata,
                current_price=price,
                timestamp=interval_time,
                model=config.model_provider
            )
            print(f"  Researcher generated {len(queries)} queries:")
            for i, q in enumerate(queries, 1):
                print(f"    {i}. {q}")
            
            # C. Execute Search
            search_results: List[SearchSnippet] = []
            for query in queries:
                # Rate limit / parallelize here in real prod
                snippets = await self.search_client.search(query, interval_time, limit=2)
                search_results.extend(snippets)
                print(f"    Query '{query[:50]}...' returned {len(snippets)} snippets")
            
            # Filter out snippets published after the interval cutoff (defense in depth)
            filtered_results = []
            for snippet in search_results:
                if snippet.published_date:
                    try:
                        # Parse the published date
                        pub_date = datetime.fromisoformat(snippet.published_date.replace("Z", "+00:00"))
                        if pub_date <= interval_time:
                            filtered_results.append(snippet)
                    except (ValueError, AttributeError):
                        # If we can't parse the date, exclude it to be safe
                        pass
                else:
                    # No published date, exclude to be safe
                    pass
            
            print(f"  After filtering: {len(filtered_results)} snippets (from {len(search_results)} total)")
            
            # Show details of filtered snippets
            if filtered_results:
                print(f"  Filtered snippets that passed time check:")
                for i, snippet in enumerate(filtered_results[:5], 1):  # Show first 5
                    print(f"    {i}. [{snippet.published_date}] {snippet.title[:60]}...")
                    print(f"       URL: {snippet.url}")
                    print(f"       Text preview: {snippet.text[:100]}...")
                
            # Show what was filtered out
            filtered_out = len(search_results) - len(filtered_results)
            if filtered_out > 0:
                print(f"  ⚠️  {filtered_out} snippets were filtered out (published after {interval_time})")
                
            # Deduplicate by URL
            unique_results = {s.url: s for s in filtered_results}.values()
            final_news_list = list(unique_results)
            final_news_count = len(final_news_list)
            print(f"  After deduplication: {final_news_count} unique news articles")
            
            # Show final news that will be used
            if final_news_list:
                print(f"  Final news articles for this interval:")
                for i, snippet in enumerate(final_news_list, 1):
                    print(f"    {i}. [{snippet.published_date}] {snippet.title}")
                    print(f"       Score: {snippet.score:.2f}")
            
            # D. Build Context
            context = IntervalContext(
                time=interval_time,
                market_info=market_metadata,
                current_market_state=market_state,
                news=list(unique_results),
                recent_history=[r.market_state for r in results[-24:]] if results else []  # Last 24 intervals for trend
            )
            
            # E. Trader Agent: Make Decisions
            print(f"\n  {'='*76}")
            print(f"  TRADER AGENT: Making Decisions (Mode: {config.mode.value})")
            print(f"  {'='*76}")
            decisions: List[AgentDecision] = []
            for sim_idx in range(config.num_simulations):
                print(f"\n  Running simulation {sim_idx + 1}/{config.num_simulations}...")
                try:
                    decision = await self.trader.make_decision(
                        context=context,
                        model=config.model_provider,
                        simulation_index=sim_idx,
                        mode=config.mode.value
                    )
                    decisions.append(decision)
                    print(f"\n  ✅ Simulation {sim_idx + 1} completed:")
                    print(f"     Decision: {decision.decision.value}")
                    print(f"     Confidence: {decision.confidence:.2%}")
                    print(f"     Relevant Evidence: {len(decision.relevant_evidence_ids)} items")
                    if decision.rationale:
                        rationale_preview = decision.rationale[:200] + "..." if len(decision.rationale) > 200 else decision.rationale
                        print(f"     Rationale Preview: {rationale_preview.split(chr(10))[0]}")
                except Exception as e:
                    import traceback
                    print(f"  ❌ Simulation {sim_idx + 1} failed: {e}")
                    print(f"     Traceback: {traceback.format_exc()}")
                    # Continue with other simulations
            
            # Aggregate decisions
            if decisions:
                yes_count = sum(1 for d in decisions if d.decision == DecisionEnum.YES)
                no_count = len(decisions) - yes_count
                aggregated_decision = DecisionEnum.YES if yes_count >= no_count else DecisionEnum.NO
                aggregated_confidence = sum(d.confidence for d in decisions) / len(decisions)
            else:
                aggregated_decision = DecisionEnum.NO
                aggregated_confidence = 0.0
            
            result = IntervalResult(
                timestamp=interval_time,
                market_state=market_state,
                decisions=decisions,
                aggregated_decision=aggregated_decision,
                aggregated_confidence=aggregated_confidence
            )
            results.append(result)
        
        # Save experiment results
        experiment_id = self.storage.save_experiment(config, results)
        print(f"\n✅ Experiment completed! Saved with ID: {experiment_id}")
        
        return experiment_id

