from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
import json
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..models.base import get_db
from ..models.user import User
from ..models.conversation import Conversation, Message
from ..services.llm import build_system_prompt, chat_stream
from ..services.rate_limit import check_rate_limit
from ..services.memory import search_memory, extract_and_save_memory
from .characters import load_characters
from .auth import require_user

router = APIRouter()


class ChatRequest(BaseModel):
    character_id: str
    content: str


@router.post("/chat")
def post_chat(req: ChatRequest, background_tasks: BackgroundTasks, user: User = Depends(require_user), db: Session = Depends(get_db)):
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
        
    # --- 增加：RAG 长期记忆检索 ---
    related_memories = search_memory(user.id, character_id, content, top_k=3)
        
    history = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).limit(40).all()
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": content})
    system_prompt = build_system_prompt(char)
    
    if related_memories:
        system_prompt += f"\n\n[温馨提示：你脑海中浮现了一些关于玩家的回忆，你可以根据需要参考：\n{related_memories}\n]"
    
    def generate():
        reply_parts = []
        try:
            for chunk in chat_stream(messages, system_prompt):
                if chunk:
                    reply_parts.append(chunk)
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'chunk': f'[Error: {str(e)}]', 'error': True})}\n\n"
        
        reply = "".join(reply_parts)
        user_msg = Message(conversation_id=conv.id, role="user", content=content)
        asst_msg = Message(conversation_id=conv.id, role="assistant", content=reply)
        db.add(user_msg)
        db.add(asst_msg)
        db.commit()
        
        # 将记忆提取挂在后台任务中异步执行，不阻碍回复
        background_tasks.add_task(extract_and_save_memory, user.id, character_id, content, reply)
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


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
