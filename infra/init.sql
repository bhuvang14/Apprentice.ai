-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('faculty', 'dept_admin', 'system_admin')),
    department VARCHAR(100),
    oidc_sub VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Templates table
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    department VARCHAR(100),
    form_type VARCHAR(100),
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('docx', 'xlsx', 'pdf')),
    storage_path VARCHAR(500) NOT NULL,
    version INTEGER DEFAULT 1,
    required_fields JSONB NOT NULL DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Template embeddings table
CREATE TABLE template_embeddings (
    template_id UUID PRIMARY KEY REFERENCES templates(id) ON DELETE CASCADE,
    embedding VECTOR(1024) NOT NULL,
    source_text TEXT NOT NULL
);

-- Policy chunks table
CREATE TABLE policy_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_doc VARCHAR(255) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1024) NOT NULL,
    department VARCHAR(100),
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Generations audit log table
CREATE TABLE generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    template_version INTEGER NOT NULL,
    field_values JSONB NOT NULL,
    output_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for vector similarity search
CREATE INDEX idx_template_embeddings_embedding ON template_embeddings USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_policy_chunks_embedding ON policy_chunks USING hnsw (embedding vector_cosine_ops);

-- Indexes for common queries
CREATE INDEX idx_templates_department ON templates(department);
CREATE INDEX idx_templates_active ON templates(active);
CREATE INDEX idx_policy_chunks_department ON policy_chunks(department);
CREATE INDEX idx_generations_user_id ON generations(user_id);
CREATE INDEX idx_generations_template_id ON generations(template_id);
CREATE INDEX idx_users_oidc_sub ON users(oidc_sub);
CREATE INDEX idx_users_email ON users(email);