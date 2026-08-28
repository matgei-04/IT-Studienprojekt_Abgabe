"""Hilfsfunktionen für die sortierbare Prüf-Tabelle (URL-Query-Parameter)."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

SORTABLE_COLUMNS = [
    ("document", "Dokument"),
    ("date", "Eingangsdatum"),
    ("order", "Vorgeschlagener Auftrag"),
    ("confidence", "Sicherheit"),
]

# Spalten der Auftragsliste.
ORDER_SORTABLE_COLUMNS = [
    ("erf_nr", "Auftragsnummer"),
    ("kunde", "Kunde"),
    ("status", "Status"),
    ("dokumente", "Dokumente"),
    ("datum", "Erstellt"),
]

# Spalten der Dokumentliste.
DOCUMENT_SORTABLE_COLUMNS = [
    ("dateiname", "Dokument"),
    ("datum", "Eingangsdatum"),
    ("auftrag", "Auftrag"),
    ("status", "Status"),
    ("confidence", "Sicherheit"),
]


@dataclass
class SortColumn:
    key: str
    label: str
    href: str
    active: bool
    direction: str  # "asc" oder "desc" – nur relevant wenn active=True


def build_sort_columns(
    base_path: str,
    query: dict[str, str],
    current_sort: str,
    current_dir: str,
    columns_spec: list[tuple[str, str]] = SORTABLE_COLUMNS,
) -> dict[str, SortColumn]:
    """Baut für jede sortierbare Spalte den Link mit umgeschalteter Richtung.

    Rückgabe als Dict (Spalten-Key -> SortColumn), damit das Template die
    Spalten in der geforderten Reihenfolge anordnen kann (inkl. der
    nicht-sortierbaren Spalte "Lieferant/Kunde" dazwischen).
    """
    columns = {}
    for key, label in columns_spec:
        active = key == current_sort
        next_dir = "desc" if (active and current_dir == "asc") else "asc"

        params = {k: v for k, v in query.items() if k not in ("sort", "dir")}
        params["sort"] = key
        params["dir"] = next_dir

        columns[key] = SortColumn(
            key=key,
            label=label,
            href=f"{base_path}?{urlencode(params)}",
            active=active,
            direction=current_dir if active else "",
        )
    return columns


@dataclass
class PageLink:
    page: int
    href: str
    active: bool


def build_page_links(
    base_path: str,
    query: dict[str, str],
    total_pages: int,
    current_page: int,
) -> list[PageLink]:
    """Baut Seiten-Links (?page=N) unter Beibehaltung der übrigen Query-Parameter."""
    links = []
    for n in range(1, total_pages + 1):
        params = {k: v for k, v in query.items() if k != "page"}
        params["page"] = str(n)
        links.append(PageLink(page=n, href=f"{base_path}?{urlencode(params)}", active=n == current_page))
    return links
