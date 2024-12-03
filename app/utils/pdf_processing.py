from typing import List
from fastapi import UploadFile
import PyPDF2
import base64
import io

async def process_pdf(pdf: UploadFile) -> dict:
    
        pdf_data = await pdf.read()
        pdf_file = io.BytesIO(pdf_data)
        
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        encoded_pdf = base64.b64encode(pdf_data).decode("utf-8")

        return encoded_pdf
