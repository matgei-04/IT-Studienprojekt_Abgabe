"""Text direkt aus einer PDF lesen (ohne OCR)."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def extract_direct_text(pdf_path: Path) -> str:
    """Liest den eingebetteten Text aller Seiten."""
    pages = []
    with fitz.open(pdf_path) as document:
        for page in document:
            pages.append(page.get_text("text") or "")

    return clean_extracted_text("\n".join(pages))


def clean_extracted_text(text: str) -> str:
    """Doppelte Leerzeichen entfernen, leere Zeilen weglassen."""
    clean_lines = []
    for line in text.splitlines():
        line = " ".join(line.split())
        if line:
            clean_lines.append(line)
    return "\n".join(clean_lines).strip()
