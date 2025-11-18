# Testing Strategy

## 1. Unit Tests
*   **Clients:**
    *   `MarketClient`: Mock Kalshi API responses. Test `get_odds_at` logic (interpolation/nearest tick).
    *   `SearchClient`: Mock Exa API. Test time filtering logic.
    *   `DaytonaClient`: Mock the sandbox execution. Test timeout handling and error parsing.
*   **Utils:**
    *   `generate_intervals`: Ensure correct start/end handling and interval slicing.

## 2. Integration Tests
*   **Orchestrator Loop:**
    *   Run a "dry run" with mocked clients but real orchestrator logic.
    *   Verify that `IntervalData` is constructed correctly and passed to the decision engine.
    *   Verify that fallback logic works (simulate Daytona failure -> check for Direct LLM call).

## 3. End-to-End (E2E) Tests
*   **Full Flow:**
    *   Run a short experiment (e.g., 3 intervals) with a "Dummy" model (no real LLM cost) to verify the pipeline from Input -> Processing -> Storage -> Output.

## 4. Evaluation (Data Quality)
*   **Galileo Export:**
    *   Verify the JSON/JSONL export format matches Galileo's ingestion schema.
    *   Check that all prompts and responses are logged.

## 5. UI Testing
*   **Component Tests:**
    *   Check Chart rendering with empty/partial data.
    *   Verify "Breaking Point" logic highlights the correct intervals.

