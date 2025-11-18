"""
Progress tracking for running experiments.
Stores progress state in memory (for now - could be persisted to Redis/DB).
"""
from typing import Dict, Optional
from datetime import datetime, timezone
import asyncio

class ExperimentProgress:
    """Tracks progress of a running experiment."""
    def __init__(self, experiment_id: str, total_intervals: int):
        self.experiment_id = experiment_id
        self.total_intervals = total_intervals
        self.completed_intervals = 0
        self.failed_intervals = 0
        self.start_time = datetime.now(timezone.utc)
        self.status = "running"  # running, completed, failed
        self.error: Optional[str] = None
    
    def update(self, completed: int, failed: int = 0):
        """Update progress."""
        self.completed_intervals = completed
        self.failed_intervals = failed
    
    def finish(self, success: bool = True, error: Optional[str] = None):
        """Mark experiment as finished."""
        self.status = "completed" if success else "failed"
        self.error = error
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        progress_pct = (self.completed_intervals / self.total_intervals * 100) if self.total_intervals > 0 else 0
        
        return {
            "experiment_id": self.experiment_id,
            "total_intervals": self.total_intervals,
            "completed_intervals": self.completed_intervals,
            "failed_intervals": self.failed_intervals,
            "progress_percent": round(progress_pct, 1),
            "status": self.status,
            "elapsed_seconds": round(elapsed, 1),
            "error": self.error
        }


class ProgressTracker:
    """Manages progress tracking for multiple experiments."""
    def __init__(self):
        self._experiments: Dict[str, ExperimentProgress] = {}
        self._lock = asyncio.Lock()
    
    async def create(self, experiment_id: str, total_intervals: int) -> ExperimentProgress:
        """Create a new progress tracker."""
        async with self._lock:
            progress = ExperimentProgress(experiment_id, total_intervals)
            self._experiments[experiment_id] = progress
            return progress
    
    async def get(self, experiment_id: str) -> Optional[ExperimentProgress]:
        """Get progress for an experiment."""
        async with self._lock:
            return self._experiments.get(experiment_id)
    
    async def update(self, experiment_id: str, completed: int, failed: int = 0):
        """Update progress."""
        async with self._lock:
            progress = self._experiments.get(experiment_id)
            if progress:
                progress.update(completed, failed)
    
    async def finish(self, experiment_id: str, success: bool = True, error: Optional[str] = None):
        """Mark experiment as finished."""
        async with self._lock:
            progress = self._experiments.get(experiment_id)
            if progress:
                progress.finish(success, error)
    
    async def remove(self, experiment_id: str):
        """Remove progress tracker (after some time)."""
        async with self._lock:
            self._experiments.pop(experiment_id, None)


# Global progress tracker instance
progress_tracker = ProgressTracker()

