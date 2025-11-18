# Task List

This project is divided into 4 Phases. Tasks within a phase can often be done in parallel by the frontend and backend "devs".

**Priority Legend:**
*   `[P0]` Critical MVP
*   `[P1]` Important Feature
*   `[P2]` Nice to have / Polish

## Phase 0: Project Setup (0.5 Days)
- [x] [P0] **Repo Setup**: Initialize Monorepo structure (backend/frontend folders). @Team
- [x] [P0] **Backend Init**: Set up Python/FastAPI project, virtualenv, and basic folder structure (`orchestrator`, `market`, `search`, `llm`). @Backend
- [x] [P0] **Frontend Init**: Set up Next.js + Tailwind project. @Frontend
- [x] [P0] **Config & Secrets**: Create `.env.template` and config loader for API keys (Kalshi, Exa, LLM, Daytona). @Backend
- [x] [P0] **Interfaces**: Define `MarketClient`, `SearchClient`, `DaytonaClient` abstract base classes/Protocols. @Backend

## Phase 1: Core Backend & UI Skeleton (Day 1)
### Backend
- [x] [P0] **Time Slicing**: Implement `generate_intervals` utility.
- [x] [P0] **Market Client**: Implement `PolymarketClient` (fetch metadata from Gamma, history from CLOB). *Replaced Kalshi due to data access limits.*
- [ ] [P0] **Search Client**: Implement `ExaClient` with time filtering (`<= interval_time`).
- [ ] [P0] **Data Models**: Define Pydantic models for `ExperimentConfig`, `IntervalView`, `DecisionResult`.
- [ ] [P0] **API Skeleton**: Create FastAPI endpoints (`POST /run`, `GET /experiment/:id`).

### Frontend (Parallel)
- [ ] [P0] **Scaffold Pages**: Create `/run` and `/experiment/[id]` routes.
- [ ] [P0] **Configuration Form**: Build the input form (Market ID, Time Range, Models). Connect to mock API.
- [ ] [P0] **Layout**: Build the basic shell (Header, Sidebar placeholders).

## Phase 2: Orchestration, Daytona & Real Visualization (Day 2)
### Backend
- [ ] [P0] **Orchestrator Loop**: Implement `run_experiment` logic (Fetch Data -> Prepare Context -> Call Decision Engine).
- [ ] [P0] **Daytona Client**: Implement `DaytonaClient.run(code, context)`.
- [ ] [P0] **Agent Prompting**: Create the prompt that instructs the LLM to write the decision code.
- [ ] [P0] **Decision Engine**: Implement the logic to try Daytona first, then fallback to Direct LLM.
- [ ] [P0] **Persistence**: Implement JSON file storage for experiment results.

### Frontend (Parallel)
- [ ] [P0] **Results Chart**: Implement Recharts time-series (Market vs Model).
- [ ] [P0] **Integration**: Connect Frontend to real Backend endpoints.
- [ ] [P0] **Interval Detail Panel**: Build the right sidebar to show Rationale and Evidence when a chart point is clicked.

## Phase 3: Analytics & Polish (Day 3)
### Backend
- [ ] [P1] **Breaking Point Analysis**: Implement logic to detect decision flips and identify "new" evidence.
- [ ] [P1] **Galileo Export**: Implement export endpoint for eval tools.
- [ ] [P1] **Live Mode (Optional)**: "Monitoring" mode that polls periodically.

### Frontend
- [ ] [P1] **Breaking Point UI**: Annotate charts with vertical lines for breaking points.
- [ ] [P1] **Evidence Highlighting**: Visually distinguish "New" evidence in the detail panel.
- [ ] [P1] **Current Recommendation**: Add the summary card at the top of the results page.
- [ ] [P2] **Styles & UX**: Polish typography, loading states, error handling.

## Ambiguities / To-Discuss
*   [ ] Are we using real Kalshi API or a specific dataset? (Assuming Real API for now, need keys).
*   [ ] Exact format of "Code" expected from the Agent (Is it a specific function signature?).

