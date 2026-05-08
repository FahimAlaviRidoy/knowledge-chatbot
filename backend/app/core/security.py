from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.core.config import get_settings
from app.core.logger import log
import hashlib

settings = get_settings()
ALGORITHM = "HS256"

# Use sha256 to hash password before bcrypt to avoid 72-byte limit
def _prep(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(password: str) -> str:
        return pwd_context.hash(_prep(password))

    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(_prep(plain), hashed)

except Exception:
    import bcrypt

    def hash_password(password: str) -> str:
        return bcrypt.hashpw(_prep(password).encode(), bcrypt.gensalt()).decode()

    def verify_password(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(_prep(plain).encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        log.warning(f"Token decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )