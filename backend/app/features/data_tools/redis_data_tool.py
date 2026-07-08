import json
from core.database.redis.redis_utils import get_redis_client


def _lb_key(quiz_id: int) -> str:
    return f"quiz:{quiz_id}:lb"


def _presence_key(quiz_id: int) -> str:
    return f"quiz:{quiz_id}:presence"


def _channel(quiz_id: int) -> str:
    return f"quiz:{quiz_id}:events"


GLOBAL_CHANNEL = "quiz:global:events"


def publish_global(event: dict):
    get_redis_client().publish(GLOBAL_CHANNEL, json.dumps(event))


def update_leaderboard(quiz_id: int, player_id: str, rank_score: float, meta: dict):
    r = get_redis_client()
    r.zadd(_lb_key(quiz_id), {player_id: rank_score})
    r.hset(_presence_key(quiz_id), player_id, meta.get("question_index", 0))
    publish(quiz_id, {"type": "leaderboard"})
    publish(quiz_id, {"type": "presence"})


def get_leaderboard_window(quiz_id: int, player_id: str, window: int = 5) -> list:
    r = get_redis_client()
    rank = r.zrevrank(_lb_key(quiz_id), player_id)
    if rank is None:
        return []
    start = max(0, rank - window)
    stop = rank + window
    entries = r.zrevrange(_lb_key(quiz_id), start, stop, withscores=True)
    return [{"player_id": pid, "rank_score": sc, "rank": start + i + 1} for i, (pid, sc) in enumerate(entries)]


def get_top_leaderboard(quiz_id: int, limit: int = 10) -> list:
    r = get_redis_client()
    entries = r.zrevrange(_lb_key(quiz_id), 0, limit - 1, withscores=True)
    return [{"player_id": pid, "rank_score": sc, "rank": i + 1} for i, (pid, sc) in enumerate(entries)]


def get_player_rank(quiz_id: int, player_id: str) -> int | None:
    r = get_redis_client()
    rank = r.zrevrank(_lb_key(quiz_id), player_id)
    return (rank + 1) if rank is not None else None


def get_presence_sample(quiz_id: int, limit: int = 20) -> list:
    r = get_redis_client()
    data = r.hgetall(_presence_key(quiz_id))
    items = [{"player_id": k, "question_index": int(v)} for k, v in list(data.items())[:limit]]
    playing, finished = count_status(quiz_id)
    return {"playing": playing, "finished": finished, "players": items}


def count_status(quiz_id: int) -> tuple[int, int]:
    r = get_redis_client()
    playing = int(r.get(f"quiz:{quiz_id}:playing") or 0)
    finished = int(r.get(f"quiz:{quiz_id}:done") or 0)
    return playing, finished


def incr_playing(quiz_id: int):
    get_redis_client().incr(f"quiz:{quiz_id}:playing")
    publish(quiz_id, {"type": "presence"})


def incr_finished(quiz_id: int):
    r = get_redis_client()
    r.decr(f"quiz:{quiz_id}:playing")
    r.incr(f"quiz:{quiz_id}:done")
    publish(quiz_id, {"type": "presence"})


def set_question_deadline(quiz_id: int, player_id: str, q_index: int, ttl_sec: int) -> int:
    """Set the per-question deadline once (NX so it can't be reset by refetching state).
    Returns the seconds remaining until the server-authoritative deadline."""
    r = get_redis_client()
    key = f"quiz:{quiz_id}:deadline:{player_id}:{q_index}"
    r.set(key, "1", nx=True, ex=ttl_sec)
    remaining = r.ttl(key)
    return remaining if remaining and remaining > 0 else ttl_sec


def is_deadline_alive(quiz_id: int, player_id: str, q_index: int) -> bool:
    return bool(get_redis_client().exists(f"quiz:{quiz_id}:deadline:{player_id}:{q_index}"))


def try_idempotent(attempt_id: int, question_index: int) -> bool:
    """Return True if this is the first submission (SETNX guard)."""
    key = f"idempotent:{attempt_id}:{question_index}"
    return bool(get_redis_client().set(key, "1", nx=True, ex=3600))


def publish(quiz_id: int, event: dict):
    get_redis_client().publish(_channel(quiz_id), json.dumps(event))
