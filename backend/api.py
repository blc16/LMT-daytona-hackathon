"""
FastAPI server for LLM Market Timeline backend.
Provides REST API endpoints for the frontend.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List
from backend.models import ExperimentConfig, ExperimentMode
from backend.orchestrator.core import Orchestrator
from backend.orchestrator.storage import ExperimentStorage
from backend.market.polymarket import PolymarketClient
import asyncio

app = FastAPI(title="LLM Market Timeline API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
orchestrator = Orchestrator()
storage = ExperimentStorage()
market_client = PolymarketClient()


@app.get("/")
async def root():
    return {"message": "LLM Market Timeline API", "version": "1.0.0"}


@app.get("/api/markets/{slug}/metadata")
async def get_market_metadata(slug: str):
    """Fetch market metadata for a given Polymarket slug."""
    try:
        metadata = await market_client.get_market_metadata(slug)
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/experiments/run")
async def run_experiment(config: dict):
    """Run a new experiment with the given configuration."""
    try:
        # Parse datetime strings - handle both ISO format and local datetime format
        start_time_str = config["start_time"]
        end_time_str = config["end_time"]
        
        # Parse start_time
        try:
            if "Z" in start_time_str or "+" in start_time_str or "-" in start_time_str[-6:]:
                # Has timezone info
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            else:
                # Local datetime without timezone - treat as UTC
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "") + "+00:00")
        except ValueError as e:
            raise ValueError(f"Invalid start_time format: {start_time_str}. Error: {e}")
        
        # Parse end_time
        try:
            if "Z" in end_time_str or "+" in end_time_str or "-" in end_time_str[-6:]:
                # Has timezone info
                end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
            else:
                # Local datetime without timezone - treat as UTC
                end_time = datetime.fromisoformat(end_time_str.replace("Z", "") + "+00:00")
        except ValueError as e:
            raise ValueError(f"Invalid end_time format: {end_time_str}. Error: {e}")
        
        # Ensure timezone-aware
        from datetime import timezone
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        
        # Validate time range
        if start_time >= end_time:
            raise ValueError(f"start_time ({start_time}) must be before end_time ({end_time})")
        
        # Validate and convert config
        experiment_config = ExperimentConfig(
            market_slug=config["market_slug"],
            start_time=start_time,
            end_time=end_time,
            interval_minutes=config["interval_minutes"],
            num_simulations=config.get("num_simulations", 1),
            model_provider=config.get("model_provider", "openai/gpt-4o"),
            mode=ExperimentMode(config.get("mode", "daytona_agent")),
        )
        
        # Run experiment (this is async and may take a while)
        experiment_id = await orchestrator.run_experiment(experiment_config)
        
        return {"experiment_id": experiment_id, "status": "completed"}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    """Get experiment results by ID."""
    try:
        experiment = storage.load_experiment(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # Convert to dict for JSON response with proper serialization
        try:
            # model_dump() doesn't accept 'default' parameter, use mode="json" which handles datetime serialization
            result = experiment.model_dump(mode="json")
            # Manually convert any remaining datetime objects to strings
            import json
            return json.loads(json.dumps(result, default=str))
        except Exception as dump_error:
            # If model_dump fails, try manual serialization
            import traceback
            error_details = f"Serialization error: {str(dump_error)}\n{traceback.format_exc()}"
            print(f"ERROR serializing experiment {experiment_id}: {error_details}")
            raise HTTPException(status_code=500, detail=f"Failed to serialize experiment: {str(dump_error)}")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        print(f"ERROR loading experiment {experiment_id}: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to load experiment: {str(e)}")


@app.get("/api/experiments")
async def list_experiments():
    """List all experiment IDs."""
    try:
        experiment_ids = storage.list_experiments()
        return experiment_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

