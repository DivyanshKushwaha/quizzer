from fastapi import Depends
from core.iam.authentication.auth import get_user_id_roles
from core.handler.exception import AuthForbidden


def require_role(*allowed_roles: str):
    """FastAPI dependency — allow only users with one of the given roles."""
    def dependency(user=Depends(get_user_id_roles)):
        roles = [r.lower() for r in user.get("roles", [])]
        if not any(r.lower() in roles for r in allowed_roles):
            raise AuthForbidden(f"Requires one of: {', '.join(allowed_roles)}")
        return user
    return dependency
