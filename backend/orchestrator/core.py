from datetime import datetime
from typing import List, Dict, Any
from backend.models import ExperimentConfig, IntervalResult, IntervalContext, MarketState, SearchSnippet
from backend.market.polymarket import PolymarketClient
from backend.search.exa import ExaSearchClient
from backend.orchestrator.researcher import Researcher
from backend.llm.client import LLMClient
from backend.utils.time import generate_intervals

class Orchestrator:
    def __init__(self):
        self.market_client = PolymarketClient()
        self.search_client = ExaSearchClient()
        self.llm_client = LLMClient()
        self.researcher = Researcher(self.llm_client)

    async def run_experiment(self, config: ExperimentConfig) -> List[IntervalResult]:
        """
        Main loop: Fetch Data -> Research -> Build Context -> (Stub) Decision.
        """
        print(f"Starting experiment for {config.market_slug}...")
        
        # 1. Fetch Static Market Metadata
        market_metadata = await self.market_client.get_market_metadata(config.market_slug)
        # Assuming single market/outcome for MVP, grab the first one or find specific one if needed.
        # For "Gemini 3.0 released by...?", there are multiple markets (Nov, Dec, etc).
        # We need to pick one. Let's grab the one that matches the end date or just the first for now.
        # Ideally config has `market_id` but we switched to slug. 
        # Let's assume the first market in the list is the main target for now or we filter by config.
        
        # Select market: prefer open markets, then most recent month
        markets = market_metadata.get("markets", [])
        if not markets:
            raise ValueError("No markets found for event")
            
        # First, try to find an open market
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
        # Polymarket Gamma API usually returns 'clobTokenIds' string array in the market object.
        # It might be a string representation of a list: '["123", "456"]'
        import json
        clob_ids_str = target_market.get("clobTokenIds", "[]")
        try:
            clob_ids = json.loads(clob_ids_str)
            # Yes ID is usually index 0 or 1 depending on outcomePrices order. 
            # Let's assume index 0 is YES or we check outcome labels. 
            # For simplified MVP, let's take ID 0.
            token_id = clob_ids[0] if clob_ids else None
        except:
            token_id = None
            
        if not token_id:
            print("Warning: Could not parse CLOB Token ID, skipping history.")
            
        results = []
        intervals = generate_intervals(config.start_time, config.end_time, config.interval_minutes)
        
        print(f"Generated {len(intervals)} intervals.")

        for interval_time in intervals:
            print(f"Processing interval: {interval_time}...")
            
            # A. Get Market State at T
            price = 0.5 # Default fallback
            if token_id:
                try:
                    price = await self.market_client.get_price_at(token_id, interval_time, config.interval_minutes)
                except Exception as e:
                    print(f"  Warning: Could not fetch price at {interval_time}: {e}")
                    # Use default price
            
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
                news=list(unique_results)
            )
            
            # E. (Stub) Decision - To be implemented with Daytona
            # For now, just record the context gathered
            
            result = IntervalResult(
                timestamp=interval_time,
                market_state=market_state,
                decisions=[], # No decisions yet
                aggregated_decision="YES", # Placeholder
                aggregated_confidence=0.0
            )
            results.append(result)
            
        return results

