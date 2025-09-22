import pdfplumber
import docx

def read_pdf(file_path):
    """Read PDF and return text."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def read_docx(file_path):
    """Read DOCX and return text."""
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text
