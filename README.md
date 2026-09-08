# Faculty Template Assistant

A RAG-powered chat agent that helps university faculty fill out recurring administrative documents (Word, Excel, PDF).

## Architecture

- **Backend**: Python + FastAPI
- **Orchestration**: Claude (Anthropic API) using tool use / function calling
- **Vector Store**: pgvector inside Postgres (single DB for metadata + embeddings)
- **Embeddings**: Voyage AI API
- **Document Generation**: python-docx for Word, openpyxl for Excel, pypdf for PDF forms
- **Frontend**: React + TypeScript chat UI
- **Auth**: Stub OIDC-based login (mock SSO for now, structured for real university IdP)
- **File Storage**: Local filesystem abstraction (swappable for S3)

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Anthropic API key
- Voyage AI API key

## Quick Start

### 1. Start the Database

```bash
cd infra
docker-compose up -d
```

This starts Postgres with pgvector on port 5432.

### 2. Configure Environment

Create `backend/.env`:

```env
# Database (matches docker-compose)
DATABASE_URL=postgresql+asyncpg://faculty_user:faculty_pass@localhost:5432/faculty_assistant

# Anthropic (get from https://console.anthropic.com)
ANTHROPIC_API_KEY=your-anthropic-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Voyage AI (get from https://www.voyageai.com)
VOYAGE_API_KEY=your-voyage-key
VOYAGE_MODEL=voyage-3
VOYAGE_EMBEDDING_DIM=1024

# File Storage
STORAGE_BASE_PATH=./storage
STORAGE_TYPE=local

# OIDC (mock for development)
OIDC_ISSUER_URL=https://mock-oidc.example.com
OIDC_CLIENT_ID=faculty-assistant
OIDC_CLIENT_SECRET=mock-secret
OIDC_REDIRECT_URI=http://localhost:3000/callback

# App
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
FRONTEND_URL=http://localhost:3000
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Seed the Database

```bash
cd backend
python -m app.scripts.seed
```

This creates:
- 4 demo users (faculty, dept_admin, system_admin)
- 4 templates (syllabus, travel reimbursement, leave request, grant budget)
- 4 policy chunks (travel, leave, grading, CS department)

### 5. Run the Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API available at http://localhost:8000
API docs at http://localhost:8000/docs

### 6. Install & Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at http://localhost:3000

## Demo Accounts

After seeding, use these emails to log in:

- `faculty@university.edu` - Dr. Jane Smith (CS Faculty)
- `prof.biology@university.edu` - Dr. Robert Johnson (Biology Faculty)  
- `dept.admin@university.edu` - Sarah Williams (Dept Admin)
- `admin@university.edu` - System Admin

## Usage

1. **Login** with one of the demo emails
2. **Chat** with the assistant - describe what document you need
3. **Answer questions** - the agent will ask for required fields
4. **Download** - generated documents appear as download links in chat

### Example Conversations

> "I need to create a syllabus for CS101 this fall"

> "Help me fill out a travel reimbursement for my conference trip to Boston last week"

> "I need to request a sabbatical leave for next semester"

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes
│   │   ├── core/          # Config, database
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── tools/         # Agent tools
│   │   └── scripts/       # Seed script
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom hooks
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript types
│   └── package.json
└── infra/
    ├── docker-compose.yml
    └── init.sql
```

## API Endpoints

### Chat
- `POST /api/chat` - Main conversational endpoint

### Admin (requires dept_admin or system_admin role)
- `POST /api/admin/templates` - Upload new template + metadata
- `GET /api/admin/templates` - List/manage templates
- `GET /api/admin/templates/search?q=` - Search templates
- `POST /api/admin/policy-docs` - Upload policy documents

### Generations
- `GET /api/generations/{user_id}` - Generation history

### Files
- `GET /api/files/{path}` - Download generated files

## Agent Tools

The Claude agent has access to these tools:

1. **search_templates(query)** - Find matching templates via vector similarity
2. **search_policy(query, department?)** - Search policy documents
3. **get_template_schema(template_id)** - Get required fields schema
4. **fill_template(template_id, field_values)** - Generate filled document
5. **get_faculty_profile(user_id)** - Get faculty data for auto-fill

## Adding Real SSO/HR Integration

The auth system is structured for easy swapping:

1. **OIDC**: Replace `mock_oidc_login` in `backend/app/api/auth.py` with real OIDC flow
2. **HR/Registrar**: Replace `FacultyProfileService.MOCK_PROFILES` in `backend/app/services/template_service.py` with real API calls

## Extending File Types

The `DocumentFiller` in `backend/app/services/document_filler.py` handles:
- **DOCX**: Placeholder replacement in paragraphs and tables
- **XLSX**: Placeholder replacement in cells
- **PDF**: AcroForm field filling

Add new types by extending the `fill_template` method.

## License

MIT