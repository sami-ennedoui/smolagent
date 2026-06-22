from __future__ import annotations

from pathlib import Path


def read_datasheet_text(path: str | Path) -> str:
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        return _read_pdf_text(path)
    return path.read_text(encoding="utf-8")


def _read_pdf_text(path: Path) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PDF input requires PyMuPDF. Install project requirements or pass extracted text."
        ) from exc

    with fitz.open(path) as document:
        return "\n".join(page.get_text() for page in document)
