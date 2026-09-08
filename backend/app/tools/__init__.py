from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.template_service import TemplateService, PolicyService, GenerationService, FacultyProfileService
from app.services.document_filler import document_filler
from app.schemas import TemplateSchema, FillTemplateResponse, FacultyProfile


class AgentTools:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_service = TemplateService(db)
        self.policy_service = PolicyService(db)
        self.generation_service = GenerationService(db)
        self.faculty_service = FacultyProfileService()
    
    async def search_templates(self, query: str) -> List[Dict[str, Any]]:
        return await self.template_service.search_templates(query, limit=5)
    
    async def search_policy(self, query: str, department: Optional[str] = None) -> List[Dict[str, Any]]:
        return await self.policy_service.search_policy(query, department, limit=5)
    
    async def get_template_schema(self, template_id: str) -> Dict[str, Any]:
        result = await self.template_service.get_template_with_schema(uuid.UUID(template_id))
        if not result:
            raise ValueError(f"Template not found: {template_id}")
        return result
    
    async def fill_template(self, template_id: str, field_values: Dict[str, Any]) -> Dict[str, Any]:
        template_schema = await self.get_template_schema(template_id)
        
        output_path = document_filler.fill_template(
            template_id=template_id,
            file_type=template_schema["file_type"],
            storage_path=template_schema["storage_path"],
            field_values=field_values,
            required_fields=template_schema["required_fields"],
        )
        
        filename = f"filled_{template_schema['name']}.{template_schema['file_type']}"
        download_url = f"/api/files/{output_path}"
        
        return {
            "output_path": output_path,
            "filename": filename,
            "download_url": download_url,
        }
    
    async def get_faculty_profile(self, user_id: str) -> Optional[FacultyProfile]:
        return await self.faculty_service.get_profile(uuid.UUID(user_id), self.db)