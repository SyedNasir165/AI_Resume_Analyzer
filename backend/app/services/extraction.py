import io
from dataclasses import dataclass, field

import pdfplumber
from docx import Document

SHORT_TEXT_WARNING_THRESHOLD = 100


class ExtractionError(Exception):
    """Raised when a file cannot be parsed at all (corrupt, password-protected, etc.)."""


@dataclass
class ExtractionResult:
    text: str
    warnings: list[str] = field(default_factory=list)


def _with_short_text_warning(result: ExtractionResult) -> ExtractionResult:
    if 0 < len(result.text) < SHORT_TEXT_WARNING_THRESHOLD:
        result.warnings.append(
            "The extracted text is unusually short for a resume — please review it carefully before confirming."
        )
    return result


def extract_pdf(content: bytes) -> ExtractionResult:
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
    except Exception as exc:
        raise ExtractionError(
            "This PDF could not be read. It may be corrupted, password-protected, or in an unsupported format."
        ) from exc

    text = "\n\n".join(page.strip() for page in pages_text if page.strip()).strip()
    warnings: list[str] = []

    if not text:
        warnings.append(
            "No text could be extracted from this PDF. It may be a scanned or image-based document, "
            "which this analyzer does not support yet — try pasting the text directly instead."
        )

    return _with_short_text_warning(ExtractionResult(text=text, warnings=warnings))


def extract_docx(content: bytes) -> ExtractionResult:
    try:
        document = Document(io.BytesIO(content))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
    except Exception as exc:
        raise ExtractionError(
            "This DOCX file could not be read. It may be corrupted or in an unsupported format."
        ) from exc

    text = "\n".join(paragraphs).strip()
    warnings: list[str] = []

    if not text:
        warnings.append("No text could be extracted from this document.")

    return _with_short_text_warning(ExtractionResult(text=text, warnings=warnings))


def extract_txt(content: bytes) -> ExtractionResult:
    warnings: list[str] = []

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
            warnings.append(
                "This file was not valid UTF-8 text, so some characters may not have decoded correctly."
            )
        except Exception as exc:
            raise ExtractionError("This text file could not be read.") from exc

    text = text.strip()

    if not text:
        warnings.append("This file appears to be empty.")

    return _with_short_text_warning(ExtractionResult(text=text, warnings=warnings))
