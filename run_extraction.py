"""CLI: PDFs im Scan-Ordner auslesen und kurz anzeigen."""

from __future__ import annotations

import sys
from pathlib import Path

from extraction.config import load_settings
from extraction.pipeline import extract_from_directory


def _preview(text: str, max_len: int = 120) -> str:
    """Kurzer Textausschnitt für die Konsole."""
    compact = " ".join(text.split())
    if len(compact) <= max_len:
        return compact
    return compact[: max_len - 3] + "..."


def main() -> int:
    project_root = Path(__file__).resolve().parent
    settings = load_settings(project_root / ".env")

    print(f"Scan-Verzeichnis: {settings.scan_directory}")
    print(f"MIN_DIRECT_TEXT_LENGTH={settings.min_direct_text_length}")
    print(f"OCR_LANGUAGE={settings.ocr_language}")
    print("-" * 60)

    try:
        documents = extract_from_directory(settings)
    except FileNotFoundError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1

    if not documents:
        print("Keine unterstützten Dokumentdateien gefunden.")
        return 0

    for doc in documents:
        print(f"Datei:        {doc.path.name}")
        print(f"order_number: {doc.order_number}")
        print(f"used_ocr:     {doc.used_ocr}")
        print(f"Vorschau:     {_preview(doc.text)}")
        print(f"Hinweise:     {'; '.join(doc.extraction_notes)}")
        print("-" * 60)

    print(f"Fertig: {len(documents)} Dokument(e) verarbeitet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
