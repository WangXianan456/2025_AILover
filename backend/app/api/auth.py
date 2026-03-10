from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..models.base import get_db
from ..models.user import User
from ..services.auth import hash_password, verify_password, create_token, decode_token
from sqlalchemy.orm import Session

router = APIRouter()
security = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    if not cred or not cred.credentials:
        return None
    username = decode_token(cred.credentials)
    if not username:
        return None
    user = db.query(User).filter(User.username == username).first()
    return user


def require_user(user: User | None = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(401, "未登录")
    return user


@router.post("/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if len(req.username) < 2 or len(req.username) > 32:
        raise HTTPException(400, "用户名 2-32 字符")
    if len(req.password) < 6:
        raise HTTPException(400, "密码至少 6 位")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "用户名已存在")
    try:
        user = User(username=req.username, password_hash=hash_password(req.password))
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_token(user.username)
        return {"token": token, "username": user.username}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    token = create_token(user.username)
    return {"token": token, "username": user.username}


@router.get("/auth/me")
def me(user: User = Depends(require_user)):
    return {"username": user.username}
