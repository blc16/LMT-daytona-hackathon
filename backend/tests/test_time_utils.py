import unittest
from datetime import datetime, timedelta, timezone
from backend.utils.time import generate_intervals

class TestGenerateIntervals(unittest.TestCase):

    def test_standard_window(self):
        # 10:00 to 11:00, 15 min interval -> 5 points
        start = datetime(2023, 10, 27, 10, 0, tzinfo=timezone.utc)
        end = datetime(2023, 10, 27, 11, 0, tzinfo=timezone.utc)
        expected = [
            start,
            start + timedelta(minutes=15),
            start + timedelta(minutes=30),
            start + timedelta(minutes=45),
            end
        ]
        result = generate_intervals(start, end, 15)
        self.assertEqual(result, expected)

    def test_partial_window(self):
        # 10:00 to 10:07, 5 min interval -> 10:00, 10:05 (10:10 is out)
        start = datetime(2023, 10, 27, 10, 0, tzinfo=timezone.utc)
        end = datetime(2023, 10, 27, 10, 7, tzinfo=timezone.utc)
        expected = [
            start,
            start + timedelta(minutes=5)
        ]
        result = generate_intervals(start, end, 5)
        self.assertEqual(result, expected)

    def test_single_point(self):
        # start == end
        start = datetime(2023, 10, 27, 10, 0, tzinfo=timezone.utc)
        result = generate_intervals(start, start, 5)
        self.assertEqual(result, [start])

    def test_naive_input_conversion(self):
        # Naive inputs should be treated as UTC
        start = datetime(2023, 10, 27, 10, 0) # Naive
        end = datetime(2023, 10, 27, 10, 10) # Naive
        result = generate_intervals(start, end, 5)
        
        self.assertTrue(result[0].tzinfo == timezone.utc)
        self.assertEqual(result[0].hour, 10)

    def test_invalid_inputs(self):
        start = datetime(2023, 10, 27, 10, 0, tzinfo=timezone.utc)
        end = datetime(2023, 10, 27, 11, 0, tzinfo=timezone.utc)
        
        with self.assertRaises(ValueError):
            generate_intervals(start, end, -5)
            
        with self.assertRaises(ValueError):
            generate_intervals(end, start, 5)

if __name__ == '__main__':
    unittest.main()

