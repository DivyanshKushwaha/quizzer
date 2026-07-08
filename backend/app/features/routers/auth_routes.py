from fastapi import APIRouter, Body, Depends
from core.iam.authentication.auth import create_keycloak_user, login_user, logout_user, get_user_id_roles

router = APIRouter(tags=["Authentication"])


@router.post("/register")
def register(
    username: str = Body(...),
    email: str = Body(...),
    first_name: str = Body(...),
    last_name: str = Body(...),
    password: str = Body(...),
    role: str = Body("player"),
):
    if role not in ("admin", "player"):
        role = "player"
    user_id = create_keycloak_user(username, email, first_name, last_name, password, role)
    return {"message": "Registered successfully", "user_id": user_id, "role": role}


@router.post("/login")
def login(email: str = Body(...), password: str = Body(...)):
    return login_user(email, password)


@router.post("/logout")
def logout(refresh_token: str = Body(..., embed=True)):
    return logout_user(refresh_token)


@router.get("/me")
def me(user=Depends(get_user_id_roles)):
    return user
