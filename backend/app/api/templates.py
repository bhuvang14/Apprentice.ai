from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json
import uuid

from app.core.database import get_db
from app.api.auth import get_current_admin
from app.services.template_service import TemplateService
from app.schemas import TemplateCreate, TemplateUpdate, TemplateResponse, TemplateSearchResult
from app.models import User

router = APIRouter()


@router.post("", response_model=TemplateResponse)
async def create_template(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    form_type: Optional[str] = Form(None),
    file_type: str = Form(...),
    required_fields: str = Form("{}"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    if file_type not in ["docx", "xlsx", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Must be docx, xlsx, or pdf")
    
    try:
        required_fields_dict = json.loads(required_fields)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON for required_fields")
    
    template_data = TemplateCreate(
        name=name,
        description=description,
        department=department,
        form_type=form_type,
        file_type=file_type,
        required_fields=required_fields_dict,
        storage_path="",  # Will be set by service
    )
    
    template_service = TemplateService(db)
    template = await template_service.create_template(template_data, file.file)
    return template


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    department: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    template_service = TemplateService(db)
    templates = await template_service.list_templates(department, active_only)
    return templates


@router.get("/search", response_model=list[TemplateSearchResult])
async def search_templates(
    q: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    template_service = TemplateService(db)
    results = await template_service.search_templates(q, limit)
    return results


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    template_service = TemplateService(db)
    template = await template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    update_data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    template_service = TemplateService(db)
    template = await template_service.update_template(template_id, update_data)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    template_service = TemplateService(db)
    success = await template_service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted"}