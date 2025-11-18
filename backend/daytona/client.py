from typing import Protocol, Dict, Any, Optional

class DaytonaClient(Protocol):
    """Interface for executing code in a Daytona sandbox."""

    async def create_workspace(self, language: str = "python") -> str:
        """Create a sandbox workspace and return its ID."""
        ...

    async def execute_code(self, workspace_id: str, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute code in the workspace.
        
        Args:
            workspace_id: The sandbox ID.
            code: The Python code to run.
            context: JSON-serializable context data to be made available to the code.
            
        Returns:
            The JSON output from the executed code (e.g. the DecisionResult).
        """
        ...
    
    async def cleanup_workspace(self, workspace_id: str) -> None:
        """Destroy the workspace."""
        ...

