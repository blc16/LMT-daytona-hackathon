from datetime import datetime, timedelta, timezone
from typing import List

def generate_intervals(start_time: datetime, end_time: datetime, interval_minutes: int) -> List[datetime]:
    """
    Generate a list of timestamps from start_time to end_time (inclusive) separated by interval_minutes.
    
    Args:
        start_time: The starting timestamp (must be timezone-aware or will be treated as UTC).
        end_time: The ending timestamp (must be timezone-aware or will be treated as UTC).
        interval_minutes: The number of minutes between each interval.

    Returns:
        List[datetime]: A list of timezone-aware datetime objects.
        
    Raises:
        ValueError: If interval_minutes <= 0 or start_time > end_time.
    """
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive")
    
    # Normalize to UTC if naive
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
        
    if start_time > end_time:
        raise ValueError("start_time must be before or equal to end_time")

    intervals = []
    current_time = start_time
    
    while current_time <= end_time:
        intervals.append(current_time)
        current_time += timedelta(minutes=interval_minutes)
        
    return intervals

