from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str
    department: Optional[str] = None


class UserCreate(UserBase):
    oidc_sub: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None


class UserResponse(UserBase):
    id: uuid.UUID
    oidc_sub: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    department: Optional[str] = None
    form_type: Optional[str] = None
    file_type: str
    required_fields: Dict[str, Any] = {}


class TemplateCreate(TemplateBase):
    storage_path: str


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    form_type: Optional[str] = None
    required_fields: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class TemplateResponse(TemplateBase):
    id: uuid.UUID
    storage_path: str
    version: int
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TemplateSearchResult(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    department: Optional[str] = None
    form_type: Optional[str] = None
    file_type: str
    required_fields: Dict[str, Any]
    similarity: float


class PolicyChunkBase(BaseModel):
    source_doc: str
    chunk_text: str
    department: Optional[str] = None
    tags: Optional[List[str]] = None


class PolicyChunkCreate(PolicyChunkBase):
    pass


class PolicyChunkResponse(PolicyChunkBase):
    id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class PolicySearchResult(BaseModel):
    id: uuid.UUID
    source_doc: str
    chunk_text: str
    department: Optional[str] = None
    tags: Optional[List[str]] = None
    similarity: float


class GenerationCreate(BaseModel):
    template_id: uuid.UUID
    field_values: Dict[str, Any]


class GenerationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    template_id: uuid.UUID
    template_version: int
    field_values: Dict[str, Any]
    output_path: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    user_id: uuid.UUID
    conversation_history: Optional[List[Dict[str, str]]] = []


class ChatResponse(BaseModel):
    response: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    generated_file: Optional[Dict[str, str]] = None


class FacultyProfile(BaseModel):
    name: str
    title: str
    department: str
    email: str
    courses: List[str] = []
    office: Optional[str] = None
    phone: Optional[str] = None


class TemplateSchema(BaseModel):
    template_id: uuid.UUID
    name: str
    required_fields: Dict[str, Any]
    field_descriptions: Dict[str, str] = {}


class FillTemplateRequest(BaseModel):
    template_id: uuid.UUID
    field_values: Dict[str, Any]


class FillTemplateResponse(BaseModel):
    output_path: str
    filename: str
    download_url: str