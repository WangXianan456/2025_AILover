from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..models.base import get_db
from ..models.user import User
from ..models.conversation import Conversation, Message
from ..services.llm import build_system_prompt, chat
from ..services.rate_limit import check_rate_limit
from .characters import load_characters
from .auth import require_user

router = APIRouter()


class ChatRequest(BaseModel):
    character_id: str
    content: str


@router.post("/chat")
def post_chat(req: ChatRequest, user: User = Depends(require_user), db: Session = Depends(get_db)):
    if not check_rate_limit(f"chat:{user.id}"):
        raise HTTPException(429, "请求过于频繁，请稍后再试")
    character_id = req.character_id
    content = (req.content or "").strip()
    if not character_id or not content:
        raise HTTPException(400, "缺少 character_id 或 content")
    chars = load_characters()
    char = next((c for c in chars if c.get("character_id") == character_id), None)
    if not char:
        raise HTTPException(404, "角色不存在")
    conv = db.query(Conversation).filter(
        Conversation.user_id == user.id,
        Conversation.character_id == character_id,
    ).first()
    if not conv:
        conv = Conversation(user_id=user.id, character_id=character_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)
    history = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).limit(40).all()
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": content})
    system_prompt = build_system_prompt(char)
    reply = chat(messages, system_prompt)
    for m in [Message(conversation_id=conv.id, role="user", content=content), Message(conversation_id=conv.id, role="assistant", content=reply)]:
        db.add(m)
    db.commit()
    return {"reply": reply}


@router.get("/conversations/{character_id}/messages")
def get_messages(character_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(
        Conversation.user_id == user.id,
        Conversation.character_id == character_id,
    ).first()
    if not conv:
        return []
    msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).all()
    return [{"role": m.role, "content": m.content} for m in msgs]
