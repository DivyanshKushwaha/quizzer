from datetime import datetime, timezone
from core.database.postgres.postgres_config import get_connection
from core.handler.exception import AuthNotFound, AuthForbidden
from features.data_tools import quiz_data_tool as quiz_db


def register_player(quiz_id: int, player_id: str, display_name: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM app_data.quizzes WHERE id = %s", (quiz_id,))
            quiz = cur.fetchone()
            if not quiz:
                raise AuthNotFound("Quiz not found")
            if quiz["status"] not in ("draft", "lobby", "live"):
                raise AuthForbidden("Registration closed")
            cur.execute(
                """INSERT INTO app_data.registrations (quiz_id, player_id, display_name)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (quiz_id, player_id) DO UPDATE SET display_name = EXCLUDED.display_name
                   RETURNING *""",
                (quiz_id, player_id, display_name),
            )
            row = cur.fetchone()
            if quiz["status"] == "draft":
                cur.execute("UPDATE app_data.quizzes SET status = 'lobby' WHERE id = %s", (quiz_id,))
        conn.commit()
    return _serialize(row)


def list_registrations(quiz_id: int) -> list:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT display_name, registered_at FROM app_data.registrations WHERE quiz_id = %s ORDER BY registered_at",
                (quiz_id,),
            )
            return [_serialize(r) for r in cur.fetchall()]


def get_registered_quiz_ids(player_id: str) -> set:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT quiz_id FROM app_data.registrations WHERE player_id = %s", (player_id,))
            return {r["quiz_id"] for r in cur.fetchall()}


def get_finished_quiz_ids(player_id: str) -> set:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT quiz_id FROM app_data.attempts WHERE player_id = %s AND status = 'finished'",
                (player_id,),
            )
            return {r["quiz_id"] for r in cur.fetchall()}


def list_player_attempts(player_id: str) -> list:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT a.quiz_id, a.score, a.total_time_ms, a.question_index, a.status,
                          a.finished_at, q.title
                   FROM app_data.attempts a
                   JOIN app_data.quizzes q ON q.id = a.quiz_id
                   WHERE a.player_id = %s AND a.status = 'finished'
                   ORDER BY a.finished_at DESC NULLS LAST""",
                (player_id,),
            )
            rows = cur.fetchall()
    out = []
    for r in rows:
        item = dict(r)
        item["finished_at"] = quiz_db.to_ist_str(item.get("finished_at"), missing="-")
        out.append(item)
    return out


def finish_stale_attempts(quiz_id: int):
    """When a quiz ends, any attempt still 'playing' is finalized to 'finished'."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE app_data.attempts
                   SET status = 'finished', finished_at = NOW()
                   WHERE quiz_id = %s AND status = 'playing'""",
                (quiz_id,),
            )
        conn.commit()


def get_or_create_attempt(quiz_id: int, player_id: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status, ends_at FROM app_data.quizzes WHERE id = %s", (quiz_id,))
            quiz = cur.fetchone()
            if not quiz or quiz["status"] != "live":
                raise AuthForbidden("Quiz is not live")
            cur.execute(
                "SELECT 1 FROM app_data.registrations WHERE quiz_id = %s AND player_id = %s",
                (quiz_id, player_id),
            )
            if not cur.fetchone():
                raise AuthForbidden("Register before joining")
            cur.execute(
                """INSERT INTO app_data.attempts (quiz_id, player_id)
                   VALUES (%s, %s) ON CONFLICT (quiz_id, player_id) DO NOTHING
                   RETURNING id""",
                (quiz_id, player_id),
            )
            created = cur.fetchone() is not None
            cur.execute(
                "SELECT * FROM app_data.attempts WHERE quiz_id = %s AND player_id = %s",
                (quiz_id, player_id),
            )
            row = cur.fetchone()
        conn.commit()
    out = _serialize(row)
    out["_created"] = created
    return out


def get_attempt(quiz_id: int, player_id: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM app_data.attempts WHERE quiz_id = %s AND player_id = %s",
                (quiz_id, player_id),
            )
            row = cur.fetchone()
    return _serialize(row) if row else None


def save_answer(attempt_id: int, question_index: int, selected_index: int, is_correct: bool, time_ms: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO app_data.answers (attempt_id, question_index, selected_index, is_correct, time_ms)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (attempt_id, question_index) DO NOTHING
                   RETURNING *""",
                (attempt_id, question_index, selected_index, is_correct, time_ms),
            )
            row = cur.fetchone()
        conn.commit()
    return _serialize(row) if row else None


def update_attempt_progress(attempt_id: int, score: int, total_time_ms: int, question_index: int, status: str = "playing"):
    with get_connection() as conn:
        with conn.cursor() as cur:
            finished_at = datetime.now(timezone.utc) if status == "finished" else None
            cur.execute(
                """UPDATE app_data.attempts
                   SET score = %s, total_time_ms = %s, question_index = %s, status = %s, finished_at = %s
                   WHERE id = %s""",
                (score, total_time_ms, question_index, status, finished_at, attempt_id),
            )
        conn.commit()


def count_attempts(quiz_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT
                     COUNT(*) FILTER (WHERE status = 'playing') AS playing,
                     COUNT(*) FILTER (WHERE status = 'finished') AS finished
                   FROM app_data.attempts WHERE quiz_id = %s""",
                (quiz_id,),
            )
            row = cur.fetchone()
    return {"playing": row["playing"], "finished": row["finished"]}


def get_display_name(quiz_id: int, player_id: str) -> str:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT display_name FROM app_data.registrations WHERE quiz_id = %s AND player_id = %s",
                (quiz_id, player_id),
            )
            row = cur.fetchone()
    return row["display_name"] if row else player_id[:8]


def _serialize(row: dict) -> dict:
    out = dict(row)
    for key in ("started_at", "finished_at", "registered_at", "answered_at", "ends_at"):
        if out.get(key) and hasattr(out[key], "isoformat"):
            out[key] = out[key].isoformat()
    return out
