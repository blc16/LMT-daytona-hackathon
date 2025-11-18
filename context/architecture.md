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

6.  **Frontend / UI**
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
1.  **Fetch:** Get Odds at $t$, Search News where $time \le t$.
2.  **Prepare Context:** specific to the current interval.
3.  **Agent Loop:**
    *   Send Context + Task to LLM -> Get Code.
    *   Send Code + Context to Daytona -> Get JSON Result.
    *   *On Error:* Fallback to Direct LLM Prompt -> Get JSON Result.
4.  **Aggregate:** Vote/Average across simulations/models.
5.  **Store:** Save `IntervalData`.

