class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
    
    def to_dict(self):
        """Return a dictionary representation (useful for JSON responses)."""
        return {"status_code": self.status_code, "detail": self.message}
    
class AuthUnauthorized(AuthError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, 401)

class AuthForbidden(AuthError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, 403)

class AuthNotFound(AuthError):
    def __init__(self, message: str = "Not Found"):
        super().__init__(message, 404)

class AuthServerError(AuthError):
    def __init__(self, message: str = "Server Error"):
        super().__init__(message, 500)

class ServiceError(Exception):
    def __init__(self, message: str, cause: str = None, status_code: int = 500):
        self.message = message
        self.cause = cause
        self.status_code = status_code
        super().__init__(message)
    
    def to_dict(self):
        return {"status_code": self.status_code, "detail": self.message, "cause": self.cause}

def handle_service_error(exc: ServiceError) -> dict:
    """Format ServiceError for API responses."""
    return exc.to_dict()
        