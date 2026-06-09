"""
services/scoring_service.py
----------------------------
Scoring engine for the quiz platform.
Calculates points based on response speed.

Scoring Formula:
    if correct:
        points = max(10, 100 - int(response_time * 5))
    else:
        points = 0

Examples:
    1 second  → 95 points
    2 seconds → 90 points
    3 seconds → 85 points
    5 seconds → 75 points
    10 seconds → 50 points
    Wrong answer → 0 points
"""

import logging

logger = logging.getLogger(__name__)


def calculate_points(response_time_seconds: float, is_correct: bool) -> int:
    """
    Calculate points based on correctness and response speed.
    
    Args:
        response_time_seconds: Time taken to answer in seconds
        is_correct: Whether the selected answer was correct
    
    Returns:
        Integer points awarded (0 for wrong answers)
    """
    if not is_correct:
        return 0

    # Ensure response time is at least 0
    response_time_seconds = max(0, response_time_seconds)

    # Formula: max(10, 100 - int(response_time * 5))
    # Faster answers get more points, minimum 10 for correct answers
    points = max(10, 100 - int(response_time_seconds * 5))

    logger.debug(
        f"Score calculated: time={response_time_seconds:.2f}s, "
        f"correct={is_correct}, points={points}"
    )

    return points


def calculate_points_from_ms(response_time_ms: float, is_correct: bool) -> int:
    """
    Calculate points from response time in milliseconds.
    Convenience wrapper around calculate_points().
    
    Args:
        response_time_ms: Time taken to answer in milliseconds
        is_correct: Whether the selected answer was correct
    
    Returns:
        Integer points awarded
    """
    return calculate_points(response_time_ms / 1000, is_correct)
