# LLM Market Timeline (LMT) - Project Description

## Concept
**LLM Market Timeline (LMT)** is a system that simulates how an LLM or AI agent would have traded a specific prediction market over a past time window, given time-sliced information. It reconstructs the "state of the world" at specific intervals, feeds it to an agent (running on Daytona) or an LLM, and records the decision confidence and rationale.

## Core Value Proposition
*   **For Traders/Quants:** Backtest LLM-driven decision rules without future leakage. Understand which news events caused sentiment flips.
*   **For AI Researchers:** Evaluate models on temporal decision processes, stability, and calibration.

## MVP Features
1.  **Market Selection:** Input a Kalshi market ID and binary target (Yes/No).
2.  **Time Slicing:** Break a historical window (e.g., 8:00-10:00) into fixed intervals (e.g., 5 mins).
3.  **Data Reconstruction:** For each interval, fetch historical market odds and time-filtered web search results (via Exa).
4.  **Agentic Decision Making (Daytona):**
    *   **Primary Mode:** The LLM writes Python code to process the context and output a decision. This code is executed in a Daytona sandbox.
    *   **Fallback Mode:** Direct LLM call if the agent fails.
5.  **Output:**
    *   Time series of decisions (YES/NO), confidence, and implied probabilities.
    *   **Breaking Point Analysis:** Identification of moments where the decision flipped, correlated with specific new evidence.
    *   **Rationale:** Detailed explanation for every decision.

## User Flow
1.  **Configure:** User selects market, time range, interval size, models, and simulation settings.
2.  **Run:** The system iterates through time intervals.
    *   At $t_i$, it fetches odds $O_t$ and news $N_{t \le i}$.
    *   Agent receives context and outputs decision $D_i$.
3.  **Analyze:** User views a dashboard showing the probability timeline vs. market odds, clicks on points to see the agent's reasoning, and inspects "breaking points" where sentiment shifted.

## Key Differentiators
*   **Agentic Execution:** Uses Daytona to allow the model to *compute* its decision (e.g., running a mini-algorithm) rather than just *guessing* via text generation.
*   **Detailed Attribution:** Links decision changes directly to specific search snippets or odds changes.

