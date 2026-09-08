from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector
import uuid

from app.models import Template, TemplateEmbedding, PolicyChunk, Generation, User
from app.schemas import TemplateCreate, TemplateUpdate, PolicyChunkCreate, GenerationCreate, FacultyProfile
from app.services.embeddings import embedding_service
from app.services.storage import get_storage


class TemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = get_storage()
    
    async def create_template(self, template_data: TemplateCreate, file_obj) -> Template:
        storage_path = f"templates/{uuid.uuid4()}_{template_data.name}"
        self.storage.save(storage_path, file_obj)
        
        embedding = embedding_service.embed_template(
            name=template_data.name,
            description=template_data.description or "",
            form_type=template_data.form_type or "",
            required_fields=template_data.required_fields,
        )
        
        template = Template(
            name=template_data.name,
            description=template_data.description,
            department=template_data.department,
            form_type=template_data.form_type,
            file_type=template_data.file_type,
            storage_path=storage_path,
            required_fields=template_data.required_fields,
        )
        self.db.add(template)
        await self.db.flush()
        
        template_embedding = TemplateEmbedding(
            template_id=template.id,
            embedding=embedding,
            source_text=f"Template: {template_data.name}\nDescription: {template_data.description or ''}\nType: {template_data.form_type or ''}\nFields: {', '.join(template_data.required_fields.keys())}",
        )
        self.db.add(template_embedding)
        
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def get_template(self, template_id: uuid.UUID) -> Optional[Template]:
        result = await self.db.execute(select(Template).where(Template.id == template_id))
        return result.scalar_one_or_none()
    
    async def get_template_with_schema(self, template_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        template = await self.get_template(template_id)
        if not template:
            return None
        return {
            "template_id": template.id,
            "name": template.name,
            "required_fields": template.required_fields,
            "file_type": template.file_type,
            "storage_path": template.storage_path,
        }
    
    async def list_templates(self, department: Optional[str] = None, active_only: bool = True) -> List[Template]:
        query = select(Template)
        if active_only:
            query = query.where(Template.active == True)
        if department:
            query = query.where(Template.department == department)
        result = await self.db.execute(query.order_by(Template.created_at.desc()))
        return result.scalars().all()
    
    async def search_templates(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_embedding = embedding_service.embed_query(query)
        
        stmt = select(
            Template,
            (1 - TemplateEmbedding.embedding.cosine_distance(query_embedding)).label("similarity")
        ).join(TemplateEmbedding).where(Template.active == True).order_by(
            (1 - TemplateEmbedding.embedding.cosine_distance(query_embedding)).desc()
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        templates = result.all()
        
        return [
            {
                "id": t.Template.id,
                "name": t.Template.name,
                "description": t.Template.description,
                "department": t.Template.department,
                "form_type": t.Template.form_type,
                "file_type": t.Template.file_type,
                "required_fields": t.Template.required_fields,
                "similarity": float(t.similarity),
            }
            for t in templates
        ]
    
    async def update_template(self, template_id: uuid.UUID, update_data: TemplateUpdate) -> Optional[Template]:
        template = await self.get_template(template_id)
        if not template:
            return None
        
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(template, field, value)
        
        if update_data.required_fields is not None:
            embedding = embedding_service.embed_template(
                name=template.name,
                description=template.description or "",
                form_type=template.form_type or "",
                required_fields=update_data.required_fields,
            )
            embed_result = await self.db.execute(
                select(TemplateEmbedding).where(TemplateEmbedding.template_id == template_id)
            )
            existing_embedding = embed_result.scalar_one_or_none()
            if existing_embedding:
                existing_embedding.embedding = embedding
                existing_embedding.source_text = f"Template: {template.name}\nDescription: {template.description or ''}\nType: {template.form_type or ''}\nFields: {', '.join(update_data.required_fields.keys())}"
        
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def delete_template(self, template_id: uuid.UUID) -> bool:
        template = await self.get_template(template_id)
        if not template:
            return False
        
        self.storage.delete(template.storage_path)
        await self.db.delete(template)
        await self.db.commit()
        return True


class PolicyService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_policy_chunks(self, chunks: List[PolicyChunkCreate]) -> List[PolicyChunk]:
        texts = [c.chunk_text for c in chunks]
        embeddings = embedding_service.embed_texts(texts)
        
        policy_chunks = []
        for chunk_data, embedding in zip(chunks, embeddings):
            pc = PolicyChunk(
                source_doc=chunk_data.source_doc,
                chunk_text=chunk_data.chunk_text,
                embedding=embedding,
                department=chunk_data.department,
                tags=chunk_data.tags,
            )
            self.db.add(pc)
            policy_chunks.append(pc)
        
        await self.db.commit()
        for pc in policy_chunks:
            await self.db.refresh(pc)
        return policy_chunks
    
    async def search_policy(self, query: str, department: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        query_embedding = embedding_service.embed_query(query)
        
        stmt = select(
            PolicyChunk,
            (1 - PolicyChunk.embedding.cosine_distance(query_embedding)).label("similarity")
        ).order_by(
            (1 - PolicyChunk.embedding.cosine_distance(query_embedding)).desc()
        ).limit(limit)
        
        if department:
            stmt = stmt.where(PolicyChunk.department == department)
        
        result = await self.db.execute(stmt)
        chunks = result.all()
        
        return [
            {
                "id": c.PolicyChunk.id,
                "source_doc": c.PolicyChunk.source_doc,
                "chunk_text": c.PolicyChunk.chunk_text,
                "department": c.PolicyChunk.department,
                "tags": c.PolicyChunk.tags,
                "similarity": float(c.similarity),
            }
            for c in chunks
        ]


class GenerationService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_generation(self, generation_data: GenerationCreate, user_id: uuid.UUID, template_version: int, output_path: str) -> Generation:
        generation = Generation(
            user_id=user_id,
            template_id=generation_data.template_id,
            template_version=template_version,
            field_values=generation_data.field_values,
            output_path=output_path,
        )
        self.db.add(generation)
        await self.db.commit()
        await self.db.refresh(generation)
        return generation
    
    async def get_user_generations(self, user_id: uuid.UUID) -> List[Generation]:
        result = await self.db.execute(
            select(Generation).where(Generation.user_id == user_id).order_by(Generation.created_at.desc())
        )
        return result.scalars().all()


class FacultyProfileService:
    MOCK_PROFILES = {
        "faculty@university.edu": FacultyProfile(
            name="Dr. Jane Smith",
            title="Professor of Computer Science",
            department="Computer Science",
            email="faculty@university.edu",
            courses=["CS101: Introduction to Programming", "CS301: Data Structures", "CS401: Algorithms"],
            office="Engineering Building, Room 301",
            phone="555-0101",
        ),
        "prof.biology@university.edu": FacultyProfile(
            name="Dr. Robert Johnson",
            title="Associate Professor of Biology",
            department="Biology",
            email="prof.biology@university.edu",
            courses=["BIO101: General Biology", "BIO201: Genetics", "BIO301: Molecular Biology"],
            office="Science Hall, Room 205",
            phone="555-0102",
        ),
        "dept.admin@university.edu": FacultyProfile(
            name="Ms. Sarah Williams",
            title="Department Administrator",
            department="Computer Science",
            email="dept.admin@university.edu",
            courses=[],
            office="Engineering Building, Room 100",
            phone="555-0103",
        ),
    }
    
    async def get_profile(self, user_id: uuid.UUID, db: AsyncSession) -> Optional[FacultyProfile]:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None
        return self.MOCK_PROFILES.get(user.email)
    
    async def get_profile_by_email(self, email: str) -> Optional[FacultyProfile]:
        return self.MOCK_PROFILES.get(email)