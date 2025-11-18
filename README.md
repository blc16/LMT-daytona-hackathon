# LLM Market Timeline (LMT)

**A Time-Machine for Prediction Markets.**

LMT simulates how an LLM or AI Agent would have traded a prediction market over a specific historical window. By reconstructing the information environment (odds + news) at 5-minute intervals, it provides a "clean" backtest of AI decision-making, free from future knowledge.

## Features

*   **Time-Travel Simulation:** Reconstructs the exact state of the world at past intervals.
*   **Agentic Decisions:** Uses **Daytona** to execute generated code for rigorous decision logic.
*   **Breaking Point Analysis:** Identifies exactly *when* and *why* the AI changed its mind.
*   **Visual Timeline:** Interactive dashboard comparing Market Odds vs. Model Confidence.

## Tech Stack

*   **Backend:** Python, FastAPI
*   **Frontend:** React, Next.js, Tailwind, Recharts
*   **AI/Agent:** Daytona (Code Execution), OpenAI/Anthropic (LLMs)
*   **Data:** Kalshi (Markets), Exa (Search)

## Getting Started

(Coming soon - see `context/task_list.md` for development plan)

## Project Structure

*   `/backend`: FastAPI orchestrator and agents.
*   `/frontend`: Next.js dashboard.
*   `/experiments`: Local storage for run data.

