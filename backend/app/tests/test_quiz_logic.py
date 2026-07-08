"""Core logic tests — scoring, ranking, timer enforcement."""
from datetime import datetime, timedelta, timezone

import pytest

from features.utils import quiz_logic


# --- scoring ---

def test_score_answer_correct():
    points, correct = quiz_logic.score_answer(2, 2)
    assert points == 10
    assert correct is True


def test_score_answer_wrong():
    points, correct = quiz_logic.score_answer(2, 0)
    assert points == 0
    assert correct is False


def test_score_answer_timeout_skip():
    points, correct = quiz_logic.score_answer(1, -1)
    assert points == 0
    assert correct is False


# --- ranking: score mode ---

def test_score_mode_higher_score_ranks_first():
    a = quiz_logic.encode_rank_score(30, 5000, "score")
    b = quiz_logic.encode_rank_score(20, 1000, "score")
    assert a > b


def test_score_mode_tie_breaks_by_faster_time():
    a = quiz_logic.encode_rank_score(30, 3000, "score")
    b = quiz_logic.encode_rank_score(30, 5000, "score")
    assert a > b


def test_score_mode_same_score_and_time():
    a = quiz_logic.encode_rank_score(20, 4000, "score")
    b = quiz_logic.encode_rank_score(20, 4000, "score")
    assert a == b


# --- ranking: speed mode ---

def test_speed_mode_faster_time_ranks_first():
    fast = quiz_logic.encode_rank_score(10, 2000, "speed")
    slow = quiz_logic.encode_rank_score(30, 8000, "speed")
    assert fast > slow


def test_speed_mode_tie_breaks_by_higher_score():
    a = quiz_logic.encode_rank_score(30, 3000, "speed")
    b = quiz_logic.encode_rank_score(20, 3000, "speed")
    assert a > b


def test_speed_mode_lower_score_but_much_faster_can_win():
    fast_low = quiz_logic.encode_rank_score(10, 1000, "speed")
    slow_high = quiz_logic.encode_rank_score(50, 10000, "speed")
    assert fast_low > slow_high


# --- timer enforcement ---

def test_check_deadline_none_is_open():
    assert quiz_logic.check_deadline(None) is True


def test_check_deadline_future():
    future = datetime.now(timezone.utc) + timedelta(seconds=30)
    assert quiz_logic.check_deadline(future) is True


def test_check_deadline_past():
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert quiz_logic.check_deadline(past) is False


def test_check_deadline_naive_treated_as_utc():
    future = datetime.utcnow() + timedelta(seconds=60)
    assert quiz_logic.check_deadline(future) is True


# --- result tiers ---

@pytest.mark.parametrize("rank,expected", [
    (1, "top3"),
    (3, "top3"),
    (4, "top10"),
    (10, "top10"),
    (11, "rest"),
    (0, "rest"),
    (-1, "rest"),
])
def test_result_tier(rank, expected):
    assert quiz_logic.result_tier(rank) == expected


# --- public question strips answer ---

def test_public_question_hides_correct_index():
    q = {"index": 0, "text": "2+2?", "options": ["3", "4"], "correct_index": 1, "timer_sec": 15}
    pub = quiz_logic.public_question(q)
    assert "correct_index" not in pub
    assert pub["text"] == "2+2?"
    assert pub["timer_sec"] == 15
