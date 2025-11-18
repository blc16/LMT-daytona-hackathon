# Logging & Monitoring

## 1. Application Logs
*   **Format:** Structured JSON logs preferred for the backend.
*   **Levels:**
    *   `INFO`: Experiment progress, major state changes.
    *   `DEBUG`: Raw API payloads, prompt inputs.
    *   `ERROR`: API failures, Daytona execution crashes.

## 2. Experiment Persistence
*   **Location:** `experiments/{experiment_id}.json` (MVP) or SQLite.
*   **Structure:**
    *   Top-level: Experiment Config & Metadata.
    *   `intervals`: Array of processed intervals.
    *   `decisions`: Array of detailed decision results.

## 3. Audit Trail
*   Every decision must trace back to:
    *   Input Prompt / Context.
    *   Generated Code (for Daytona mode).
    *   Raw Output from Sandbox/LLM.
    *   Used Search Snippets (IDs).

## 4. Progress Tracking
*   **Location:** In-memory (can be persisted to Redis/DB in future).
*   **Module:** `backend/orchestrator/progress.py`
*   **Features:**
    *   Real-time progress tracking for running experiments.
    *   Tracks completed/failed intervals, progress percentage, elapsed time.
    *   Status: `running`, `completed`, `failed`.
    *   API endpoint: `GET /api/experiments/{experiment_id}/progress`
*   **Data Structure:**
    *   `experiment_id`: Unique identifier
    *   `total_intervals`: Total number of intervals
    *   `completed_intervals`: Successfully processed intervals
    *   `failed_intervals`: Failed intervals
    *   `progress_percent`: Percentage complete (0-100)
    *   `status`: Current status
    *   `elapsed_seconds`: Time since start
    *   `error`: Error message if failed

## 5. Rate Limiting
*   **Module:** `backend/utils/rate_limit.py`
*   **Purpose:** Prevent API rate limit violations and manage concurrent requests.
*   **Implementation:** Uses `asyncio.Semaphore` for concurrency control and optional delays.
*   **Configuration:**
    *   **Polymarket:** `max_concurrent=10`, `delay_seconds=0.05`
    *   **Exa Search:** `max_concurrent=10`, `delay_seconds=0.15`
    *   **OpenRouter:** `max_concurrent=10`, `delay_seconds=0.1`
    *   **Daytona:** `max_concurrent=2`, `delay_seconds=0.5` (reduced due to disk limits)
*   **Usage:** Context manager pattern (`async with rate_limiter:`)
*   **Features:**
    *   Automatic semaphore acquisition/release
    *   Configurable delays between requests
    *   Exception-safe (releases semaphore even on errors)
    *   Supports nested usage (e.g., trader needs both OpenRouter and Daytona)

## 6. Evaluation Export
*   **Goal:** Post-hoc analysis in Galileo.
*   **Format:**
    *   `input`: The constructed context/prompt.
    *   `output`: The model's rationale and decision.
    *   `metadata`: Timestamp, model_id, market_odds, decision_mode.

