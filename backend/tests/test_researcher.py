import unittest
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime, timezone
from backend.orchestrator.researcher import Researcher, SearchQueries

class TestResearcher(unittest.IsolatedAsyncioTestCase):

    async def test_generate_queries(self):
        mock_llm = Mock()
        # Mock the generate_json to return a Pydantic object
        mock_llm.generate_json = AsyncMock(return_value=SearchQueries(
            queries=["query 1", "query 2", "query 3"]
        ))
        
        researcher = Researcher(mock_llm)
        
        queries = await researcher.generate_queries(
            market_info={"title": "Test Market", "description": "Test Desc"},
            current_price=0.5,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.assertEqual(len(queries), 3)
        self.assertEqual(queries[0], "query 1")
        mock_llm.generate_json.assert_called_once()

if __name__ == '__main__':
    unittest.main()

