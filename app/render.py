"""Jinja2-Rendering."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
_LOCAL_TZ = ZoneInfo("Europe/Berlin")

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _to_local(value: datetime) -> datetime:
    """UTC-/Offset-Zeitstempel nach Europe/Berlin; naive Werte als lokal belassen."""
    if value.tzinfo is None:
        return value
    return value.astimezone(_LOCAL_TZ)


def _de_date(value: datetime | date | None) -> str:
    if value is None:
        return "–"
    if isinstance(value, datetime):
        value = _to_local(value)
    return value.strftime("%d.%m.%Y")


def _de_datetime(value: datetime | None) -> str:
    if value is None:
        return "–"
    return _to_local(value).strftime("%d.%m.%Y %H:%M")


_env.filters["de_date"] = _de_date
_env.filters["de_datetime"] = _de_datetime


def render(template_name: str, **context) -> str:
    template = _env.get_template(template_name)
    return template.render(**context)
