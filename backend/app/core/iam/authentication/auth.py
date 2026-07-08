import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends

from core.database.postgres.postgres_config import get_connection
from core.handler.exception import AuthForbidden, AuthNotFound, AuthUnauthorized
from .auth_config import oauth2_scheme, JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_MINUTES, REFRESH_TOKEN_DAYS


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def _verify_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$", 1)
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return secrets.compare_digest(check, digest)


def _access_token(user_id: str, email: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": user_id, "email": email, "role": role, "exp": exp}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _refresh_token(user_id: str) -> str:
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO public.refresh_tokens (id, user_id, token_hash, expires_at) VALUES (%s, %s, %s, %s)",
                (str(uuid.uuid4()), user_id, token_hash, expires),
            )
        conn.commit()
    return raw


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise AuthUnauthorized(f"Invalid token: {exc}")


def create_keycloak_user(username: str, email: str, first_name: str, last_name: str, password: str, job_role: str):
    role = job_role if job_role in ("admin", "player") else "player"
    user_id = str(uuid.uuid4())
    full_name = f"{first_name} {last_name}".strip() or username
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM public.users WHERE email = %s", (email,))
            if cur.fetchone():
                raise AuthForbidden("Email already registered")
            cur.execute(
                "INSERT INTO public.users (id, full_name, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
                (user_id, full_name, email, _hash_password(password), role),
            )
        conn.commit()
    return user_id


def assign_user_role(user_id: str, subscription: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE public.users SET role = %s, updated_at = NOW() WHERE id = %s", (subscription, user_id))
        conn.commit()
    return {"message": f"Role '{subscription}' assigned to user {user_id}"}


def login_user(username: str, password: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, password_hash, role, is_active FROM public.users WHERE email = %s",
                (username,),
            )
            user = cur.fetchone()
    if not user:
        raise AuthNotFound("User not found")
    if not user["is_active"]:
        raise AuthForbidden("Account disabled")
    if not _verify_password(password, user["password_hash"]):
        raise AuthUnauthorized("Invalid credentials")
    uid = str(user["id"])
    return {
        "access_token": _access_token(uid, user["email"], user["role"]),
        "refresh_token": _refresh_token(uid),
        "token_type": "bearer",
    }


def logout_user(refresh_token: str):
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE public.refresh_tokens SET revoked = TRUE WHERE token_hash = %s", (token_hash,))
        conn.commit()
    return {"message": "User logged out successfully"}


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    payload = _decode_token(token)
    return {"sub": payload["sub"], "email": payload["email"], "role": payload.get("role")}


def get_user_id_roles(token: Annotated[str, Depends(oauth2_scheme)]):
    payload = _decode_token(token)
    role = payload.get("role")
    if not role:
        raise AuthUnauthorized("Role missing in token")
    return {"user_id": payload["sub"], "roles": [role]}
