from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.api.auth import get_current_user
from app.services.template_service import GenerationService
from app.schemas import GenerationResponse
from app.models import User

router = APIRouter()


@router.get("/{user_id}", response_model=list[GenerationResponse])
async def get_user_generations(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if str(current_user.id) != str(user_id) and current_user.role not in ["dept_admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Cannot view another user's generations")
    
    generation_service = GenerationService(db)
    generations = await generation_service.get_user_generations(user_id)
    return generations