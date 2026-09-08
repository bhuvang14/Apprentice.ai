from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.api.auth import get_current_user
from app.services.agent import ChatAgent
from app.schemas import ChatRequest, ChatResponse
from app.models import User

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != request.user_id:
        raise HTTPException(status_code=403, detail="Cannot chat as another user")
    
    agent = ChatAgent(db, request.user_id)
    result = await agent.process_message(request.message)
    
    return ChatResponse(**result)