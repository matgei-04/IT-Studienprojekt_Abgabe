"""CLI: Extraktion + Matching (immer manuelle Bestätigung)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from extraction import extract_from_directory
from extraction.config import load_settings
from matching.candidate_search import CandidateRepository
from matching.matcher import DocumentMatcher


def main() -> int:
    project_root = Path(__file__).resolve().parent
    load_dotenv(project_root / ".env")
    settings = load_settings(project_root / ".env")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("Fehler: SUPABASE_URL und SUPABASE_KEY in .env setzen.", file=sys.stderr)
        return 1

    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as exc:
        print(f"Supabase-Verbindung fehlgeschlagen: {exc}", file=sys.stderr)
        return 1

    matcher = DocumentMatcher(CandidateRepository(supabase))

    try:
        documents = extract_from_directory(settings)
    except Exception as exc:
        print(f"Extraktion fehlgeschlagen: {exc}", file=sys.stderr)
        return 1

    if not documents:
        print("Keine unterstützten Dokumentdateien gefunden.")
        return 0

    for document in documents:
        print("=" * 70)
        print(f"Dokument:            {document.path.name}")
        print(f"order_number:        {document.order_number}")
        print(f"OCR:                 {document.used_ocr}")
        print("-" * 70)

        try:
            result = matcher.match(document)
        except Exception as exc:
            print(f"Matching fehlgeschlagen: {exc}")
            continue

        print(f"Vorschlag ErfNr:     {result.erf_nr}")
        print(f"Confidence:          {result.confidence:.3f}")
        print("Status:              Vorschlag – manuelle Bestätigung erforderlich")
        print(f"Brauchbarer Treffer: {result.matched}")

        print("-" * 70)
        print("Score:")
        print(f"  Auftragsnummer:    {result.breakdown.order_number:.3f}")
        print(f"  Absender:          {result.breakdown.sender:.3f}")
        print(f"  Empfänger:         {result.breakdown.receiver:.3f}")
        print(f"  Gesamt:            {result.breakdown.total:.3f}")

        for reason in result.breakdown.reasons:
            print(f"  - {reason}")

        if result.candidate:
            c = result.candidate
            print("-" * 70)
            print(f"DB Absender:         {c.sender_name}")
            print(f"DB Empfänger:        {c.receiver_name}")
            print(f"DB Referenz:         {c.referenz}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
