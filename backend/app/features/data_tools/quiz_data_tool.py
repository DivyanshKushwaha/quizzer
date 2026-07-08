import asyncio
import json
from datetime import datetime, timezone, timedelta
import pytz
from core.database.postgres.postgres_config import get_connection
from core.handler.exception import AuthNotFound, AuthForbidden
from features.data_tools import redis_data_tool as redis_db

IST = pytz.timezone("Asia/Kolkata")


def to_ist_str(value, missing="Not started"):
    if not value:
        return missing
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(IST).strftime("%H:%M:%S")


def _compute_ends_at(started_at, settings: dict):
    overall_sec = (settings or {}).get("overall_timer_sec")
    if started_at and overall_sec:
        return started_at + timedelta(seconds=int(overall_sec))
    return None


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


async def create_quiz(admin_id: str, title: str, description: str, settings: dict, prize: dict,
                      questions: list, start_at=None) -> dict:
    questions = _normalize_questions(questions)
    started_at = _parse_dt(start_at)
    ends_at = _compute_ends_at(started_at, settings)

    def _op():
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO app_data.quizzes
                       (admin_id, title, description, settings, prize, questions, started_at, ends_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                    (admin_id, title, description, json.dumps(settings), json.dumps(prize),
                     json.dumps(questions), started_at, ends_at),
                )
                row = cur.fetchone()
            conn.commit()
        return row

    row = await asyncio.to_thread(_op)
    return _serialize(row, audience="admin")


def expire_finished_quizzes(cur, quiz_id: int | None = None) -> list:
    """Server-side auto-finish: any live quiz whose ends_at is in the past becomes 'finished'."""
    sql = """UPDATE app_data.quizzes SET status = 'finished'
             WHERE status = 'live' AND ends_at IS NOT NULL AND ends_at < NOW()"""
    params = []
    if quiz_id is not None:
        sql += " AND id = %s"
        params.append(quiz_id)
    sql += " RETURNING id"
    cur.execute(sql, params)
    return [r["id"] for r in cur.fetchall()]


def activate_scheduled_quizzes(cur, quiz_id: int | None = None) -> list:
    """Server-side auto-start: any scheduled draft/lobby quiz whose start time has arrived goes 'live'."""
    sql = """UPDATE app_data.quizzes SET status = 'live'
             WHERE status IN ('draft', 'lobby') AND started_at IS NOT NULL AND started_at <= NOW()"""
    params = []
    if quiz_id is not None:
        sql += " AND id = %s"
        params.append(quiz_id)
    sql += " RETURNING id"
    cur.execute(sql, params)
    return [r["id"] for r in cur.fetchall()]


async def run_transitions() -> dict:
    """One tick: flip due quizzes live, expire finished ones. Returns changed quiz ids for WS push."""
    def _op():
        with get_connection() as conn:
            with conn.cursor() as cur:
                activated = activate_scheduled_quizzes(cur)
                finished = expire_finished_quizzes(cur)
                conn.commit()
        return {"activated": activated, "finished": finished}
    return await asyncio.to_thread(_op)


async def list_quizzes(status: str | None = None, admin_id: str | None = None, audience: str | None = None):
    sql = """SELECT id, title, description, status, settings, prize,
             started_at, ends_at, created_at FROM app_data.quizzes WHERE 1=1"""
    params = []
    if status:
        sql += " AND status = %s"
        params.append(status)
    if admin_id:
        sql += " AND admin_id = %s"
        params.append(admin_id)
    sql += " ORDER BY created_at DESC"

    def _op():
        with get_connection() as conn:
            with conn.cursor() as cur:
                activate_scheduled_quizzes(cur)
                expire_finished_quizzes(cur)
                conn.commit()
                cur.execute(sql, params)
                return cur.fetchall()

    rows = await asyncio.to_thread(_op)
    return [_serialize(r, audience=audience) for r in rows]


