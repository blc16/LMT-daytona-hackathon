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
        
        # HACK: For the hackathon integration test, let's pick the "December 31" market specifically 
        # if available, or just the first one.
        target_market = None
        for m in market_metadata.get("markets", []):
            # Look for a matching question or just take the first
            target_market = m
            break
            
        if not target_market:
            raise ValueError("No markets found for event")
            
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
            price = 0.5 # Default
            if token_id:
                price = await self.market_client.get_price_at(token_id, interval_time)
            
            market_state = MarketState(timestamp=interval_time, price=price)
            
            # B. Researcher Agent: Generate Queries
            queries = await self.researcher.generate_queries(
                market_info=market_metadata,
                current_price=price,
                timestamp=interval_time,
                model=config.model_provider
            )
            print(f"  Researcher queries: {queries}")
            
            # C. Execute Search
            search_results: List[SearchSnippet] = []
            for query in queries:
                # Rate limit / parallelize here in real prod
                snippets = await self.search_client.search(query, interval_time, limit=2)
                search_results.extend(snippets)
                
            # Deduplicate by URL
            unique_results = {s.url: s for s in search_results}.values()
            
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

