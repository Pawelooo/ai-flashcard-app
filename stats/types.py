from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class StudyStats:
    today_count: int
    correct_pct: int | None  # None when no reviews exist for today
    streak: int
    last_reviewed: date | None  # None when user has never reviewed
    next_review: date          # earliest date the next review is due