async def get_quiz(quiz_id: int, include_answers: bool = False, audience: str | None = None) -> dict:
    def _op():
        with get_connection() as conn:
            with conn.cursor() as cur:
                activate_scheduled_quizzes(cur, quiz_id)
                expire_finished_quizzes(cur, quiz_id)
                conn.commit()
                cur.execute("SELECT * FROM app_data.quizzes WHERE id = %s", (quiz_id,))
                return cur.fetchone()

    row = await asyncio.to_thread(_op)
    if not row:
        raise AuthNotFound("Quiz not found")
    quiz = _serialize(row, audience=audience)
    if not include_answers:
        quiz["questions"] = [
            {k: v for k, v in q.items() if k != "correct_index"}
            for q in quiz.get("questions", [])
        ]
    return quiz


async def update_quiz(quiz_id: int, admin_id: str, **fields) -> dict:
    quiz = await get_quiz(quiz_id, include_answers=True)
    if quiz["admin_id"] != admin_id:
        raise AuthForbidden("Not your quiz")
    if quiz["status"] != "draft":
        raise AuthForbidden("Only draft quizzes can be edited")
    allowed = {"title", "description", "settings", "prize", "questions"}
    updates, params = [], []
    for key, val in fields.items():
        if key in allowed and val is not None:
            if key == "questions":
                val = _normalize_questions(val)
            updates.append(f"{key} = %s")
            params.append(json.dumps(val) if key in ("settings", "prize", "questions") else val)

    if "start_at" in fields:
        started_at = _parse_dt(fields.get("start_at"))
        settings = fields.get("settings") or quiz.get("settings")
        updates.append("started_at = %s")
        params.append(started_at)
        updates.append("ends_at = %s")
        params.append(_compute_ends_at(started_at, settings))

    if not updates:
        return quiz
    params.append(quiz_id)

    def _op():
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE app_data.quizzes SET {', '.join(updates)} WHERE id = %s RETURNING *", params)
                row = cur.fetchone()
            conn.commit()
        return row

    row = await asyncio.to_thread(_op)
    return _serialize(row, audience="admin")


async def delete_quiz(quiz_id: int, admin_id: str):
    quiz = await get_quiz(quiz_id, include_answers=True)
    if quiz["admin_id"] != admin_id:
        raise AuthForbidden("Not your quiz")
    if quiz["status"] != "draft":
        raise AuthForbidden("Only draft quizzes can be deleted")

    def _op():
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM app_data.quizzes WHERE id = %s", (quiz_id,))
            conn.commit()

    await asyncio.to_thread(_op)


async def start_quiz(quiz_id: int, admin_id: str) -> dict:
    quiz = await get_quiz(quiz_id, include_answers=True)
    if quiz["admin_id"] != admin_id:
        raise AuthForbidden("Not your quiz")
    if quiz["status"] not in ("draft", "lobby"):
        raise AuthForbidden("Quiz already started or finished")
    if not quiz.get("questions"):
        raise AuthForbidden("Add at least one question before starting")
    overall_sec = (quiz.get("settings") or {}).get("overall_timer_sec")
    ends_at = None
    if overall_sec:
        ends_at = datetime.now(timezone.utc) + timedelta(seconds=int(overall_sec))

    def _op():
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE app_data.quizzes SET status = 'live', started_at = NOW(), ends_at = %s
                       WHERE id = %s RETURNING *""",
                    (ends_at, quiz_id),
                )
                row = cur.fetchone()
            conn.commit()
        return row

    row = await asyncio.to_thread(_op)
    await redis_db.publish_global({"type": "feed"})
    await redis_db.publish(quiz_id, {"type": "started"})
    return _serialize(row, audience="admin")


def _normalize_questions(questions: list) -> list:
    return [{**q, "index": i} for i, q in enumerate(questions)]


def _serialize(row: dict, audience: str | None = None) -> dict:
    out = dict(row)
    for key in ("questions", "settings", "prize"):
        if isinstance(out.get(key), str):
            out[key] = json.loads(out[key])

    if audience == "admin":
        out["created_at"] = to_ist_str(out.get("created_at"))
        out["started_at"] = to_ist_str(out.get("started_at"))
        out["ends_at"] = to_ist_str(out.get("ends_at"))
    elif audience == "player":
        out.pop("created_at", None)
        out["started_at"] = to_ist_str(out.get("started_at"))
        out["ends_at"] = to_ist_str(out.get("ends_at"))
    else:
        for key in ("started_at", "ends_at", "created_at"):
            if out.get(key) and hasattr(out[key], "isoformat"):
                out[key] = out[key].isoformat()
    return out
