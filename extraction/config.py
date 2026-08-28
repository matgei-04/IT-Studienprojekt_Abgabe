"""Einstellungen aus der .env-Datei laden."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from domain.models import Settings


def load_settings(env_path: Path | None = None) -> Settings:
    """Liest SCAN_DIRECTORY, MIN_DIRECT_TEXT_LENGTH und OCR_LANGUAGE."""
    if env_path is not None:
        load_dotenv(env_path)
    else:
        load_dotenv()

    scan_directory = Path(
        os.getenv("SCAN_DIRECTORY", "./eingang")
    ).expanduser().resolve()

    min_text = os.getenv("MIN_DIRECT_TEXT_LENGTH", "40")
    try:
        min_direct_text_length = int(min_text)
    except ValueError as exc:
        raise ValueError(
            f"MIN_DIRECT_TEXT_LENGTH muss eine Zahl sein, nicht: {min_text}"
        ) from exc

    ocr_language = os.getenv("OCR_LANGUAGE", "deu")

    return Settings(
        scan_directory=scan_directory,
        min_direct_text_length=min_direct_text_length,
        ocr_language=ocr_language,
    )
