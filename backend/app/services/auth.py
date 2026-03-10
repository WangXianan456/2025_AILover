import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET = os.getenv("JWT_SECRET", "change-me")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


def _trunc_pw(pw: str) -> str:
    b = pw.encode("utf-8")
    return b[:72].decode("utf-8", errors="ignore") if len(b) > 72 else pw


def hash_password(pw: str) -> str:
    return pwd_ctx.hash(_trunc_pw(pw))


def verify_password(pw: str, hashed: str) -> bool:
    return pwd_ctx.verify(_trunc_pw(pw), hashed)


def create_token(sub: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=EXPIRE_HOURS)
    return jwt.encode({"sub": sub, "exp": expire}, SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
