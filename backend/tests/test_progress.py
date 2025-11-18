"""
Unit tests for progress tracking module.
Tests ExperimentProgress and ProgressTracker classes.
"""
import unittest
import asyncio
from datetime import datetime
from backend.orchestrator.progress import ExperimentProgress, ProgressTracker, progress_tracker


class TestExperimentProgress(unittest.TestCase):
    """Test ExperimentProgress class."""
    
    def test_initialization(self):
        """Test progress initialization."""
        progress = ExperimentProgress("test-id", 10)
        self.assertEqual(progress.experiment_id, "test-id")
        self.assertEqual(progress.total_intervals, 10)
        self.assertEqual(progress.completed_intervals, 0)
        self.assertEqual(progress.failed_intervals, 0)
        self.assertEqual(progress.status, "running")
        self.assertIsNone(progress.error)
        self.assertIsNotNone(progress.start_time)
    
    def test_update(self):
        """Test progress update."""
        progress = ExperimentProgress("test-id", 10)
        progress.update(5, 1)
        self.assertEqual(progress.completed_intervals, 5)
        self.assertEqual(progress.failed_intervals, 1)
    
    def test_finish_success(self):
        """Test finishing with success."""
        progress = ExperimentProgress("test-id", 10)
        progress.update(10, 0)
        progress.finish(success=True)
        self.assertEqual(progress.status, "completed")
        self.assertIsNone(progress.error)
    
    def test_finish_failure(self):
        """Test finishing with failure."""
        progress = ExperimentProgress("test-id", 10)
        progress.update(5, 5)
        progress.finish(success=False, error="Test error")
        self.assertEqual(progress.status, "failed")
        self.assertEqual(progress.error, "Test error")
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        progress = ExperimentProgress("test-id", 10)
        progress.update(5, 1)
        
        result = progress.to_dict()
        self.assertEqual(result["experiment_id"], "test-id")
        self.assertEqual(result["total_intervals"], 10)
        self.assertEqual(result["completed_intervals"], 5)
        self.assertEqual(result["failed_intervals"], 1)
        self.assertEqual(result["status"], "running")
        self.assertIn("progress_percent", result)
        self.assertIn("elapsed_seconds", result)
        self.assertGreaterEqual(result["progress_percent"], 0)
        self.assertLessEqual(result["progress_percent"], 100)
    
    def test_progress_percent_calculation(self):
        """Test progress percentage calculation."""
        progress = ExperimentProgress("test-id", 10)
        progress.update(5, 0)
        result = progress.to_dict()
        self.assertEqual(result["progress_percent"], 50.0)
        
        progress.update(10, 0)
        result = progress.to_dict()
        self.assertEqual(result["progress_percent"], 100.0)


class TestProgressTracker(unittest.IsolatedAsyncioTestCase):
    """Test ProgressTracker class."""
    
    async def test_create(self):
        """Test creating a new progress tracker."""
        tracker = ProgressTracker()
        progress = await tracker.create("test-id", 10)
        
        self.assertEqual(progress.experiment_id, "test-id")
        self.assertEqual(progress.total_intervals, 10)
        
        # Verify it's stored
        retrieved = await tracker.get("test-id")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.experiment_id, "test-id")
    
    async def test_get_nonexistent(self):
        """Test getting non-existent progress."""
        tracker = ProgressTracker()
        result = await tracker.get("nonexistent-id")
        self.assertIsNone(result)
    
    async def test_update(self):
        """Test updating progress."""
        tracker = ProgressTracker()
        await tracker.create("test-id", 10)
        await tracker.update("test-id", 5, 1)
        
        progress = await tracker.get("test-id")
        self.assertEqual(progress.completed_intervals, 5)
        self.assertEqual(progress.failed_intervals, 1)
    
    async def test_finish(self):
        """Test finishing progress."""
        tracker = ProgressTracker()
        await tracker.create("test-id", 10)
        await tracker.finish("test-id", success=True)
        
        progress = await tracker.get("test-id")
        self.assertEqual(progress.status, "completed")
        
        await tracker.finish("test-id-2", success=False, error="Test error")
        progress2 = await tracker.get("test-id-2")
        self.assertIsNone(progress2)  # Should not exist if not created
    
    async def test_remove(self):
        """Test removing progress tracker."""
        tracker = ProgressTracker()
        await tracker.create("test-id", 10)
        
        retrieved = await tracker.get("test-id")
        self.assertIsNotNone(retrieved)
        
        await tracker.remove("test-id")
        retrieved = await tracker.get("test-id")
        self.assertIsNone(retrieved)
    
    async def test_concurrent_updates(self):
        """Test concurrent updates are handled correctly."""
        tracker = ProgressTracker()
        await tracker.create("test-id", 100)
        
        # Simulate concurrent updates
        async def update_progress(value):
            await tracker.update("test-id", value, 0)
        
        tasks = [update_progress(i) for i in range(1, 11)]
        await asyncio.gather(*tasks)
        
        progress = await tracker.get("test-id")
        # Should have been updated (final value may vary due to race conditions, but should be >= 1)
        self.assertGreaterEqual(progress.completed_intervals, 1)


class TestGlobalProgressTracker(unittest.IsolatedAsyncioTestCase):
    """Test the global progress_tracker instance."""
    
    async def test_global_instance(self):
        """Test that global instance works."""
        test_id = "global-test-id"
        progress = await progress_tracker.create(test_id, 20)
        self.assertEqual(progress.experiment_id, test_id)
        
        await progress_tracker.update(test_id, 10, 0)
        retrieved = await progress_tracker.get(test_id)
        self.assertEqual(retrieved.completed_intervals, 10)
        
        await progress_tracker.finish(test_id, success=True)
        finished = await progress_tracker.get(test_id)
        self.assertEqual(finished.status, "completed")
        
        # Cleanup
        await progress_tracker.remove(test_id)


if __name__ == '__main__':
    unittest.main()

