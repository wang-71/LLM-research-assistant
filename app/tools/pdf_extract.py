import fitz  # PyMuPDF
from typing import Tuple, List

def extract_pdf_text(pdf_bytes: bytes, max_pages: int = 30) -> Tuple[str, List[str]]:
    """
    Returns:
      - full_text: concatenated text
      - page_texts: list of per-page text (1-indexed conceptually)
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_texts = []
    for i in range(min(len(doc), max_pages)):
        page = doc[i]
        page_texts.append(page.get_text("text"))
    full_text = "\n\n".join([f"[PAGE {i+1}]\n{t}" for i, t in enumerate(page_texts)])
    return full_text, page_texts
