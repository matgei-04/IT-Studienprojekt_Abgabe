"""Unterstützte Dokumentdateien: PDF plus gängige Fotoformate."""

from __future__ import annotations

from pathlib import Path

PDF_EXTENSIONS = frozenset({".pdf"})
IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"})
SUPPORTED_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS

# Reihenfolge für Dateiauswahl und Fehlermeldungen (PDF zuerst, dann Fotos).
HTML_ACCEPT = ".pdf,.png,.jpg,.jpeg,.webp,.tif,.tiff"
SUPPORTED_LABEL = "PDF, PNG, JPG, WebP und TIFF"

MIME_BY_SUFFIX = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


def suffix_of(path: Path | str) -> str:
    return Path(path).suffix.lower()


def is_pdf_file(path: Path | str) -> bool:
    return suffix_of(path) in PDF_EXTENSIONS


def is_image_file(path: Path | str) -> bool:
    return suffix_of(path) in IMAGE_EXTENSIONS


def is_supported_document(path: Path | str) -> bool:
    return suffix_of(path) in SUPPORTED_EXTENSIONS


def content_type_for(path: Path | str) -> str:
    return MIME_BY_SUFFIX.get(suffix_of(path), "application/octet-stream")
