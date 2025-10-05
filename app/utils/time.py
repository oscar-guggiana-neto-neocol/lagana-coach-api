from datetime import time


def calculate_duration_minutes(start: time, end: time) -> int:
    start_total = start.hour * 60 + start.minute
    end_total = end.hour * 60 + end.minute
    if end_total <= start_total:
        raise ValueError("End time must be after start time")
    return end_total - start_total
