from fastapi import APIRouter, Depends, Body
from features.utils.auth_utils import require_role
from features.data_tools import quiz_data_tool as db

router = APIRouter(prefix="/quizzes", tags=["Admin - Quizzes"])


@router.post("")
def create_quiz(
    body: dict = Body(...),
    user=Depends(require_role("admin")),
):
    return db.create_quiz(
        admin_id=user["user_id"],
        title=body["title"],
        description=body.get("description", ""),
        settings=body.get("settings", {}),
        prize=body.get("prize", {}),
        questions=body.get("questions", []),
        start_at=body.get("start_at"),
    )


@router.get("")
def list_my_quizzes(user=Depends(require_role("admin"))):
    return db.list_quizzes(admin_id=user["user_id"], audience="admin")


@router.get("/{quiz_id}")
def get_quiz(quiz_id: int, user=Depends(require_role("admin"))):
    quiz = db.get_quiz(quiz_id, include_answers=True, audience="admin")
    if quiz["admin_id"] != user["user_id"]:
        from core.handler.exception import AuthForbidden
        raise AuthForbidden("Not your quiz")
    return quiz


@router.put("/{quiz_id}")
def update_quiz(quiz_id: int, body: dict = Body(...), user=Depends(require_role("admin"))):
    return db.update_quiz(quiz_id, user["user_id"], **body)


@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: int, user=Depends(require_role("admin"))):
    db.delete_quiz(quiz_id, user["user_id"])
    return {"message": "Quiz deleted"}


@router.post("/{quiz_id}/start")
def start_quiz(quiz_id: int, user=Depends(require_role("admin"))):
    return db.start_quiz(quiz_id, user["user_id"])
