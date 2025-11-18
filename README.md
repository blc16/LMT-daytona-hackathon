# LLM Market Timeline (LMT)

**AI-Powered Prediction Market Analysis Platform**

Backtest LLM-driven trading decisions on prediction markets with time-sliced analysis. This system simulates how an AI agent would have traded a specific prediction market over a past time window, given time-sliced information.

## 🚀 Features

- **Time-Sliced Analysis**: Break historical windows into intervals and analyze decisions at each point
- **AI-Powered Decisions**: LLM agents execute code in secure Daytona sandboxes for sophisticated decision-making
- **Market Integration**: Real-time Polymarket data integration
- **Beautiful Visualization**: Interactive charts comparing AI decisions vs actual market odds
- **Detailed Attribution**: Link decision changes directly to specific news events and evidence

## 🏗️ Architecture

### Backend (Python)
- **Orchestrator**: Manages experiment loops and coordinates data fetching
- **Market Client**: Fetches historical odds from Polymarket
- **Search Client**: Retrieves time-filtered news via Exa API
- **Trader Agent**: Generates and executes Python code in Daytona sandboxes
- **Researcher Agent**: Generates optimized search queries
- **FastAPI Server**: REST API for frontend integration

### Frontend (Next.js)
- **Experiment Configuration**: Beautiful form for setting up backtests
- **Timeline Visualization**: Interactive charts with Recharts
- **Drill-Down Analysis**: Detailed view of decisions, reasoning, and evidence

## 📦 Installation

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## ⚙️ Configuration

1. Copy `env.example` to `.env` in the project root
2. Fill in your API keys:
   - `POLYMARKET_GAMMA_URL` - Polymarket API endpoint
   - `EXA_API_KEY` - Exa search API key
   - `OPENROUTER_API_KEY` - OpenRouter API key
   - `DAYTONA_API_KEY` - Daytona sandbox API key
   - `DAYTONA_API_URL` - Daytona API URL (default: https://app.daytona.io/api)

## 🚀 Running

### Start Backend API Server

```bash
cd backend
source venv/bin/activate
python api.py
```

The API will be available at `http://localhost:8000`

### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📊 Usage

1. **Configure Experiment**: 
   - Enter a Polymarket market slug (e.g., `gemini-3pt0-released-by`)
   - Set time range and interval size
   - Choose model and execution mode

2. **Run Experiment**: 
   - Click "Run Experiment" to start the backtest
   - The system will process each interval sequentially

3. **Analyze Results**:
   - View the timeline chart comparing AI decisions vs market odds
   - Click on any interval point to see detailed reasoning
   - Explore evidence and execution traces

## 🧪 Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
python -m unittest discover tests
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 📁 Project Structure

```
.
├── backend/
│   ├── api.py                 # FastAPI server
│   ├── orchestrator/         # Core orchestration logic
│   ├── market/               # Polymarket integration
│   ├── search/               # Exa search integration
│   ├── llm/                  # LLM client
│   ├── daytona/              # Daytona sandbox client
│   └── models.py             # Data models
├── frontend/
│   ├── app/                  # Next.js pages
│   ├── components/           # React components
│   └── lib/                  # Utilities and API client
├── context/                  # Project documentation
└── experiments/              # Saved experiment results
```

## 🎯 Key Differentiators

- **Agentic Execution**: Uses Daytona to allow models to *compute* decisions via code execution
- **No Future Leakage**: Strictly filters information by timestamp
- **Detailed Traces**: Full execution traces with code, output, and timing
- **Breaking Point Analysis**: Identifies moments where sentiment shifted

## 📝 License

MIT

## 🙏 Acknowledgments

Built for the Daytona Hackathon
