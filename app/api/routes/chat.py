from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db, engine
from app.db.models import Base, Chat, Message
from app.orchestration.graph import GraphManager
from app.core.logger import logger
from app.api.dependencies import limiter

router = APIRouter()
graph_manager = GraphManager()

# Pydantic Schemas for API
class MessageCreate(BaseModel):
    content: str
    role: str = "user"

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSummary(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChatDetail(ChatSummary):
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"

class ChatUpdate(BaseModel):
    title: str

# Helper to init DB (quick hack for dev)
@router.post("/db/init", include_in_schema=False)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return {"status": "Database Initialized"}

@router.post("/chats", response_model=ChatSummary)
@limiter.limit("10/minute")
async def create_chat(request: Request, chat_data: ChatCreate, db: AsyncSession = Depends(get_db)):
    new_chat = Chat(title=chat_data.title)
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    return new_chat

@router.get("/chats/check-title")
async def check_title(title: str, db: AsyncSession = Depends(get_db)):
    # Case-insensitive check
    result = await db.execute(select(Chat).where(func.lower(Chat.title) == title.lower()))
    exists = result.scalars().first() is not None
    return {"exists": exists}

@router.patch("/chats/{chat_id}", response_model=ChatSummary)
async def update_chat(chat_id: str, chat_data: ChatUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat.title = chat_data.title
    chat.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(chat)
    return chat

@router.get("/chats", response_model=List[ChatSummary])
async def list_chats(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    # Order by updated_at so recent interactions float to top
    result = await db.execute(select(Chat).offset(skip).limit(limit).order_by(Chat.updated_at.desc()))
    chats = result.scalars().all()
    return chats

@router.get("/chats/{chat_id}", response_model=ChatDetail)
async def get_chat(chat_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chat).where(Chat.id == chat_id).options(selectinload(Chat.messages)))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@router.post("/chats/{chat_id}/messages", response_model=MessageResponse)
@limiter.limit("20/minute")
async def send_message(request: Request, chat_id: str, message_data: MessageCreate, db: AsyncSession = Depends(get_db)):
    # 1. Check chat exists
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # 2. Update Chat Timestamp (explicitly)
    chat.updated_at = datetime.utcnow()
    
    # 3. Save User Message
    user_msg = Message(chat_id=chat_id, role="user", content=message_data.content)
    db.add(user_msg)
    
    # 4. Auto-Title Generation (If first real message or default title)
    # Check if we should rename
    if not chat.title or chat.title == "New Chat" or chat.title == "New Session":
        # Simple heuristic: Rename on first user message
        try:
            # We use the graph manager but frame it as a strict instruction
            # Or just use the user content if it's short? 
            # Better: Ask LLM to summarize.
            # Ideally we'd have a separate method, but reusing invoke:
            gen_prompt = f"Generate a a very short (3-5 words) title for a chat starting with: '{message_data.content}'. Return ONLY the title, no quotes."
            # Note: The graph might try to RAG this. We prefer a direct LLM call. 
            # Assuming graph_manager has a direct client we can use? 
            # Getting lazy: Use graph_manager.invoke but it might include RAG sources.
            # Let's just use the first few words for now to be safe/fast/robust without breaking RAG flow.
            # Safe Fallback: "Topic: {First 5 words}"
            words = message_data.content.split()[:5]
            title_candidate = " ".join(words) + ("..." if len(words) < len(message_data.content.split()) else "")
            chat.title = title_candidate.title()
        except Exception as e:
            logger.error(f"Title Gen failed: {e}")

    await db.commit()
    await db.refresh(user_msg)
    
    # 5. Get AI Response via LangGraph
    logger.info(f"Invoking LangGraph for query: {message_data.content}")
    try:
        stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.desc()).limit(10)
        result = await db.execute(stmt)
        recent_msgs = result.scalars().all()[::-1]
        
        history_msgs = [m for m in recent_msgs if m.id != user_msg.id]
        
        from app.orchestration.memory import format_history
        history_str = format_history(history_msgs)
        
        graph_response = graph_manager.invoke(message_data.content, chat_history=history_str)
        ai_content = graph_response['answer']
        logger.info(f"Graph Output: Confidence={graph_response.get('confidence')}")
    except Exception as e:
        logger.error(f"LangGraph failed: {e}")
        ai_content = "I'm sorry, I encountered an error while processing your request."
    
    # 6. Save AI Message
    ai_msg = Message(chat_id=chat_id, role="assistant", content=ai_content)
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)

    return ai_msg
