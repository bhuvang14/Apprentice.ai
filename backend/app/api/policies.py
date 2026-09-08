from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.api.auth import get_current_admin
from app.services.template_service import PolicyService
from app.services.chunker import chunker
from app.schemas import PolicyChunkCreate, PolicyChunkResponse
from app.models import User

router = APIRouter()


@router.post("", response_model=List[PolicyChunkResponse])
async def upload_policy_document(
    file: UploadFile = File(...),
    source_doc: str = Form(...),
    department: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    file_type = file.filename.split(".")[-1].lower()
    if file_type not in ["pdf", "docx", "xlsx", "txt"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        tag_list = tags.split(",") if tags else []
        chunks_data = chunker.process_document(
            file_path=tmp_path,
            file_type=file_type,
            source_doc=source_doc,
            department=department,
            tags=tag_list,
        )
        
        policy_chunks = [
            PolicyChunkCreate(**chunk) for chunk in chunks_data
        ]
        
        policy_service = PolicyService(db)
        created_chunks = await policy_service.add_policy_chunks(policy_chunks)
        return created_chunks
    finally:
        import os
        os.unlink(tmp_path)


@router.get("/search")
async def search_policy(
    q: str,
    department: Optional[str] = None,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    policy_service = PolicyService(db)
    results = await policy_service.search_policy(q, department, limit)
    return results