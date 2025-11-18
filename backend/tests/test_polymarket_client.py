import unittest
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime, timezone
import httpx
from backend.market.polymarket import PolymarketClient

class TestPolymarketClient(unittest.IsolatedAsyncioTestCase):

    async def test_get_market_metadata(self):
        slug = "gemini-3pt0-released-by"
        mock_response = [{
            "id": "123",
            "slug": slug,
            "title": "Gemini 3.0 Released?",
            "markets": [{"id": "m1", "question": "Will it release?"}]
        }]

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_resp_obj = Mock()
            mock_resp_obj.status_code = 200
            mock_resp_obj.json.return_value = mock_response
            mock_resp_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_resp_obj

            client = PolymarketClient()
            result = await client.get_market_metadata(slug)
            
            self.assertEqual(result["slug"], slug)
            self.assertEqual(result["title"], "Gemini 3.0 Released?")
            self.assertEqual(len(result["markets"]), 1)
            
            expected_url = "https://gamma-api.polymarket.com/events"
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            self.assertEqual(args[0], expected_url)
            self.assertEqual(kwargs["params"], {"slug": slug})

    async def test_get_market_history(self):
        token_id = "123456"
        start = datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 2, 0, 0, tzinfo=timezone.utc)
        
        mock_history = {
            "history": [
                {"t": 1672531200, "p": 0.5},
                {"t": 1672617600, "p": 0.6}
            ]
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_resp_obj = Mock()
            mock_resp_obj.status_code = 200
            mock_resp_obj.json.return_value = mock_history
            mock_resp_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_resp_obj

            client = PolymarketClient()
            result = await client.get_market_history(token_id, start, end)
            
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["p"], 0.5)
            
            expected_url = "https://clob.polymarket.com/prices-history"
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            self.assertEqual(args[0], expected_url)
            self.assertIn("market", kwargs["params"])
            self.assertIn("startTs", kwargs["params"])

    async def test_get_price_at(self):
        token_id = "123456"
        target_time = datetime(2023, 1, 1, 10, 30, tzinfo=timezone.utc)
        target_ts = int(target_time.timestamp())
        
        # History points: 10:00 (0.4), 10:25 (0.45), 10:35 (0.5)
        # Target 10:30 -> should return 0.45 (latest point <= target)
        mock_history = {
            "history": [
                {"t": target_ts - 1800, "p": 0.4},   # 10:00
                {"t": target_ts - 300, "p": 0.45},   # 10:25
                {"t": target_ts + 300, "p": 0.5}     # 10:35
            ]
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_resp_obj = Mock()
            mock_resp_obj.status_code = 200
            mock_resp_obj.json.return_value = mock_history
            mock_resp_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_resp_obj

            client = PolymarketClient()
            price = await client.get_price_at(token_id, target_time)
            
            self.assertEqual(price, 0.45)

if __name__ == '__main__':
    unittest.main()
