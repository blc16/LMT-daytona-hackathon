# System Architecture

## High-Level Components

1.  **Orchestrator / Controller**
    *   Manages the experiment loop (iterating through time intervals).
    *   Coordinates data fetching, agent execution, and result storage.

2.  **Market Data Module**
    *   **Source:** Kalshi API.
    *   **Responsibilities:** Fetch market metadata, historical odds time series.
    *   **Key Functions:** `get_market_metadata(id)`, `get_odds_at(id, time)`.

3.  **Search Module**
    *   **Source:** Exa API.
    *   **Responsibilities:** Fetch news/web content filtered by timestamp (strictly `<= current_interval_time`).
    *   **Key Functions:** `search(query, time_upper_bound, limit)`.

4.  **Decision Engine (The Core)**
    *   **Modes:**
        *   **Daytona Agent (Default):** Orchestrator constructs a context JSON. LLM generates Python code to process this context. Daytona executes the code to return a `DecisionResult`.
        *   **Direct LLM (Fallback):** Standard prompt-response if Daytona execution fails.
    *   **Inputs:** Market info, Current Odds, Search Snippets, Previous Decisions.
    *   **Outputs:** JSON structured decision (YES/NO, confidence, probability, rationale, evidence_ids).

5.  **Persistence & Logging**
    *   **Storage:** JSON files (per experiment) or SQLite.
    *   **Exports:** Galileo-compatible format for evaluation.

6.  **Progress Tracking**
    *   **Module:** `backend/orchestrator/progress.py`
    *   **Purpose:** Real-time progress tracking for long-running experiments.
    *   **Storage:** In-memory (can be persisted to Redis/DB).
    *   **Features:** Tracks completed/failed intervals, progress percentage, elapsed time, status.
    *   **API:** `GET /api/experiments/{experiment_id}/progress`

7.  **Rate Limiting**
    *   **Module:** `backend/utils/rate_limit.py`
    *   **Purpose:** Prevent API rate limit violations and manage concurrent requests.
    *   **Implementation:** Uses `asyncio.Semaphore` for concurrency control.
    *   **APIs Managed:** Polymarket, Exa Search, OpenRouter, Daytona.
    *   **Features:** Configurable concurrency limits and delays per API.

8.  **Frontend / UI**
    *   **Stack:** React / Next.js + Tailwind + Recharts.
    *   **API:** Python (FastAPI).

## Data Models

### ExperimentConfig
```typescript
{
  market_id: string;
  start_time: string; // ISO
  end_time: string;   // ISO
  interval_minutes: number;
  num_sims: number;
  models: string[];
  mode: "daytona_agent" | "direct_llm" | "hybrid";
  search_config: {
    max_results: number;
    query_mode: "template" | "llm_generated";
  }
}
```

### IntervalContext (Input to Agent)
```json
{
  "time": "2023-10-27T10:00:00Z",
  "market": {
    "id": "KALSHI:...",
    "description": "...",
    "odds": 0.61
  },
  "search_snippets": [
    { "id": "1", "text": "...", "timestamp": "..." }
  ],
  "previous_intervals": [
    { "time": "...", "aggregated_probability": 0.55 }
  ]
}
```

### DecisionResult (Output from Agent)
```typescript
{
  model_id: string;
  simulation_index: number;
  mode: "daytona_agent" | "direct_llm";
  decision: "YES" | "NO";
  confidence: number;        // 0-1
  probability: number;       // 0-1
  rationale: string;
  key_evidence_ids: string[];
  created_at: string;
}
```

## Execution Flow (Per Interval)
1.  **Initialize Progress:** Create progress tracker for experiment.
2.  **Fetch (with Rate Limiting):** Get Odds at $t$, Search News where $time \le t$.
3.  **Prepare Context:** specific to the current interval.
4.  **Agent Loop (with Rate Limiting):**
    *   Send Context + Task to LLM -> Get Code.
    *   Send Code + Context to Daytona -> Get JSON Result.
    *   *On Error:* Fallback to Direct LLM Prompt -> Get JSON Result.
5.  **Update Progress:** Track completion/failure of interval.
6.  **Aggregate:** Vote/Average across simulations/models.
7.  **Store:** Save `IntervalData`.
8.  **Finish Progress:** Mark experiment as completed/failed.

## Rate Limiting Strategy
*   **Parallel Processing:** All intervals processed concurrently with rate limiting.
*   **Per-API Limits:** Each API has its own rate limiter with appropriate concurrency and delays.
*   **Nested Usage:** Trader agent uses both OpenRouter and Daytona limiters (nested context managers).
*   **Exception Safety:** Rate limiters release semaphores even on exceptions.

