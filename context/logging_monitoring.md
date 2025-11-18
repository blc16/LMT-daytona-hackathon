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

## 4. Evaluation Export
*   **Goal:** Post-hoc analysis in Galileo.
*   **Format:**
    *   `input`: The constructed context/prompt.
    *   `output`: The model's rationale and decision.
    *   `metadata`: Timestamp, model_id, market_odds, decision_mode.

