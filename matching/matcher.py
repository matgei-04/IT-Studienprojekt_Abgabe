"""Matching: Dokument einem Auftrag zuordnen (Vorschlag)."""

from __future__ import annotations

from domain.models import IncomingDocument
from matching.candidate_search import CandidateRepository
from matching.models import MatchResult, ScoreBreakdown
from matching.scoring import checklist_reasons, score_candidate

# Untergrenze für „brauchbarer Treffer“ – gleich der App-Ampel „Prüfung“ (60 %).
MIN_MATCH_SCORE = 0.60


class DocumentMatcher:
    """
    Sucht zuerst über die erkannte Auftragsnummer (ErfNr).
    Fehlt die Nummer, Fallback über Absender-/Empfängernamen im Text.
    Vorschläge werden immer manuell bestätigt (confirm_assignment).
    """

    def __init__(self, repository: CandidateRepository, min_score: float = MIN_MATCH_SCORE):
        self.repository = repository
        self.min_score = min_score

    def match(self, document: IncomingDocument) -> MatchResult:
        if document.order_number:
            candidates = self.repository.find_by_order_number(document.order_number)
        else:
            candidates = self.repository.find_by_address_text(document.text)

        empty_checklist = checklist_reasons(False, False, False)

        if not candidates:
            return MatchResult(
                erf_nr=None,
                confidence=0.0,
                candidate=None,
                breakdown=ScoreBreakdown(reasons=empty_checklist),
                matched=False,
            )

        ranked = []
        for candidate in candidates:
            breakdown = score_candidate(document, candidate)
            if breakdown.total <= 0:
                continue
            ranked.append((breakdown.total, candidate, breakdown))

        if not ranked:
            return MatchResult(
                erf_nr=None,
                confidence=0.0,
                candidate=None,
                breakdown=ScoreBreakdown(reasons=empty_checklist),
                matched=False,
            )

        ranked.sort(key=lambda item: item[0], reverse=True)
        best_score, best_candidate, best_breakdown = ranked[0]

        return MatchResult(
            erf_nr=best_candidate.erf_nr,
            confidence=best_score,
            candidate=best_candidate,
            breakdown=best_breakdown,
            matched=best_score >= self.min_score,
        )
