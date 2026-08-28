"""Strukturierte Ergebnis- und Konfigurationsobjekte der Extraktion."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class IncomingDocument:
    """Ergebnis der Extraktion für ein einzelnes Dokument (PDF oder Foto)."""

    path: Path
    text: str
    order_number: str | None
    used_ocr: bool
    extraction_notes: list[str] = field(default_factory=list)


@dataclass
class Settings:
    """Laufzeit-Einstellungen (typischerweise aus .env)."""

    scan_directory: Path
    min_direct_text_length: int = 40
    ocr_language: str = "deu"
