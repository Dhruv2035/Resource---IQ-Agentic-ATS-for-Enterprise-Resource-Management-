"""
parser.py
Multimodal layout parsing.

"Multimodal" here means the parser doesn't just read plain text -- it also
reads the *visual layout* of the document:
  - font sizes / boldness (to guess headings vs body text)
  - x/y block positions (to detect multi-column layouts, a known ATS killer)
  - embedded images/graphics (icons, profile photos -> ATS red flag)
  - tables (ATS parsers frequently scramble table content)

Supported inputs: PDF (via PyMuPDF), DOCX (via python-docx), and plain TXT.
If a PDF has no extractable text (i.e. it's a scanned image), we fall back
to OCR via pytesseract when available.
"""

import io
import re
from typing import Any, Dict, List

import fitz  # PyMuPDF
import docx

from skills_db import STANDARD_SECTIONS

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def _detect_sections(lines: List[str]) -> Dict[str, int]:
    """Return {section_name: line_index} for every standard section header found."""
    found = {}
    for idx, line in enumerate(lines):
        clean = line.strip().lower().rstrip(":")
        if clean in STANDARD_SECTIONS and len(clean) < 40:
            found[clean] = idx
    return found


def parse_pdf(file_bytes: bytes) -> Dict[str, Any]:
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    full_text_lines: List[str] = []
    font_sizes: List[float] = []
    has_images = False
    multi_column_pages = 0

    for page in doc:
        page_dict = page.get_text("dict")
        page_width = page.rect.width
        left_edges = []

        for block in page_dict.get("blocks", []):
            if block.get("type") == 1:
                has_images = True
                continue
            if block.get("type") != 0:
                continue

            block_lines = block.get("lines", [])
            if not block_lines:
                continue

            bbox = block["bbox"]
            left_edges.append(bbox[0])

            for line in block_lines:
                line_text = "".join(span["text"] for span in line["spans"]).strip()
                if line_text:
                    full_text_lines.append(line_text)
                for span in line["spans"]:
                    font_sizes.append(span["size"])

        # crude multi-column heuristic: if we see two clusters of left-edges
        # that are both > 15% of page width apart from the page's own left
        # margin, and each cluster repeats many times, it's probably columns.
        if left_edges:
            left_edges_sorted = sorted(left_edges)
            distinct = []
            for x in left_edges_sorted:
                if not distinct or x - distinct[-1] > page_width * 0.12:
                    distinct.append(x)
            if len(distinct) >= 2 and distinct[1] > page_width * 0.30:
                multi_column_pages += 1

        if page.get_images(full=True):
            has_images = True

    text = "\n".join(full_text_lines)

    # OCR fallback if almost nothing extracted (scanned resume)
    used_ocr = False
    if len(text.strip()) < 40 and OCR_AVAILABLE:
        used_ocr = True
        ocr_text_parts = []
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text_parts.append(pytesseract.image_to_string(img))
        text = "\n".join(ocr_text_parts)
        full_text_lines = [l for l in text.split("\n") if l.strip()]

    sections_found = _detect_sections(full_text_lines)

    layout_flags = {
        "has_images_or_icons": has_images,
        "possible_multi_column": multi_column_pages > 0,
        "avg_font_size": round(sum(font_sizes) / len(font_sizes), 2) if font_sizes else 0,
        "font_size_variety": len(set(round(f, 1) for f in font_sizes)),
        "page_count": doc.page_count,
        "used_ocr_fallback": used_ocr,
    }

    return {
        "raw_text": text,
        "lines": full_text_lines,
        "sections_found": sections_found,
        "layout_flags": layout_flags,
        "source_type": "pdf",
    }


def parse_docx(file_bytes: bytes) -> Dict[str, Any]:
    document = docx.Document(io.BytesIO(file_bytes))

    lines = []
    font_sizes = []
    has_images = bool(document.inline_shapes)
    has_tables = bool(document.tables)

    for para in document.paragraphs:
        txt = para.text.strip()
        if txt:
            lines.append(txt)
        for run in para.runs:
            if run.font.size:
                font_sizes.append(run.font.size.pt)

    # tables often hold a two-column "skills | tools" style layout that
    # confuses real ATS parsers, so we flag it explicitly
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                txt = cell.text.strip()
                if txt:
                    lines.append(txt)

    text = "\n".join(lines)
    sections_found = _detect_sections(lines)

    layout_flags = {
        "has_images_or_icons": has_images,
        "possible_multi_column": False,  # not reliably detectable in docx via python-docx
        "has_tables": has_tables,
        "avg_font_size": round(sum(font_sizes) / len(font_sizes), 2) if font_sizes else 0,
        "font_size_variety": len(set(round(f, 1) for f in font_sizes)),
        "page_count": None,
        "used_ocr_fallback": False,
    }

    return {
        "raw_text": text,
        "lines": lines,
        "sections_found": sections_found,
        "layout_flags": layout_flags,
        "source_type": "docx",
    }


def parse_txt(file_bytes: bytes) -> Dict[str, Any]:
    text = file_bytes.decode("utf-8", errors="ignore")
    lines = [l for l in text.split("\n") if l.strip()]
    sections_found = _detect_sections(lines)
    layout_flags = {
        "has_images_or_icons": False,
        "possible_multi_column": False,
        "has_tables": False,
        "avg_font_size": 0,
        "font_size_variety": 0,
        "page_count": None,
        "used_ocr_fallback": False,
    }
    return {
        "raw_text": text,
        "lines": lines,
        "sections_found": sections_found,
        "layout_flags": layout_flags,
        "source_type": "txt",
    }


def parse_resume(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return parse_pdf(file_bytes)
    elif lower.endswith(".docx"):
        return parse_docx(file_bytes)
    elif lower.endswith(".txt"):
        return parse_txt(file_bytes)
    else:
        raise ValueError("Unsupported file type. Please upload a .pdf, .docx, or .txt resume.")
