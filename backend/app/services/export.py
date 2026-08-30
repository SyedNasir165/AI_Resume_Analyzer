"""Resume export.

Exports contain only the resume text the user has already reviewed and approved — nothing is
generated or added here. Plain text is returned as-is; DOCX wraps each line in a paragraph so the
output stays plain, ATS-friendly, and text-extractable.
"""

import io
import re

from docx import Document
from fpdf import FPDF

# fpdf2's core fonts are latin-1 only; map the unicode punctuation Gemini commonly emits to ASCII
# so PDF generation never fails on a smart quote or em dash.
_UNICODE_REPLACEMENTS = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "•": "-", "…": "...", " ": " ",
}


def _latin1_safe(text: str) -> str:
    for src, dst in _UNICODE_REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "replace").decode("latin-1")


def to_txt_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def to_docx_bytes(text: str) -> bytes:
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def to_pdf_bytes(text: str) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for line in text.splitlines():
        safe = _latin1_safe(line)
        if safe.strip() == "":
            pdf.ln(4)
        else:
            # Use the explicit effective page width; break long unbroken tokens (e.g. long URLs or
            # emails) mid-word so they never overflow the available space.
            pdf.multi_cell(pdf.epw, 6, safe, wrapmode="CHAR", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def safe_filename(name: str, extension: str) -> str:
    """A conservative download filename derived from the resume name."""
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", (name or "resume").strip()) or "resume"
    base = base.rsplit(".", 1)[0]  # drop any existing extension
    return f"{base}.{extension}"
