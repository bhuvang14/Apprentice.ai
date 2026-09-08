import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, BinaryIO
from docx import Document
from docx.shared import Inches
from openpyxl import load_workbook
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject

from app.services.storage import get_storage


class DocumentFiller:
    def __init__(self):
        self.storage = get_storage()
    
    def validate_fields(self, required_fields: Dict[str, Any], provided_fields: Dict[str, Any]) -> tuple[bool, list[str]]:
        missing = []
        for field_name, field_schema in required_fields.items():
            if field_schema.get("required", True) and field_name not in provided_fields:
                missing.append(field_name)
        return len(missing) == 0, missing
    
    def fill_docx(self, template_path: str, field_values: Dict[str, Any], output_path: str) -> str:
        doc = Document(template_path)
        
        for paragraph in doc.paragraphs:
            for key, value in field_values.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in paragraph.text:
                    for run in paragraph.runs:
                        if placeholder in run.text:
                            run.text = run.text.replace(placeholder, str(value))
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for key, value in field_values.items():
                            placeholder = f"{{{{{key}}}}}"
                            if placeholder in paragraph.text:
                                for run in paragraph.runs:
                                    if placeholder in run.text:
                                        run.text = run.text.replace(placeholder, str(value))
        
        doc.save(output_path)
        return output_path
    
    def fill_xlsx(self, template_path: str, field_values: Dict[str, Any], output_path: str) -> str:
        wb = load_workbook(template_path)
        
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for cell in row:
                    if cell.value and isinstance(cell.value, str):
                        for key, value in field_values.items():
                            placeholder = f"{{{{{key}}}}}"
                            if placeholder in cell.value:
                                cell.value = cell.value.replace(placeholder, str(value))
        
        wb.save(output_path)
        return output_path
    
    def fill_pdf(self, template_path: str, field_values: Dict[str, Any], output_path: str) -> str:
        reader = PdfReader(template_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        if "/AcroForm" in reader.trailer["/Root"]:
            writer._root_object.update({
                NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]
            })
        
        for page in writer.pages:
            if "/Annots" in page:
                for annot in page["/Annots"]:
                    annot_obj = annot.get_object()
                    if annot_obj.get("/Subtype") == "/Widget" and "/T" in annot_obj:
                        field_name = annot_obj["/T"]
                        if field_name in field_values:
                            annot_obj.update({
                                NameObject("/V"): TextStringObject(str(field_values[field_name])),
                                NameObject("/Ff"): 1,
                            })
        
        writer.write(output_path)
        return output_path
    
    def fill_template(self, template_id: str, file_type: str, storage_path: str, field_values: Dict[str, Any], required_fields: Dict[str, Any]) -> str:
        valid, missing = self.validate_fields(required_fields, field_values)
        if not valid:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_template:
            template_file = self.storage.get(storage_path)
            tmp_template.write(template_file.read())
            template_file.close()
            template_path = tmp_template.name
        
        output_filename = f"filled_{template_id}_{os.path.basename(storage_path)}"
        output_path = f"outputs/{output_filename}"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_output:
            output_temp_path = tmp_output.name
        
        try:
            if file_type == "docx":
                self.fill_docx(template_path, field_values, output_temp_path)
            elif file_type == "xlsx":
                self.fill_xlsx(template_path, field_values, output_temp_path)
            elif file_type == "pdf":
                self.fill_pdf(template_path, field_values, output_temp_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            with open(output_temp_path, "rb") as f:
                self.storage.save(output_path, f)
            
            return output_path
        finally:
            if os.path.exists(template_path):
                os.unlink(template_path)
            if os.path.exists(output_temp_path):
                os.unlink(output_temp_path)


document_filler = DocumentFiller()