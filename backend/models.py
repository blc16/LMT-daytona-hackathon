from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

# --- Enums ---

class DecisionEnum(str, Enum):
    YES = "YES"
    NO = "NO"

class ExperimentMode(str, Enum):
    DAYTONA_AGENT = "daytona_agent"
    DIRECT_LLM = "direct_llm"

# --- 1. Input Models (Configuration) ---

class ExperimentConfig(BaseModel):
    """Configuration for a simulation run."""
    market_slug: str = Field(..., description="The Polymarket slug (e.g. 'gemini-3pt0-released-by')")
    start_time: datetime
    end_time: datetime
    interval_minutes: int = Field(..., gt=0)
    num_simulations: int = Field(1, ge=1, description="Number of agent runs per interval")
    model_provider: str = Field("openai/gpt-4o", description="OpenRouter model ID")
    mode: ExperimentMode = ExperimentMode.DAYTONA_AGENT

# --- 2. Context Models (Agent Input) ---

class SearchSnippet(BaseModel):
    """A single news article or search result."""
    id: str
    title: str
    url: str
    text: str
    published_date: str
    score: float = 0.0

class MarketState(BaseModel):
    """Snapshot of the market at a specific time."""
    timestamp: datetime
    price: float = Field(..., ge=0.0, le=1.0, description="Probability of YES (0-1)")
    volume: Optional[float] = None

class IntervalContext(BaseModel):
    """
    The 'State of the World' passed to the Agent.
    This is the prompt context.
    """
    time: datetime
    market_info: Dict[str, Any] = Field(..., description="Static market metadata (title, rules)")
    current_market_state: MarketState
    news: List[SearchSnippet]
    recent_history: List[MarketState] = Field(default_factory=list, description="Optional recent price history")

# --- 3. Output Models (Agent Output & Storage) ---

class AgentDecision(BaseModel):
    """The structured decision returned by the Agent code."""
    decision: DecisionEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str = Field(..., description="Markdown explanation of the decision")
    relevant_evidence_ids: List[str] = Field(default_factory=list, description="IDs/URLs of SearchSnippets used")

class IntervalResult(BaseModel):
    """The recorded result for one time interval."""
    timestamp: datetime
    market_state: MarketState
    decisions: List[AgentDecision]
    aggregated_decision: DecisionEnum
    aggregated_confidence: float

class ExperimentResult(BaseModel):
    """Complete dump of an experiment run."""
    id: str
    config: ExperimentConfig
    timeline: List[IntervalResult]
    created_at: datetime = Field(default_factory=datetime.utcnow)
