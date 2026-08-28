"""Kandidaten in Supabase suchen."""

from __future__ import annotations

from typing import Any

from supabase import Client

from matching.models import Candidate
from matching.scoring import exact_in_text, normalize


class CandidateRepository:
    """Liest Aufträge und Adressen aus der Spedifix-DB."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def find_by_order_number(self, order_number: str) -> list[Candidate]:
        """Sucht Sendungen mit passender ErfNr (nicht storniert)."""
        response = (
            self.supabase.table("3100_Sdg_Haupt")
            .select("*")
            .eq("ErfNr", str(order_number))
            .eq("Storno", "0")
            .execute()
        )
        return self._candidates_from_haupt(response.data)

    def find_by_address_text(self, document_text: str) -> list[Candidate]:
        """Sendungen, deren Absender- oder Empfängername im Dokument vorkommt.

        Fallback, wenn keine Auftragsnummer erkannt wurde: nicht alle Aufträge
        bewerten, sondern nur die, deren Firmenname exakt im Text steht.
        """
        erf_nrs = self._erf_nrs_with_name_in_text(document_text)
        if not erf_nrs:
            return []
        response = (
            self.supabase.table("3100_Sdg_Haupt")
            .select("*")
            .in_("ErfNr", list(erf_nrs))
            .eq("Storno", "0")
            .execute()
        )
        return self._candidates_from_haupt(response.data)

    def _erf_nrs_with_name_in_text(self, document_text: str) -> list[str]:
        response = (
            self.supabase.table("3100_Sdg_Adressen")
            .select("ErfNr, Name1")
            .execute()
        )
        found: list[str] = []
        seen: set[str] = set()
        for row in response.data or []:
            name = row.get("Name1")
            if len(normalize(name)) < 6:
                continue
            if not exact_in_text(document_text, name):
                continue
            erf_nr = str(row.get("ErfNr") or "")
            if not erf_nr or erf_nr in seen:
                continue
            seen.add(erf_nr)
            found.append(erf_nr)
        return found

    def _candidates_from_haupt(self, rows: list[dict[str, Any]] | None) -> list[Candidate]:
        candidates = []
        for row in rows or []:
            candidate = self._build_candidate(row)
            self._load_addresses(candidate)
            candidates.append(candidate)
        return candidates

    def _build_candidate(self, row: dict[str, Any]) -> Candidate:
        """Zeile aus 3100_Sdg_Haupt → Candidate."""
        return Candidate(
            erf_nr=str(row.get("ErfNr", "")),
            referenz=row.get("Ref-1"),
        )

    def _load_addresses(self, candidate: Candidate) -> None:
        """Absender/Empfänger zur ErfNr laden."""
        response = (
            self.supabase.table("3100_Sdg_Adressen")
            .select("*")
            .eq("ErfNr", candidate.erf_nr)
            .execute()
        )
        for row in response.data:
            self._add_address(candidate, row)

    @staticmethod
    def _add_address(candidate: Candidate, row: dict[str, Any]) -> None:
        """Art 1 = Absender, Art 2 = Empfänger."""
        art = str(row.get("Art", "")).strip()

        if art == "1":
            candidate.sender_name = row.get("Name1")
            candidate.sender_street = row.get("Strasse")
            candidate.sender_plz = row.get("Plz")
            candidate.sender_city = row.get("Ort")
        elif art == "2":
            candidate.receiver_name = row.get("Name1")
            candidate.receiver_street = row.get("Strasse")
            candidate.receiver_plz = row.get("Plz")
            candidate.receiver_city = row.get("Ort")
