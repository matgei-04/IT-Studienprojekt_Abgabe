"""Konfigurierbare Erkennungslabels für die Auftragsnummer.

Gespeichert lokal in labels.json. Fehlt die Datei, gelten die Defaults
(entsprechen dem bisherigen hardcodierten Verhalten).
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LABELS_PATH = PROJECT_ROOT / "labels.json"

# Defaults = bisheriges Verhalten der Extraktion.
DEFAULT_ORDER_LABELS = [
    "Erfassungsnummer",
    "ErfNr",
    "Erf Nr",
    "Auftragsnummer",
    "Auftrags-Nr",
    "Auftragsnr",
    "Auftrag Nr",
    "Auftrag Nummer",
    "Auftrag No",
    "Auftrag",
]

_MAX_LABELS = 40
_MAX_LABEL_LEN = 60

_lock = threading.Lock()
_cache_mtime: float | None = None
_cache: LabelConfig | None = None


@dataclass
class LabelConfig:
    order_labels: list[str] = field(default_factory=lambda: list(DEFAULT_ORDER_LABELS))


def default_labels() -> LabelConfig:
    return LabelConfig()


def _normalize_list(raw: object, fallback: list[str]) -> list[str]:
    if not isinstance(raw, list):
        return list(fallback)
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, str):
            continue
        value = " ".join(item.split()).strip()
        if not value or len(value) > _MAX_LABEL_LEN:
            continue
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(value)
        if len(cleaned) >= _MAX_LABELS:
            break
    return cleaned or list(fallback)


def _from_dict(data: dict) -> LabelConfig:
    return LabelConfig(
        order_labels=_normalize_list(data.get("order_labels"), DEFAULT_ORDER_LABELS),
    )


def load_labels(path: Path | None = None) -> LabelConfig:
    """Lädt Labels aus JSON; bei fehlender/ungültiger Datei → Defaults."""
    global _cache_mtime, _cache
    target = path or LABELS_PATH

    with _lock:
        try:
            mtime = target.stat().st_mtime if target.is_file() else None
        except OSError:
            mtime = None

        if _cache is not None and path is None and mtime == _cache_mtime:
            return LabelConfig(order_labels=list(_cache.order_labels))

        if not target.is_file():
            cfg = default_labels()
            if path is None:
                _cache = cfg
                _cache_mtime = None
            return default_labels()

        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("labels.json muss ein Objekt sein")
            cfg = _from_dict(data)
        except (OSError, ValueError, json.JSONDecodeError):
            cfg = default_labels()

        if path is None:
            _cache = cfg
            _cache_mtime = mtime
        return LabelConfig(order_labels=list(cfg.order_labels))


def save_labels(config: LabelConfig, path: Path | None = None) -> None:
    """Speichert Labels als JSON und leert den Cache."""
    global _cache_mtime, _cache
    target = path or LABELS_PATH
    cleaned = LabelConfig(
        order_labels=_normalize_list(config.order_labels, DEFAULT_ORDER_LABELS),
    )
    target.write_text(
        json.dumps(asdict(cleaned), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with _lock:
        if path is None:
            _cache = cleaned
            try:
                _cache_mtime = target.stat().st_mtime
            except OSError:
                _cache_mtime = None


def clear_labels_cache() -> None:
    global _cache_mtime, _cache
    with _lock:
        _cache = None
        _cache_mtime = None


def parse_label_lines(text: str) -> list[str]:
    """Textarea (eine Zeile = ein Label) → bereinigte Liste."""
    lines = []
    seen: set[str] = set()
    for line in (text or "").splitlines():
        value = " ".join(line.split()).strip()
        if not value or len(value) > _MAX_LABEL_LEN:
            continue
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        lines.append(value)
        if len(lines) >= _MAX_LABELS:
            break
    return lines


def labels_to_textarea(labels: list[str]) -> str:
    return "\n".join(labels)
