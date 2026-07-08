from fastapi.security import OAuth2PasswordBearer
from config import Configs

config = Configs()

JWT_SECRET = config.JWT_SECRET
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60
REFRESH_TOKEN_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
