from datetime import datetime, timezone

RANK_MULTIPLIER = 10_000_000


def encode_rank_score(score: int, total_time_ms: int) -> float:
    """Higher score wins; ties broken by lower total time."""
    return score * RANK_MULTIPLIER - total_time_ms


def score_answer(correct_index: int, selected_index: int) -> tuple[int, bool]:
    is_correct = selected_index == correct_index
    return (10 if is_correct else 0), is_correct


def check_deadline(deadline: datetime | None) -> bool:
    """Return True if still within deadline (or no deadline set)."""
    if deadline is None:
        return True
    now = datetime.now(timezone.utc)
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return now <= deadline


def result_tier(rank: int) -> str:
    if rank <= 3:
        return "top3"
    if rank <= 10:
        return "top10"
    return "rest"


def public_question(question: dict) -> dict:
    """Strip correct answer — never reveal mid-quiz."""
    return {
        "index": question["index"],
        "text": question["text"],
        "options": question["options"],
        "timer_sec": question.get("timer_sec"),
    }
