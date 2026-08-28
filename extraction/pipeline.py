"""Pipeline: Datei → Text → Nummer → IncomingDocument."""

from __future__ import annotations

from pathlib import Path

from domain.models import IncomingDocument, Settings
from extraction.formats import SUPPORTED_LABEL, is_image_file, is_supported_document
from extraction.ocr import extract_text_via_ocr
from extraction.order_number import find_order_number
from extraction.pdf_text import extract_direct_text


def list_document_files(directory: Path) -> list[Path]:
    """Alle unterstützten Dokumentdateien im Ordner (auch Unterordner), sortiert."""
    if not directory.is_dir():
        raise FileNotFoundError(f"Scan-Verzeichnis nicht gefunden: {directory}")

    files = []
    for path in directory.rglob("*"):
        if path.is_file() and is_supported_document(path):
            files.append(path)
    return sorted(files)


def extract_single_document(path: Path | str, settings: Settings, allow_ocr: bool = True) -> IncomingDocument:
    """Ein Dokument auslesen und als IncomingDocument zurückgeben.

    PDFs: zuerst eingebetteter Text, bei zu wenig Text optional OCR.
    Fotos (PNG/JPG/WebP/TIFF): immer OCR, es gibt keinen eingebetteten Text.

    allow_ocr=False: OCR überspringen (Einstellung „OCR nach Import“).
    """
    doc_path = Path(path).resolve()
    notes: list[str] = []

    if not doc_path.is_file():
        raise FileNotFoundError(f"Datei nicht gefunden: {doc_path}")
    if not is_supported_document(doc_path):
        raise ValueError(f"Kein unterstütztes Format ({SUPPORTED_LABEL}): {doc_path}")

    text = ""
    used_ocr = False

    if is_image_file(doc_path):
        notes.append("Bilddatei: kein eingebetteter Text")
        if not allow_ocr:
            notes.append("OCR deaktiviert (Einstellungen)")
        else:
            notes.append("Bild → OCR")
            try:
                text = extract_text_via_ocr(doc_path, language=settings.ocr_language)
                used_ocr = True
                notes.append(f"OCR-Text: {len(text)} Zeichen")
            except Exception as exc:  # noqa: BLE001
                notes.append(f"OCR fehlgeschlagen: {exc}")
    else:
        # 1) Text direkt aus der PDF
        text = extract_direct_text(doc_path)
        notes.append(f"Direkter Text: {len(text)} Zeichen")

        # 2) Zu wenig Text? → OCR (sofern nicht deaktiviert)
        if not allow_ocr:
            notes.append("OCR deaktiviert (Einstellungen)")
        elif len(text) < settings.min_direct_text_length:
            notes.append("Zu wenig Text → OCR")
            try:
                text = extract_text_via_ocr(doc_path, language=settings.ocr_language)
                used_ocr = True
                notes.append(f"OCR-Text: {len(text)} Zeichen")
            except Exception as exc:  # noqa: BLE001
                notes.append(f"OCR fehlgeschlagen: {exc}")
        else:
            notes.append("OCR nicht nötig")

    order_number = find_order_number(text)
    if order_number:
        notes.append(f"Auftragsnummer: {order_number}")
    else:
        notes.append("Keine Auftragsnummer erkannt")

    return IncomingDocument(
        path=doc_path,
        text=text,
        order_number=order_number,
        used_ocr=used_ocr,
        extraction_notes=notes,
    )


def extract_from_directory(settings: Settings) -> list[IncomingDocument]:
    """Alle unterstützten Dokumente im Scan-Ordner verarbeiten (nur lesen)."""
    results = []
    for doc_path in list_document_files(settings.scan_directory):
        results.append(extract_single_document(doc_path, settings))
    return results
