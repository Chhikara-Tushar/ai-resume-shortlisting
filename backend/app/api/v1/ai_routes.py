from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.candidate import ChatRequest, ChatResponse
from app.ai.chatbot import chat

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await chat(
        user_id=current_user.id,
        session_id=data.session_id,
        message=data.message,
        role=current_user.role,
        db=db,
    )
    return ChatResponse(**result)
