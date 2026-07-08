from datetime import datetime, timezone, timedelta
from features.utils import quiz_logic
from features.data_tools import quiz_data_tool as quiz_db
from features.data_tools import play_data_tool as play_db
from features.data_tools import redis_data_tool as redis_db
from core.handler.exception import AuthForbidden, AuthNotFound


async def list_quizzes(player_id=None):
    rows = await quiz_db.list_quizzes(audience="player")
    registered = await play_db.get_registered_quiz_ids(player_id) if player_id else set()
    played = await play_db.get_finished_quiz_ids(player_id) if player_id else set()
    visible = []
    for q in rows:
        if q["id"] in played:
            continue
        available = q["status"] in ("lobby", "live") or (
            q["status"] == "draft" and q.get("started_at") not in (None, "Not started")
        )
        if available:
            q["registered"] = q["id"] in registered
            visible.append(q)
    return visible


async def my_attempts(player_id):
    return await play_db.list_player_attempts(player_id)


async def register(quiz_id, player_id, body):
    name = body.get("display_name") or player_id[:8]
    row = await play_db.register_player(quiz_id, player_id, name)
    await redis_db.publish(quiz_id, {"type": "lobby"})
    await redis_db.publish_global({"type": "feed"})
    return row


async def lobby(quiz_id, player_id=None):
    is_registered = bool(player_id) and quiz_id in (await play_db.get_registered_quiz_ids(player_id))
    quiz = await quiz_db.get_quiz(quiz_id, audience="player")
    registered = await play_db.list_registrations(quiz_id)
    return {
        "quiz": quiz,
        "registered": registered,
        "is_registered": is_registered,
    }


async def play_state(quiz_id, player_id, join=False):
    if join:
        attempt = await play_db.get_or_create_attempt(quiz_id, player_id)
        if attempt.get("_created"):
            await redis_db.incr_playing(quiz_id)
    else:
        attempt = await play_db.get_attempt(quiz_id, player_id)
        if not attempt:
            raise AuthNotFound("No active attempt — join first")

    quiz = await quiz_db.get_quiz(quiz_id)
    questions = quiz.get("questions", [])
    idx = attempt["question_index"]
    done = attempt["status"] == "finished" or idx >= len(questions)
    question = None
    question_deadline = None

    if not done and idx < len(questions):
        raw = questions[idx]
        question = quiz_logic.public_question({**raw, "index": idx})
        timer_sec = raw.get("timer_sec") or (quiz.get("settings") or {}).get("per_question_timer_sec")
        if timer_sec:
            remaining = await redis_db.set_question_deadline(quiz_id, player_id, idx, int(timer_sec))
            question_deadline = (datetime.now(timezone.utc) + timedelta(seconds=remaining)).isoformat()

    return {
        "attempt_id": attempt["id"],
        "score": attempt["score"],
        "question_index": idx,
        "status": attempt["status"],
        "quiz_status": quiz.get("status"),
        "question": question,
        "question_deadline": question_deadline,
        "total_questions": len(questions),
        "quiz_ends_at": quiz.get("ends_at"),
    }


async def submit_answer(quiz_id, player_id, body):
    selected = body.get("selected_index")
    if selected is None:
        raise AuthForbidden("selected_index required")

    quiz = await quiz_db.get_quiz(quiz_id, include_answers=True)
    attempt = await play_db.get_attempt(quiz_id, player_id)
    if not attempt or attempt["status"] != "playing":
        raise AuthForbidden("No active attempt")

    q_idx = attempt["question_index"]
    questions = quiz.get("questions", [])
    if q_idx >= len(questions):
        raise AuthForbidden("Quiz already finished")
    if not await redis_db.try_idempotent(attempt["id"], q_idx):
        return await play_state(quiz_id, player_id)

    if quiz.get("ends_at") and not quiz_logic.check_deadline(datetime.fromisoformat(quiz["ends_at"])):
        await play_db.finish_stale_attempts(quiz_id)
        return await play_state(quiz_id, player_id)

    within_deadline = await redis_db.is_deadline_alive(quiz_id, player_id, q_idx)
    if within_deadline and selected is not None and selected >= 0:
        points, is_correct = quiz_logic.score_answer(questions[q_idx]["correct_index"], selected)
    else:
        points, is_correct = 0, False
    time_ms = int(body.get("time_ms", 0))
    if not await play_db.save_answer(attempt["id"], q_idx, selected, is_correct, time_ms):
        return await play_state(quiz_id, player_id)

    new_score = attempt["score"] + points
    new_time = attempt["total_time_ms"] + time_ms
    next_idx = q_idx + 1
    finished = next_idx >= len(questions)
    status = "finished" if finished else "playing"

    await play_db.update_attempt_progress(attempt["id"], new_score, new_time, next_idx, status)
    display_name = await play_db.get_display_name(quiz_id, player_id)
    win_condition = (quiz.get("settings") or {}).get("win_condition", "score")
    rank_score = quiz_logic.encode_rank_score(new_score, new_time, win_condition)
    await redis_db.update_leaderboard(quiz_id, player_id, rank_score, {
        "score": new_score,
        "question_index": next_idx,
        "display_name": display_name,
    })
    if finished:
        await redis_db.incr_finished(quiz_id)

    state = await play_state(quiz_id, player_id)
    return {**state, "score_delta": points}


async def leaderboard(quiz_id, player_id=None, top=False):
    rows = await (redis_db.get_top_leaderboard(quiz_id) if top else redis_db.get_leaderboard_window(quiz_id, player_id))
    result = []
    for r in rows:
        name = await play_db.get_display_name(quiz_id, r["player_id"])
        result.append({**r, "display_name": name})
    return result


async def presence(quiz_id):
    sample = await redis_db.get_presence_sample(quiz_id)
    counts = await play_db.count_attempts(quiz_id)
    sample["playing"] = counts["playing"]
    sample["finished"] = counts["finished"]
    return sample


async def result(quiz_id, player_id):
    quiz = await quiz_db.get_quiz(quiz_id)
    if quiz.get("status") != "finished":
        raise AuthForbidden("Results will be announced after the quiz ends")

    attempt = await play_db.get_attempt(quiz_id, player_id)
    if not attempt or attempt["status"] != "finished":
        raise AuthForbidden("You did not complete this quiz")

    rank = await redis_db.get_player_rank(quiz_id, player_id)
    if not rank:
        return {
            "rank": 0,
            "score": attempt["score"],
            "total_time_ms": attempt["total_time_ms"],
            "tier": "rest",
            "prize": None,
        }
    tier = quiz_logic.result_tier(rank)
    prize = quiz.get("prize") or {}
    return {
        "rank": rank,
        "score": attempt["score"],
        "total_time_ms": attempt["total_time_ms"],
        "tier": tier,
        "prize": prize.get(tier),
    }
