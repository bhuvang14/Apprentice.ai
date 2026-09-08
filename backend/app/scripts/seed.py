import asyncio
import json
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, init_db
from app.models import User, Template, TemplateEmbedding, PolicyChunk
from app.services.embeddings import embedding_service
from app.services.storage import get_storage


async def seed_users(db: AsyncSession):
    users_data = [
        {
            "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
            "name": "Dr. Jane Smith",
            "email": "faculty@university.edu",
            "role": "faculty",
            "department": "Computer Science",
            "oidc_sub": "mock-oidc-faculty-001",
        },
        {
            "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
            "name": "Dr. Robert Johnson",
            "email": "prof.biology@university.edu",
            "role": "faculty",
            "department": "Biology",
            "oidc_sub": "mock-oidc-faculty-002",
        },
        {
            "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
            "name": "Ms. Sarah Williams",
            "email": "dept.admin@university.edu",
            "role": "dept_admin",
            "department": "Computer Science",
            "oidc_sub": "mock-oidc-admin-001",
        },
        {
            "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
            "name": "System Admin",
            "email": "admin@university.edu",
            "role": "system_admin",
            "department": "IT",
            "oidc_sub": "mock-oidc-admin-002",
        },
    ]
    
    for user_data in users_data:
        user = User(**user_data)
        db.add(user)
    
    await db.commit()
    print("Seeded users")


async def create_mock_template_file(file_type: str, template_name: str) -> bytes:
    if file_type == "docx":
        from docx import Document
        doc = Document()
        doc.add_heading(template_name, 0)
        doc.add_paragraph("Faculty Name: {{faculty_name}}")
        doc.add_paragraph("Department: {{department}}")
        doc.add_paragraph("Course: {{course_name}}")
        doc.add_paragraph("Semester: {{semester}}")
        doc.add_paragraph("Office Hours: {{office_hours}}")
        doc.add_paragraph("Grading Policy: {{grading_policy}}")
        
        import io
        buffer = io.BytesIO()
        doc.save(buffer)
        return buffer.getvalue()
    
    elif file_type == "xlsx":
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Reimbursement"
        ws.append(["Field", "Value"])
        ws.append(["Faculty Name", "{{faculty_name}}"])
        ws.append(["Department", "{{department}}"])
        ws.append(["Travel Date", "{{travel_date}}"])
        ws.append(["Destination", "{{destination}}"])
        ws.append(["Purpose", "{{purpose}}"])
        ws.append(["Amount", "{{amount}}"])
        ws.append(["Account Code", "{{account_code}}"])
        
        import io
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()
    
    elif file_type == "pdf":
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject, NameObject
        
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        
        # Add form fields
        writer.add_blank_page(width=612, height=792)
        
        import io
        buffer = io.BytesIO()
        writer.write(buffer)
        return buffer.getvalue()
    
    return b""


