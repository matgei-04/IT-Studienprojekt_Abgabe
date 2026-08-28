"""Linke Navigation: Menüpunkte und ihre Icons (einfache Inline-SVGs)."""

from __future__ import annotations

# Schlanke, einheitliche Strich-Icons (24x24, aktuelle Textfarbe wird geerbt).
_ICON_UEBERSICHT = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">'
    '<rect x="3" y="3" width="8" height="8" rx="1.5"/>'
    '<rect x="13" y="3" width="8" height="5" rx="1.5"/>'
    '<rect x="13" y="11" width="8" height="10" rx="1.5"/>'
    '<rect x="3" y="14" width="8" height="7" rx="1.5"/>'
    '</svg>'
)
_ICON_AUFTRAEGE = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">'
    '<rect x="3" y="7" width="18" height="13" rx="1.5"/>'
    '<path d="M8 7V5.5A1.5 1.5 0 0 1 9.5 4h5A1.5 1.5 0 0 1 16 5.5V7"/>'
    '<path d="M3 12h18"/>'
    '</svg>'
)
_ICON_DOKUMENTE = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">'
    '<path d="M7 3h7l4 4v14H7z"/>'
    '<path d="M14 3v4h4"/>'
    '<path d="M9.5 12.5h5M9.5 15.5h5"/>'
    '</svg>'
)
_ICON_AUSWERTUNGEN = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">'
    '<path d="M4 20V10M11 20V4M18 20v-7" stroke-linecap="round"/>'
    '</svg>'
)
_ICON_EINSTELLUNGEN = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">'
    '<circle cx="12" cy="12" r="3"/>'
    '<path d="M19 12a7 7 0 0 0-.13-1.32l2-1.55-2-3.46-2.36.95a7 7 0 0 0-2.28-1.32L14 3h-4l-.23 2.3a7 7 0 0 0-2.28 1.32l-2.36-.95-2 3.46 2 1.55A7 7 0 0 0 5 12c0 .45.045.89.13 1.32l-2 1.55 2 3.46 2.36-.95a7 7 0 0 0 2.28 1.32L10 21h4l.23-2.3a7 7 0 0 0 2.28-1.32l2.36.95 2-3.46-2-1.55c.085-.43.13-.87.13-1.32z"/>'
    '</svg>'
)

# Hauptnavigation (obere Gruppe der Sidebar).
NAV_ITEMS: list[dict] = [
    {"key": "uebersicht", "label": "Übersicht", "path": "/", "icon": _ICON_UEBERSICHT},
    {"key": "dokumente", "label": "Zuordnung", "path": "/dokumente", "icon": _ICON_DOKUMENTE},
    {"key": "auftraege", "label": "Aufträge", "path": "/auftraege", "icon": _ICON_AUFTRAEGE},
    {"key": "auswertungen", "label": "Auswertungen", "path": "/auswertungen", "icon": _ICON_AUSWERTUNGEN},
]

# Wird unten in der Sidebar angepinnt.
SETTINGS_ITEM: dict = {
    "key": "einstellungen",
    "label": "Einstellungen",
    "path": "/einstellungen",
    "icon": _ICON_EINSTELLUNGEN,
}
