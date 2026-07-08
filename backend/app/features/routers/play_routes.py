from fastapi import APIRouter, Depends, Body
from features.utils.auth_utils import require_role
from features.utils import play_logic

router = APIRouter(prefix="/play", tags=["Player"])


@router.get("/quizzes")
async def browse_quizzes(user=Depends(require_role("player"))):
    return await play_logic.list_quizzes(user["user_id"])


@router.get("/my/attempts")
async def my_attempts(user=Depends(require_role("player"))):
    return await play_logic.my_attempts(user["user_id"])


@router.post("/quizzes/{quiz_id}/register")
async def register(quiz_id: int, body: dict = Body(...), user=Depends(require_role("player"))):
    return await play_logic.register(quiz_id, user["user_id"], body)


@router.get("/quizzes/{quiz_id}/lobby")
async def lobby(quiz_id: int, user=Depends(require_role("player"))):
    return await play_logic.lobby(quiz_id, user["user_id"])


@router.post("/quizzes/{quiz_id}/join")
async def join(quiz_id: int, user=Depends(require_role("player"))):
    return await play_logic.play_state(quiz_id, user["user_id"], join=True)


@router.get("/quizzes/{quiz_id}/state")
async def play_state(quiz_id: int, user=Depends(require_role("player"))):
    return await play_logic.play_state(quiz_id, user["user_id"])


@router.post("/quizzes/{quiz_id}/answer")
async def submit_answer(quiz_id: int, body: dict = Body(...), user=Depends(require_role("player"))):
    return await play_logic.submit_answer(quiz_id, user["user_id"], body)


@router.get("/quizzes/{quiz_id}/leaderboard")
async def leaderboard(quiz_id: int, user=Depends(require_role("player"))):
    return await play_logic.leaderboard(quiz_id, user["user_id"])


@router.get("/quizzes/{quiz_id}/leaderboard/top")
async def leaderboard_top(quiz_id: int):
    return await play_logic.leaderboard(quiz_id, top=True)


@router.get("/quizzes/{quiz_id}/presence")
async def presence(quiz_id: int):
    return await play_logic.presence(quiz_id)


@router.get("/quizzes/{quiz_id}/result")
async def result(quiz_id: int, user=Depends(require_role("player"))):
    return await play_logic.result(quiz_id, user["user_id"])
