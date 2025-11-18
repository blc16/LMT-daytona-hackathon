# UI Specification

## 1. Run Experiment Page (`/`)
**Goal:** Configure and start a backtest simulation.

### Components
*   **Market Input:**
    *   Text field for Market ID (e.g., `KALSHI:INFLATION...`).
    *   "Fetch Info" button to validate and show Market Description/Expiry.
*   **Time Configuration:**
    *   Start Time & End Time pickers.
    *   Interval (minutes) number input.
*   **Simulation Settings:**
    *   Num Simulations per interval (default: 1).
    *   Model Selector (Multi-select: GPT-4o, Claude 3.5, etc.).
    *   Mode Toggle: **Daytona Agent (Default)** vs Direct LLM.
*   **Action:**
    *   "Run Experiment" button.
    *   Progress Bar during execution (showing processed intervals).
    *   Log stream (e.g., "08:00 processed...").

## 2. Experiment Results Page (`/experiment/:id`)
**Goal:** Visualize the timeline, compare model vs. market, and drill down into reasoning.

### Layout
*   **Header:** Experiment Metadata (Market, Time range, Status).
*   **Main Content (Left/Center):**
    *   **Timeline Chart:**
        *   X-Axis: Time.
        *   Y-Axis: Probability (0-1).
        *   Series 1: Market Odds (Reference).
        *   Series 2: Model Aggregated Probability.
        *   **Interactivity:** Clickable points/markers for each interval. Color-coded (Green=Yes, Red=No).
        *   **Annotations:** Vertical lines for "Breaking Points" (major sentiment shifts).
*   **Drill-Down Panel (Right Sidebar):**
    *   *Triggered by clicking a chart point.*
    *   **Header:** Interval Time, Aggregated Decision.
    *   **Reasoning Tab:**
        *   List of models/sims.
        *   For each: Decision, Confidence, **Rationale Summary** (3 bullets).
        *   Expandable "Full Rationale".
        *   Badge: "Daytona" or "Fallback".
    *   **Evidence Tab:**
        *   List of `SearchSnippet`s cited in `key_evidence_ids`.
        *   Highlight "New" evidence (appeared in this interval vs previous).
*   **Summary Cards (Top):**
    *   **Current Recommendation:** Final decision + confidence.
    *   **Edge:** Difference between Model Prob and Market Odds.

## 3. Comparison/History (Optional)
*   List of past experiments.
*   Ability to overlay multiple experiment runs on the same chart (stretch).

