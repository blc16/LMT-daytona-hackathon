from datetime import datetime
from typing import List, Dict, Any
import asyncio
from backend.models import ExperimentConfig, IntervalResult, IntervalContext, MarketState, SearchSnippet, AgentDecision, DecisionEnum
from backend.market.polymarket import PolymarketClient
from backend.search.exa import ExaSearchClient
from backend.orchestrator.researcher import Researcher
from backend.orchestrator.trader import TraderAgent
from backend.orchestrator.storage import ExperimentStorage
from backend.llm.client import LLMClient
from backend.daytona.daytona_client import DaytonaClient
from backend.utils.time import generate_intervals
from backend.utils.rate_limit import APIRateLimiters
from backend.orchestrator.progress import progress_tracker
import uuid

class Orchestrator:
    def __init__(self):
        self.market_client = PolymarketClient()
        self.search_client = ExaSearchClient()
        self.llm_client = LLMClient()
        self.daytona_client = DaytonaClient()
        self.researcher = Researcher(self.llm_client)
        self.trader = TraderAgent(self.llm_client, self.daytona_client)
        self.storage = ExperimentStorage()
        self.rate_limiters = APIRateLimiters()

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
        
        intervals = generate_intervals(config.start_time, config.end_time, config.interval_minutes)
        
        print(f"Generated {len(intervals)} intervals.")
        print(f"🚀 Processing {len(intervals)} intervals in parallel with rate limiting...")
        
        # Generate experiment ID upfront for progress tracking
        experiment_id = str(uuid.uuid4())
        await progress_tracker.create(experiment_id, len(intervals))
        
        # Calculate expected API calls for monitoring
        expected_polymarket = len(intervals)
        expected_exa = len(intervals) * 5  # 5 queries per interval
        expected_openrouter = len(intervals) * (1 + config.num_simulations)  # 1 for queries + N for decisions
        expected_daytona = len(intervals) * config.num_simulations
        print(f"📊 Expected API calls:")
        print(f"   - Polymarket: {expected_polymarket} calls (max 10 concurrent)")
        print(f"   - Exa Search: {expected_exa} calls (max 5 concurrent, 15/min)")
        print(f"   - OpenRouter: {expected_openrouter} calls (max 10 concurrent)")
        print(f"   - Daytona: {expected_daytona} calls (max 2 concurrent - reduced to avoid disk limits)")
        print(f"⏱️  Estimated time: ~{max(expected_exa // 10 * 2, expected_daytona // 2 * 3) // 60} minutes")
        
        # Track progress with shared counter
        import time
        start_time = time.time()
        total_intervals = len(intervals)
        completed_counter = {"count": 0}  # Use dict to allow mutation in closures
        failed_counter = {"count": 0}
        
        # Process all intervals in parallel
        tasks = [
            self._process_interval(
                interval_time=interval_time,
                token_id=token_id,
                market_metadata=market_metadata,
                config=config,
                interval_index=idx,
                total_intervals=total_intervals,
                progress_counter=completed_counter,
                failed_counter=failed_counter,
                start_time=start_time,
                progress_id=experiment_id
            )
            for idx, interval_time in enumerate(intervals)
        ]
        
        try:
            # Wait for all intervals to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            elapsed = time.time() - start_time
            print(f"\n⏱️  Total execution time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
            
            # Filter out exceptions and sort by timestamp
            valid_results = []
            failed_intervals = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"\n❌ Interval {i+1} failed with error: {result}")
                    import traceback
                    traceback.print_exc()
                    failed_intervals.append(i + 1)
                else:
                    valid_results.append(result)
            
            # Sort by timestamp to ensure correct order
            valid_results.sort(key=lambda r: r.timestamp)
            
            print(f"\n✅ Processed {len(valid_results)}/{len(intervals)} intervals successfully")
            if failed_intervals:
                print(f"⚠️  Failed intervals: {failed_intervals}")
            
            # Ensure we have at least some results
            if not valid_results:
                await progress_tracker.finish(experiment_id, success=False, error="All intervals failed")
                raise ValueError(f"All {len(intervals)} intervals failed. Cannot save experiment.")
            
            # Save experiment results
            try:
                self.storage.save_experiment(config, valid_results, experiment_id)
                await progress_tracker.finish(experiment_id, success=True)
                print(f"\n✅ Experiment completed! Saved with ID: {experiment_id}")
                return experiment_id
            except Exception as e:
                import traceback
                print(f"\n❌ Failed to save experiment: {e}")
                traceback.print_exc()
                await progress_tracker.finish(experiment_id, success=False, error=str(e))
                raise
        except Exception as e:
            await progress_tracker.finish(experiment_id, success=False, error=str(e))
            raise
    
    async def _process_interval(
        self,
        interval_time: datetime,
        token_id: str,
        market_metadata: Dict[str, Any],
        config: ExperimentConfig,
        interval_index: int,
        total_intervals: int,
        progress_counter: Dict[str, int],
        failed_counter: Dict[str, int],
        start_time: float,
        progress_id: str
    ) -> IntervalResult:
        """Process a single interval with rate limiting."""
        print(f"\n[Interval {interval_index + 1}/{total_intervals}] Processing {interval_time}...")
        
        try:
            # A. Get Market State at T - with rate limiting
            async with self.rate_limiters.polymarket:
                print(f"  [Interval {interval_index + 1}] Fetching market price...")
                price = await self.market_client.get_price_at(token_id, interval_time, config.interval_minutes)
                print(f"  ✅ [Interval {interval_index + 1}] Market Price: {price:.2%}")
            
            market_state = MarketState(timestamp=interval_time, price=price)
            
            # B. Researcher Agent: Generate Queries - with rate limiting
            async with self.rate_limiters.openrouter:
                queries = await self.researcher.generate_queries(
                    market_info=market_metadata,
                    current_price=price,
                    timestamp=interval_time,
                    model=config.model_provider
                )
                print(f"  [Interval {interval_index + 1}] Generated {len(queries)} queries")
            
            # C. Execute Search - parallelize queries with rate limiting
            search_tasks = []
            for query in queries:
                async def search_with_limit(q: str):
                    async with self.rate_limiters.exa:
                        return await self.search_client.search(q, interval_time, limit=2)
                search_tasks.append(search_with_limit(query))
            
            search_results_lists = await asyncio.gather(*search_tasks, return_exceptions=True)
            search_results: List[SearchSnippet] = []
            for result in search_results_lists:
                if isinstance(result, Exception):
                    print(f"  ⚠️  [Interval {interval_index + 1}] Search query failed: {result}")
                else:
                    search_results.extend(result)
            
            # Filter out snippets published after the interval cutoff
            filtered_results = []
            for snippet in search_results:
                if snippet.published_date:
                    try:
                        pub_date = datetime.fromisoformat(snippet.published_date.replace("Z", "+00:00"))
                        if pub_date <= interval_time:
                            filtered_results.append(snippet)
                    except (ValueError, AttributeError):
                        pass
            
            # Deduplicate by URL
            unique_results = list({s.url: s for s in filtered_results}.values())
            print(f"  [Interval {interval_index + 1}] Found {len(unique_results)} unique news articles")
            
            # D. Build Context (recent_history will be empty for parallel processing, but that's OK)
            context = IntervalContext(
                time=interval_time,
                market_info=market_metadata,
                current_market_state=market_state,
                news=unique_results,
                recent_history=[]  # Can't easily get this in parallel, but it's optional
            )
            
            # E. Trader Agent: Make Decisions - with rate limiting
            # Note: Trader uses both OpenRouter (for LLM) and Daytona (for code execution)
            decisions: List[AgentDecision] = []
            for sim_idx in range(config.num_simulations):
                try:
                    # Acquire both rate limiters (nested)
                    async with self.rate_limiters.openrouter:
                        async with self.rate_limiters.daytona:
                            decision = await self.trader.make_decision(
                                context=context,
                                model=config.model_provider,
                                simulation_index=sim_idx,
                                mode=config.mode.value
                            )
                            decisions.append(decision)
                            print(f"  ✅ [Interval {interval_index + 1}] Simulation {sim_idx + 1}: {decision.decision.value} ({decision.confidence:.0%})")
                except Exception as e:
                    print(f"  ❌ [Interval {interval_index + 1}] Simulation {sim_idx + 1} failed: {e}")
            
            # Aggregate decisions
            if decisions:
                yes_count = sum(1 for d in decisions if d.decision == DecisionEnum.YES)
                aggregated_decision = DecisionEnum.YES if yes_count >= len(decisions) - yes_count else DecisionEnum.NO
                aggregated_confidence = sum(d.confidence for d in decisions) / len(decisions)
            else:
                aggregated_decision = DecisionEnum.NO
                aggregated_confidence = 0.0
            
            result = IntervalResult(
                timestamp=interval_time,
                market_state=market_state,
                decisions=decisions,
                aggregated_decision=aggregated_decision,
                aggregated_confidence=aggregated_confidence,
                news=unique_results  # Store the news snippets for evidence display
            )
            
            print(f"  ✅ [Interval {interval_index + 1}] Completed: {aggregated_decision.value} ({aggregated_confidence:.0%})")
            
            # Update progress
            progress_counter["count"] += 1
            completed = progress_counter["count"]
            failed = failed_counter["count"]
            import time
            elapsed = time.time() - start_time
            if completed > 0:
                avg_time_per_interval = elapsed / completed
                remaining = total_intervals - completed - failed
                estimated_remaining = avg_time_per_interval * remaining if remaining > 0 else 0
                print(f"\n📊 Progress: {completed}/{total_intervals} intervals completed ({completed*100//total_intervals}%)")
                if remaining > 0:
                    print(f"   ⏱️  Elapsed: {elapsed:.1f}s | Est. remaining: {estimated_remaining:.1f}s ({estimated_remaining/60:.1f} min)")
            
            # Update progress tracker
            await progress_tracker.update(progress_id, completed, failed)
            
            return result
            
        except Exception as e:
            print(f"  ❌ [Interval {interval_index + 1}] Failed: {e}")
            import traceback
            traceback.print_exc()
            # Update failed counter
            failed_counter["count"] += 1
            failed = failed_counter["count"]
            completed = progress_counter["count"]
            await progress_tracker.update(progress_id, completed, failed)
            raise

