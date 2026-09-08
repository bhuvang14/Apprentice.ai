import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, ForeignKey, Index, ARRAY, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    oidc_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    generations: Mapped[List["Generation"]] = relationship("Generation", back_populates="user")
    
    __table_args__ = (
        CheckConstraint("role IN ('faculty', 'dept_admin', 'system_admin')", name="check_user_role"),
        Index("idx_users_oidc_sub", "oidc_sub"),
        Index("idx_users_email", "email"),
    )


class Template(Base):
    __tablename__ = "templates"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    form_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    required_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    embeddings: Mapped[Optional["TemplateEmbedding"]] = relationship("TemplateEmbedding", back_populates="template", uselist=False)
    generations: Mapped[List["Generation"]] = relationship("Generation", back_populates="template")
    
    __table_args__ = (
        CheckConstraint("file_type IN ('docx', 'xlsx', 'pdf')", name="check_template_file_type"),
        Index("idx_templates_department", "department"),
        Index("idx_templates_active", "active"),
    )


class TemplateEmbedding(Base):
    __tablename__ = "template_embeddings"
    
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), primary_key=True)
    embedding: Mapped[List[float]] = mapped_column(Vector(1024), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    template: Mapped["Template"] = relationship("Template", back_populates="embeddings")
    
    __table_args__ = (
        Index("idx_template_embeddings_embedding", "embedding", postgresql_using="hnsw", postgresql_with={"m": 16, "ef_construction": 64}, postgresql_ops={"embedding": "vector_cosine_ops"}),
    )


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_doc: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(Vector(1024), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_policy_chunks_embedding", "embedding", postgresql_using="hnsw", postgresql_with={"m": 16, "ef_construction": 64}, postgresql_ops={"embedding": "vector_cosine_ops"}),
        Index("idx_policy_chunks_department", "department"),
    )


class Generation(Base):
    __tablename__ = "generations"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    field_values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    user: Mapped["User"] = relationship("User", back_populates="generations")
    template: Mapped["Template"] = relationship("Template", back_populates="generations")
    
    __table_args__ = (
        Index("idx_generations_user_id", "user_id"),
        Index("idx_generations_template_id", "template_id"),
    )