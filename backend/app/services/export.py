"""Resume export.

Exports contain only the resume text the user has already reviewed and approved — nothing is
generated or added here. Plain text is returned as-is; DOCX wraps each line in a paragraph so the
output stays plain, ATS-friendly, and text-extractable.
"""

import io
import re

from docx import Document


def to_txt_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def to_docx_bytes(text: str) -> bytes:
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def safe_filename(name: str, extension: str) -> str:
    """A conservative download filename derived from the resume name."""
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", (name or "resume").strip()) or "resume"
    base = base.rsplit(".", 1)[0]  # drop any existing extension
    return f"{base}.{extension}"
