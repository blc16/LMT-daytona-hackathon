import unittest
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime, timezone
import httpx
from backend.search.exa import ExaSearchClient
from backend.models import SearchSnippet

class TestExaSearchClient(unittest.IsolatedAsyncioTestCase):

    async def test_search_payload_and_parsing(self):
        # Setup
        query = "Google Gemini 3.0"
        cutoff_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        limit = 3
        
        mock_api_response = {
            "results": [
                {
                    "id": "doc1",
                    "title": "Gemini 3 Rumors",
                    "url": "https://news.com/gemini3",
                    "text": "Some rumor text...",
                    "publishedDate": "2023-12-25T10:00:00Z",
                    "score": 0.95
                }
            ]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            # Mock the response object
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_api_response
            mock_response_obj.raise_for_status.return_value = None
            
            mock_post.return_value = mock_response_obj

            # Execute
            client = ExaSearchClient()
            results = await client.search(query, cutoff_time, limit)
            
            # Verify Payload
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            payload = kwargs["json"]
            
            self.assertEqual(payload["query"], query)
            self.assertEqual(payload["numResults"], limit)
            self.assertEqual(payload["endPublishedDate"], cutoff_time.isoformat())
            self.assertTrue(payload["contents"]["text"])
            
            # Verify Parsing
            self.assertEqual(len(results), 1)
            self.assertIsInstance(results[0], SearchSnippet)
            self.assertEqual(results[0].id, "doc1")
            self.assertEqual(results[0].title, "Gemini 3 Rumors")
            self.assertEqual(results[0].published_date, "2023-12-25T10:00:00Z")

if __name__ == '__main__':
    unittest.main()

