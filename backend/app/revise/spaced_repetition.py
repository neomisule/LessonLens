"""Simplified SM-2 spaced repetition algorithm for Revise Mode.

SM-2 reference: https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-learning

Adaptation:
  - Quality 5 → mastered
  - Quality 3 → shaky
  - Quality 1 → confused
  - Quality 0 → not_started (treated same as confused)
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

_DEFAULT_EASE = 2.5
_MIN_EASE     = 1.3
_MAX_INTERVAL = 180  # days

# Minimum intervals per confidence (first review)
_FIRST_INTERVALS = {
    "mastered":    1,
    "shaky":       1,
    "confused":    1,
    "not_started": 1,
}


def next_review(
    confidence: str,
    current_interval_days: int,
    ease_factor: float,
    attempt_number: int,
) -> tuple[int, float, datetime]:
    """
    Apply SM-2 and return (new_interval_days, new_ease_factor, next_review_at).

    Args:
        confidence:           "mastered" | "shaky" | "confused" | "not_started"
        current_interval_days: last interval (1 on first attempt)
        ease_factor:           current EF (default 2.5)
        attempt_number:        how many times this item has been reviewed (0-indexed)
    """
    q = _quality(confidence)

    # EF update (SM-2 formula)
    new_ef = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = max(_MIN_EASE, min(3.0, new_ef))

    # Interval update
    if q < 3:
        # Failed — reset
        new_interval = 1
    elif attempt_number == 0:
        new_interval = 1
    elif attempt_number == 1:
        new_interval = 6
    else:
        new_interval = min(_MAX_INTERVAL, round(current_interval_days * new_ef))

    due_at = datetime.now(timezone.utc) + timedelta(days=new_interval)
    return new_interval, new_ef, due_at


def due_in_days(confidence: str, current_interval_days: int) -> int:
    """
    Rough due-in estimate for a given confidence state.
    Used for revision plan display without full SM-2 state.
    """
    if confidence in ("confused", "not_started"):
        return 0   # due now
    if confidence == "shaky":
        return min(3, current_interval_days)
    # mastered
    return current_interval_days


def _quality(confidence: str) -> int:
    return {"mastered": 5, "shaky": 3, "confused": 1, "not_started": 0}.get(confidence, 0)
