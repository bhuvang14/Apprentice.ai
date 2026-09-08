import re
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document
from openpyxl import load_workbook


class DocumentChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                break_point = max(last_period, last_newline)
                if break_point > start:
                    end = break_point + 1
            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        return [c for c in chunks if c]
    
    def extract_pdf_text(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def extract_docx_text(self, file_path: str) -> str:
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        for table in doc.tables:
            for row in table.rows:
                text += " | ".join(cell.text for cell in row.cells) + "\n"
        return text
    
    def extract_xlsx_text(self, file_path: str) -> str:
        wb = load_workbook(file_path, read_only=True)
        text = ""
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            text += f"Sheet: {sheet_name}\n"
            for row in ws.iter_rows(values_only=True):
                text += " | ".join(str(c) for c in row if c is not None) + "\n"
        return text
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        if file_type == "pdf":
            return self.extract_pdf_text(file_path)
        elif file_type == "docx":
            return self.extract_docx_text(file_path)
        elif file_type == "xlsx":
            return self.extract_xlsx_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def process_document(self, file_path: str, file_type: str, source_doc: str, department: str = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        text = self.extract_text(file_path, file_type)
        chunks = self.chunk_text(text)
        
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                "source_doc": source_doc,
                "chunk_text": chunk,
                "department": department,
                "tags": tags or [],
                "chunk_index": i,
            })
        return result


chunker = DocumentChunker()