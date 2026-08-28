"""Auftragsnummer (ErfNr) im Text finden – nur Label direkt vor der Zahl."""

from __future__ import annotations

import re

from extraction.labels import LabelConfig, load_labels

_pattern_cache_key: tuple[str, ...] | None = None
_pattern_cache: re.Pattern[str] | None = None


def _label_to_pattern(label: str) -> str | None:
    """Ein Label → Regex-Fragment (flexible Leerzeichen/Punkte/Bindestriche)."""
    tokens = re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", label)
    if not tokens:
        return None
    parts = [re.escape(t) for t in tokens]
    return r"[\s.\-]*".join(parts) + r"\.?"


def build_order_number_pattern(labels: list[str]) -> re.Pattern[str]:
    """Baut die Such-Regex aus konfigurierbaren Labels (längere zuerst)."""
    fragments: list[str] = []
    seen: set[str] = set()
    for label in labels:
        frag = _label_to_pattern(label)
        if not frag or frag.casefold() in seen:
            continue
        seen.add(frag.casefold())
        fragments.append(frag)

    if not fragments:
        fragments = ["auftrag"]

    fragments.sort(key=len, reverse=True)
    alternation = "|".join(f"(?:{f})" for f in fragments)
    return re.compile(
        rf"(?:{alternation})[\s:.\-]*(\d{{3,6}})(?!\d)",
        re.IGNORECASE,
    )


def _get_pattern(config: LabelConfig | None = None) -> re.Pattern[str]:
    global _pattern_cache_key, _pattern_cache
    cfg = config or load_labels()
    key = tuple(cfg.order_labels)
    if _pattern_cache is not None and _pattern_cache_key == key:
        return _pattern_cache
    pattern = build_order_number_pattern(cfg.order_labels)
    _pattern_cache_key = key
    _pattern_cache = pattern
    return pattern


def find_order_number(text: str, config: LabelConfig | None = None) -> str | None:
    """Erste Zahl direkt hinter einem Auftrags-Label, sonst None.

    Kein Fallback auf beliebige Zahlen. Ohne Label → keine Zuordnung möglich.
    """
    if not text.strip():
        return None

    match = _get_pattern(config).search(text)
    if not match:
        return None

    number = match.group(1)
    return number if number.isdigit() else None
