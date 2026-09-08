from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.services.storage import get_storage
from app.models import User

router = APIRouter()


@router.get("/{file_path:path}")
async def download_file(
    file_path: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    storage = get_storage()
    
    if not storage.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_obj = storage.get(file_path)
        media_type = "application/octet-stream"
        
        if file_path.endswith(".docx"):
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif file_path.endswith(".xlsx"):
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif file_path.endswith(".pdf"):
            media_type = "application/pdf"
        
        return StreamingResponse(
            file_obj,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{file_path.split("/")[-1]}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")