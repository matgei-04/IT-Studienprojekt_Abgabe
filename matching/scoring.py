"""Ähnlichkeit zwischen Dokument und DB-Auftrag berechnen.

Jedes Merkmal ist binär: 1.0 bei exakter Übereinstimmung, sonst 0.0.
Keine Teiltreffer / Wort-Überlappungen.
"""

from __future__ import annotations

from domain.models import IncomingDocument
from matching.models import Candidate, ScoreBreakdown

# Gewichtung des Matching-Scores (Summe = 1.0)
WEIGHT_ORDER = 0.60
WEIGHT_SENDER = 0.20
WEIGHT_RECEIVER = 0.20


def normalize(value: str | None) -> str:
    """Text vereinheitlichen: klein, ohne überflüssige Leerzeichen."""
    if not value:
        return ""
    return " ".join(value.casefold().split())


def exact_in_text(document_text: str, value: str | None) -> bool:
    """True nur wenn der DB-Wert vollständig im Dokumenttext vorkommt."""
    needle = normalize(value)
    haystack = normalize(document_text)
    if not needle or not haystack:
        return False
    return needle in haystack


def address_matches(
    document_text: str,
    name: str | None,
    street: str | None,
    plz: str | None,
    city: str | None,
) -> float:
    """Adresse: 1.0 wenn alle vorhandenen Felder exakt im Text stehen, sonst 0.0."""
    parts = [name, street, plz, city]
    present = [p for p in parts if normalize(p)]
    if not present:
        return 0.0
    if all(exact_in_text(document_text, p) for p in present):
        return 1.0
    return 0.0


def checklist_reasons(
    order_ok: bool,
    sender_ok: bool,
    receiver_ok: bool,
) -> list[str]:
    """Feste Checkliste: Auftragsnummer · Absender · Empfänger."""

    def line(label: str, ok: bool) -> str:
        return f"{'✓' if ok else '✗'} {label}"

    return [
        line("Auftragsnummer", order_ok),
        line("Absender", sender_ok),
        line("Empfänger", receiver_ok),
    ]


def score_candidate(
    document: IncomingDocument,
    candidate: Candidate,
) -> ScoreBreakdown:
    """Einen Kandidaten bewerten → total = Matching-Confidence (nur 0/1-Merkmale)."""
    result = ScoreBreakdown()
    text = document.text

    # 1) Auftragsnummer / ErfNr – exakt gleich
    if document.order_number and normalize(document.order_number) == normalize(
        candidate.erf_nr
    ):
        result.order_number = 1.0

    # 2) Absender – alle Adressfelder exakt
    result.sender = address_matches(
        text,
        candidate.sender_name,
        candidate.sender_street,
        candidate.sender_plz,
        candidate.sender_city,
    )

    # 3) Empfänger – alle Adressfelder exakt
    result.receiver = address_matches(
        text,
        candidate.receiver_name,
        candidate.receiver_street,
        candidate.receiver_plz,
        candidate.receiver_city,
    )

    result.reasons = checklist_reasons(
        order_ok=result.order_number == 1.0,
        sender_ok=result.sender == 1.0,
        receiver_ok=result.receiver == 1.0,
    )
    result.total = round(
        result.order_number * WEIGHT_ORDER
        + result.sender * WEIGHT_SENDER
        + result.receiver * WEIGHT_RECEIVER,
        3,
    )
    return result
