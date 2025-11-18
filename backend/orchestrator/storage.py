import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from backend.models import ExperimentConfig, ExperimentResult, IntervalResult

class ExperimentStorage:
    """Simple file-based storage for experiment results."""
    
    def __init__(self, storage_dir: str = "experiments"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_experiment(
        self, 
        config: ExperimentConfig, 
        timeline: List[IntervalResult],
        experiment_id: Optional[str] = None
    ) -> str:
        """
        Save experiment results to a JSON file.
        
        Args:
            config: Experiment configuration
            timeline: List of interval results
            experiment_id: Optional experiment ID. If not provided, generates a new UUID.
        
        Returns:
            Experiment ID (filename without extension)
        """
        if experiment_id is None:
            experiment_id = str(uuid.uuid4())
        
        result = ExperimentResult(
            id=experiment_id,
            config=config,
            timeline=timeline,
            created_at=datetime.now(timezone.utc)
        )
        
        file_path = self.storage_dir / f"{experiment_id}.json"
        
        with open(file_path, "w") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2, default=str)
        
        return experiment_id
    
    def load_experiment(self, experiment_id: str) -> Optional[ExperimentResult]:
        """Load an experiment by ID."""
        file_path = self.storage_dir / f"{experiment_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, "r") as f:
            data = json.load(f)
        
        return ExperimentResult.model_validate(data)
    
    def list_experiments(self) -> List[str]:
        """List all experiment IDs."""
        return [f.stem for f in self.storage_dir.glob("*.json")]

