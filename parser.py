import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import io
import logging

logger = logging.getLogger(__name__)


def extract_text(file_bytes):
    """
    Extracts text from a PDF file.
    Tries standard text extraction first; falls back to OCR if needed.
    """
    text = ""

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "

        # If extraction yielded too little text, try OCR
        if len(text.strip()) < 50:
            logger.info("Standard extraction insufficient — switching to OCR.")
            images = convert_from_bytes(file_bytes)
            for img in images:
                text += pytesseract.image_to_string(img)

    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""

    return text.lower()