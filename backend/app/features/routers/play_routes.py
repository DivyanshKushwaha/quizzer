from fastapi import APIRouter, Depends, Body
from features.utils.auth_utils import require_role
from features.utils import play_logic

router = APIRouter(prefix="/play", tags=["Player"])


@router.get("/quizzes")
def browse_quizzes(user=Depends(require_role("player"))):
    return play_logic.list_quizzes(user["user_id"])


@router.get("/my/attempts")
def my_attempts(user=Depends(require_role("player"))):
    return play_logic.my_attempts(user["user_id"])


@router.post("/quizzes/{quiz_id}/register")
def register(quiz_id: int, body: dict = Body(...), user=Depends(require_role("player"))):
    return play_logic.register(quiz_id, user["user_id"], body)


@router.get("/quizzes/{quiz_id}/lobby")
def lobby(quiz_id: int, user=Depends(require_role("player"))):
    return play_logic.lobby(quiz_id, user["user_id"])


@router.post("/quizzes/{quiz_id}/join")
def join(quiz_id: int, user=Depends(require_role("player"))):
    return play_logic.play_state(quiz_id, user["user_id"], join=True)


@router.get("/quizzes/{quiz_id}/state")
def play_state(quiz_id: int, user=Depends(require_role("player"))):
    return play_logic.play_state(quiz_id, user["user_id"])


@router.post("/quizzes/{quiz_id}/answer")
def submit_answer(quiz_id: int, body: dict = Body(...), user=Depends(require_role("player"))):
    return play_logic.submit_answer(quiz_id, user["user_id"], body)


@router.get("/quizzes/{quiz_id}/leaderboard")
def leaderboard(quiz_id: int, user=Depends(require_role("player"))):
    return play_logic.leaderboard(quiz_id, user["user_id"])


@router.get("/quizzes/{quiz_id}/leaderboard/top")
def leaderboard_top(quiz_id: int):
    return play_logic.leaderboard(quiz_id, top=True)


@router.get("/quizzes/{quiz_id}/presence")
def presence(quiz_id: int):
    return play_logic.presence(quiz_id)


@router.get("/quizzes/{quiz_id}/result")
def result(quiz_id: int, user=Depends(require_role("player"))):
    return play_logic.result(quiz_id, user["user_id"])
