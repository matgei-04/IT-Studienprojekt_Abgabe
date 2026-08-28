"""Datenmodelle für Matching."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Candidate:
    """Ein möglicher Auftrag aus der Datenbank."""

    erf_nr: str
    referenz: str | None = None
    sender_name: str | None = None
    sender_street: str | None = None
    sender_plz: str | None = None
    sender_city: str | None = None
    receiver_name: str | None = None
    receiver_street: str | None = None
    receiver_plz: str | None = None
    receiver_city: str | None = None


@dataclass
class ScoreBreakdown:
    """Einzelteile des Matching-Scores."""

    order_number: float = 0.0
    sender: float = 0.0
    receiver: float = 0.0
    total: float = 0.0
    reasons: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    """Matching-Ergebnis. confidence = Matching-Score (0.0–1.0)."""

    erf_nr: str | None
    confidence: float
    candidate: Candidate | None
    breakdown: ScoreBreakdown
    matched: bool