async def seed_templates(db: AsyncSession):
    storage = get_storage()
    
    templates_data = [
        {
            "id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            "name": "Course Syllabus Template",
            "description": "Standard syllabus template for all courses",
            "department": "Computer Science",
            "form_type": "syllabus",
            "file_type": "docx",
            "storage_path": "",
            "version": 1,
            "required_fields": {
                "faculty_name": {"type": "string", "required": True, "description": "Instructor's full name"},
                "department": {"type": "string", "required": True, "description": "Department name"},
                "course_name": {"type": "string", "required": True, "description": "Course title"},
                "course_code": {"type": "string", "required": True, "description": "Course code (e.g., CS101)"},
                "semester": {"type": "string", "required": True, "description": "Semester (e.g., Fall 2024)"},
                "office_hours": {"type": "string", "required": False, "description": "Office hours schedule"},
                "grading_policy": {"type": "string", "required": True, "description": "Grading breakdown"},
                "textbook": {"type": "string", "required": False, "description": "Required textbook"},
            },
            "active": True,
        },
        {
            "id": uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            "name": "Travel Reimbursement Form",
            "description": "Faculty travel expense reimbursement",
            "department": None,
            "form_type": "reimbursement",
            "file_type": "xlsx",
            "storage_path": "",
            "version": 1,
            "required_fields": {
                "faculty_name": {"type": "string", "required": True, "description": "Faculty member name"},
                "department": {"type": "string", "required": True, "description": "Department"},
                "travel_date": {"type": "string", "required": True, "description": "Travel date (YYYY-MM-DD)"},
                "destination": {"type": "string", "required": True, "description": "Travel destination"},
                "purpose": {"type": "string", "required": True, "description": "Purpose of travel"},
                "amount": {"type": "number", "required": True, "description": "Total amount to reimburse"},
                "account_code": {"type": "string", "required": True, "description": "Budget account code"},
            },
            "active": True,
        },
        {
            "id": uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
            "name": "Leave Request Form",
            "description": "Faculty leave of absence request",
            "department": None,
            "form_type": "leave_request",
            "file_type": "pdf",
            "storage_path": "",
            "version": 1,
            "required_fields": {
                "faculty_name": {"type": "string", "required": True, "description": "Faculty member name"},
                "department": {"type": "string", "required": True, "description": "Department"},
                "leave_type": {"type": "string", "required": True, "description": "Type of leave (sick, vacation, sabbatical, etc.)"},
                "start_date": {"type": "string", "required": True, "description": "Leave start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "required": True, "description": "Leave end date (YYYY-MM-DD)"},
                "reason": {"type": "string", "required": False, "description": "Reason for leave"},
            },
            "active": True,
        },
        {
            "id": uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
            "name": "Grant Budget Template",
            "description": "Budget template for grant applications",
            "department": None,
            "form_type": "grant_budget",
            "file_type": "xlsx",
            "storage_path": "",
            "version": 1,
            "required_fields": {
                "pi_name": {"type": "string", "required": True, "description": "Principal Investigator name"},
                "department": {"type": "string", "required": True, "description": "Department"},
                "grant_title": {"type": "string", "required": True, "description": "Grant proposal title"},
                "funding_agency": {"type": "string", "required": True, "description": "Funding agency name"},
                "total_budget": {"type": "number", "required": True, "description": "Total budget amount"},
                "project_start": {"type": "string", "required": True, "description": "Project start date"},
                "project_end": {"type": "string", "required": True, "description": "Project end date"},
            },
            "active": True,
        },
    ]
    
    for template_data in templates_data:
        file_content = await create_mock_template_file(template_data["file_type"], template_data["name"])
        
        import io
        file_obj = io.BytesIO(file_content)
        storage_path = f"templates/{template_data['id']}_{template_data['name'].replace(' ', '_')}.{template_data['file_type']}"
        storage.save(storage_path, file_obj)
        
        template_data["storage_path"] = storage_path
        
        embedding = embedding_service.embed_template(
            name=template_data["name"],
            description=template_data["description"] or "",
            form_type=template_data["form_type"] or "",
            required_fields=template_data["required_fields"],
        )
        
        template = Template(**template_data)
        db.add(template)
        await db.flush()
        
        template_embedding = TemplateEmbedding(
            template_id=template.id,
            embedding=embedding,
            source_text=f"Template: {template_data['name']}\nDescription: {template_data['description'] or ''}\nType: {template_data['form_type'] or ''}\nFields: {', '.join(template_data['required_fields'].keys())}",
        )
        db.add(template_embedding)
    
    await db.commit()
    print("Seeded templates")


async def seed_policies(db: AsyncSession):
    policies_text = [
        {
            "source_doc": "University Travel Policy",
            "chunk_text": "All faculty travel must be pre-approved by the department chair. Reimbursement rates: $0.65/mile for personal vehicle, actual cost for airfare (economy class), $75/day per diem for meals. International travel requires Dean approval 30 days in advance. All receipts must be submitted within 30 days of return.",
            "department": None,
            "tags": ["travel", "reimbursement", "policy"],
        },
        {
            "source_doc": "University Leave Policy",
            "chunk_text": "Faculty are entitled to: 12 sick days per year (accrues at 1 day/month), 15 vacation days per year, 1 semester sabbatical after 7 years of service. Leave requests must be submitted at least 2 weeks in advance for planned leave. Emergency leave requires notification within 24 hours. Sabbatical leave requires a formal proposal approved by Dean and Provost.",
            "department": None,
            "tags": ["leave", "sabbatical", "policy"],
        },
        {
            "source_doc": "Faculty Grading Policy",
            "chunk_text": "Final grades must be submitted within 72 hours of final exam. Grade distribution guidelines: A: 20-30%, B: 30-40%, C: 20-30%, D/F: 10-15%. Incomplete grades (I) must be resolved within one semester. Grade changes after submission require department chair approval with documented justification.",
            "department": None,
            "tags": ["grading", "grades", "policy"],
        },
        {
            "source_doc": "Computer Science Department Policy",
            "chunk_text": "CS faculty must hold office hours minimum 3 hours/week during teaching semesters. Course syllabi must be posted to LMS at least 1 week before semester start. All CS courses must include at least one programming assignment. Final exams must be comprehensive covering all course material.",
            "department": "Computer Science",
            "tags": ["cs", "department", "syllabus", "office_hours"],
        },
    ]
    
    for policy in policies_text:
        embedding = embedding_service.embed_policy_chunk(policy["chunk_text"])
        
        policy_chunk = PolicyChunk(
            source_doc=policy["source_doc"],
            chunk_text=policy["chunk_text"],
            embedding=embedding,
            department=policy["department"],
            tags=policy["tags"],
        )
        db.add(policy_chunk)
    
    await db.commit()
    print("Seeded policies")


async def main():
    await init_db()
    
    async with AsyncSessionLocal() as db:
        await seed_users(db)
        await seed_templates(db)
        await seed_policies(db)
    
    print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())