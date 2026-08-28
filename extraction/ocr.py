"""OCR-Fallback: PDF-Seiten oder Fotos als Bild lesen (Tesseract)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageOps

from extraction.formats import is_image_file
from extraction.pdf_text import clean_extracted_text

_TESSERACT_CONFIGURED = False


def _configure_tesseract() -> None:
    """Setzt unter Windows den Tesseract-Pfad, falls er nicht im PATH liegt."""
    global _TESSERACT_CONFIGURED
    if _TESSERACT_CONFIGURED:
        return
    _TESSERACT_CONFIGURED = True

    env_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if env_cmd and Path(env_cmd).is_file():
        pytesseract.pytesseract.tesseract_cmd = env_cmd
        return

    if not sys.platform.startswith("win"):
        return

    candidates = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return


def extract_text_via_ocr(path: Path, language: str = "deu") -> str:
    """Datei → Bild(er) → Text mit Tesseract."""
    _configure_tesseract()
    path = Path(path)
    if is_image_file(path):
        return _ocr_image(path, language)
    return _ocr_pdf(path, language)


def _ocr_image(image_path: Path, language: str) -> str:
    with Image.open(image_path) as image:
        oriented = ImageOps.exif_transpose(image) or image
        rgb = oriented.convert("RGB")
        text = pytesseract.image_to_string(rgb, lang=language) or ""
    return clean_extracted_text(text)


def _ocr_pdf(pdf_path: Path, language: str) -> str:
    """Seite → Bild → Text mit Tesseract."""
    page_texts = []
    # 2x Vergrößerung = bessere Erkennung
    zoom = fitz.Matrix(2.0, 2.0)

    with fitz.open(pdf_path) as document:
        for page in document:
            pixmap = page.get_pixmap(matrix=zoom, alpha=False)
            image = Image.frombytes(
                "RGB",
                (pixmap.width, pixmap.height),
                pixmap.samples,
            )
            text = pytesseract.image_to_string(image, lang=language) or ""
            if text.strip():
                page_texts.append(text.strip())

    return clean_extracted_text("\n".join(page_texts))
