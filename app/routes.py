"""Routen: Query-Parameter lesen, Daten laden, Template rendern."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote, urlencode

from app import data, table
from app.nav import NAV_ITEMS, SETTINGS_ITEM
from app.render import render
from extraction.formats import HTML_ACCEPT, SUPPORTED_EXTENSIONS

DEFAULT_SORT = "confidence"
DEFAULT_DIR = "asc"


def _sort_dir(query: dict[str, str]) -> tuple[str, str]:
    sort = query.get("sort", DEFAULT_SORT)
    if sort not in {"document", "date", "order", "confidence"}:
        sort = DEFAULT_SORT
    direction = query.get("dir", DEFAULT_DIR)
    if direction not in {"asc", "desc"}:
        direction = DEFAULT_DIR
    return sort, direction


def _base_context(active_key: str, page_title: str) -> dict:
    return {
        "nav_items": NAV_ITEMS,
        "settings_item": SETTINGS_ITEM,
        "active_key": active_key,
        "page_title": page_title,
    }


def dashboard(query: dict[str, str]) -> str:
    all_items, warning = data.get_open_review_items()

    sort, direction = _sort_dir(query)
    # Alle offenen Belege in der Vorschau – auch „Hoch“. Der Score ist
    # keine Freigabe; bestätigt wird erst auf der Prüfseite.
    review_items = data.sort_items(all_items, sort, direction)[:5]
    cols = table.build_sort_columns("/", query, sort, direction)

    # Dieselbe Quelle wie die Zuordnungsseite – sonst bleiben die Kacheln
    # bei 0, wenn in Dokumente kein ImportiertAm steht.
    all_rows, _ = data.get_assignment_rows(open_items=all_items, warning=warning)
    kpis = {
        "neu": len(all_rows),
        "automatisch": sum(1 for r in all_rows if r.status == "Bestätigt"),
        "pruefung": sum(1 for r in all_rows if r.status == "Prüfung erforderlich"),
        "nicht_zuordenbar": sum(
            1
            for r in all_rows
            if r.status in ("Keine Zuordnung", "Fehlerhaft", "In Bearbeitung")
        ),
    }
    recent_events = sorted(data.order_events(all_rows), key=lambda e: e[0], reverse=True)[:5]

    context = _base_context("uebersicht", "Übersicht")
    context.update(
        warning=warning,
        kpis=kpis,
        items=review_items,
        cols=cols,
        recent_events=recent_events,
        file_accept=HTML_ACCEPT,
        file_extensions_json=json.dumps(sorted(SUPPORTED_EXTENSIONS)),
        notice=query.get("notice"),
    )
    return render("dashboard.html", **context)


_EMPTY_MESSAGES = {
    "pruefung": "Keine Dokumente mit Prüfbedarf. Alle offenen Fälle sind entweder eindeutig oder bereits bestätigt.",
    "nicht_zuordenbar": "Keine Dokumente ohne Zuordnung.",
    "bestaetigt": "Noch keine bestätigten Zuordnungen.",
}


def _empty_message(active_filter: str | None, search_query: str | None) -> str:
    if search_query:
        return f"Keine Treffer für „{search_query}“."
    if active_filter in _EMPTY_MESSAGES:
        return _EMPTY_MESSAGES[active_filter]
    return "Noch keine Dokumente importiert."


def pruefen(query: dict[str, str]) -> str:
    doc_path = query.get("doc")
    detail = data.get_review_detail(doc_path) if doc_path else None

    if detail is None:
        context = _base_context("dokumente", "Zuordnung prüfen")
        context.update(
            message="Dokument wurde nicht gefunden (evtl. verschoben oder gelöscht).",
        )
        return render("placeholder.html", **context)

    item, candidate, reasons, confirmed = detail

    manual_q = query.get("manual_q")

    context = _base_context("dokumente", "Zuordnung prüfen")
    context.update(
        item=item,
        candidate=candidate,
        reasons=reasons,
        confirmed=confirmed,
        error=query.get("error"),
        manual_q=manual_q,
    )
    return render("pruefen.html", **context)


def search_orders_api(query: dict[str, str]) -> dict:
    """JSON für Live-Suche auf der Prüfseite (Auftragsnummer / Kunde / Referenz)."""
    q = (query.get("q") or "").strip()
    try:
        limit = min(max(int(query.get("limit", "8")), 1), 20)
    except ValueError:
        limit = 8
    if len(q) < 1:
        return {"ok": True, "query": q, "results": []}
    orders, warning = data.search_orders(q, limit=limit)
    return {
        "ok": warning is None,
        "query": q,
        "warning": warning,
        "results": [
            {
                "erf_nr": o.erf_nr,
                "kunde": o.kunde,
                "beschreibung": o.beschreibung,
            }
            for o in orders
        ],
    }


def confirm(form: dict[str, str]) -> str:
    """Verarbeitet den POST von 'Zuordnung bestätigen' und leitet zurück."""
    doc_path = form.get("doc", "")
    erf_nr = form.get("erf_nr", "")

    try:
        score = float(form.get("score", "0"))
    except ValueError:
        score = 0.0

    if not doc_path or not erf_nr:
        redirect_target = f"/zuordnung/pruefen?doc={quote(doc_path)}&error={quote('Unvollständige Anfrage.')}"
        return redirect_target

    ok, message = data.confirm_assignment(doc_path, erf_nr, score)

    if ok:
        return f"/zuordnung/pruefen?doc={quote(doc_path)}"
    return f"/zuordnung/pruefen?doc={quote(doc_path)}&error={quote(message)}"


def delete_assignment(form: dict[str, str]) -> str:
    doc_path = form.get("doc", "")
    next_url = form.get("next") or "/dokumente"
    ok, message = data.delete_assignment(doc_path)
    if ok:
        # Dokument bleibt – zurück zur Prüfseite, falls Datei noch da
        if Path(doc_path).is_file():
            return f"/zuordnung/pruefen?doc={quote(doc_path)}"
        return next_url
    return f"{next_url}?error={quote(message)}" if "?" not in next_url else f"{next_url}&error={quote(message)}"


def delete_document(form: dict[str, str]) -> str:
    doc_path = form.get("doc", "")
    next_url = form.get("next") or "/dokumente"
    ok, message = data.delete_document(doc_path)
    if ok:
        return next_url
    sep = "&" if "?" in next_url else "?"
    return f"{next_url}{sep}error={quote(message)}"


def upload(filename: str, content: bytes) -> dict:
    """Speichert den Upload und startet OCR/Matching im Hintergrund.

    Die HTTP-Antwort kommt sofort zurück – sonst bricht unter Windows/WebView2
    die Verbindung ab, wenn Tesseract länger braucht (WinError 10053).
    """
    import threading

    saved_path, error = data.save_uploaded_pdf(filename, content)
    if error:
        already = "bereits importiert" in error
        return {
            "ok": False,
            "filename": filename,
            "error": error,
            "skipped": already,
        }

    threading.Thread(target=data.process_pending_documents, daemon=True).start()

    return {
        "ok": True,
        "filename": saved_path.name,
        "status": "In Bearbeitung",
        "confidence": 0,
    }


ORDER_PAGE_SIZE = 20

_ORDER_EMPTY_MESSAGES = {
    "Vollständig": "Keine vollständig zugeordneten Aufträge.",
    "Prüfung erforderlich": "Keine Aufträge mit offenem Prüfbedarf.",
    "Ohne Dokumente": "Keine Aufträge ohne Dokumente.",
}


def _order_empty_message(status_filter: str | None, search_query: str | None) -> str:
    if search_query:
        return f"Keine Treffer für „{search_query}“."
    if status_filter in _ORDER_EMPTY_MESSAGES:
        return _ORDER_EMPTY_MESSAGES[status_filter]
    return "Noch keine Aufträge in der Datenbank."


def _order_date_param(query: dict[str, str], key: str):
    value = query.get(key)
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def auftraege(query: dict[str, str]) -> str:
    all_summaries, warning = data.get_order_summaries()

    status_filter = query.get("status") or None
    if status_filter not in data.ORDER_STATUS_CLASS:
        status_filter = None
    kunde_filter = query.get("kunde") or None
    search_query = query.get("q") or None
    date_from = _order_date_param(query, "von")
    date_to = _order_date_param(query, "bis")

    filtered = data.filter_order_summaries(
        all_summaries, status_filter, kunde_filter, date_from, date_to, search_query
    )

    sort = query.get("sort", "datum")
    if sort not in data.ORDER_SORT_FIELDS:
        sort = "datum"
    direction = query.get("dir", "desc")
    if direction not in {"asc", "desc"}:
        direction = "desc"
    filtered = data.sort_order_summaries(filtered, sort, direction)

    try:
        page = max(1, int(query.get("page", "1")))
    except ValueError:
        page = 1
    total = len(filtered)
    total_pages = max(1, (total + ORDER_PAGE_SIZE - 1) // ORDER_PAGE_SIZE)
    page = min(page, total_pages)
    page_items = filtered[(page - 1) * ORDER_PAGE_SIZE : page * ORDER_PAGE_SIZE]

    cols = table.build_sort_columns("/auftraege", query, sort, direction, table.ORDER_SORTABLE_COLUMNS)
    page_links = table.build_page_links("/auftraege", query, total_pages, page)
    kunden_options = sorted({s.order.kunde for s in all_summaries if s.order.kunde})

    context = _base_context("auftraege", "Aufträge")
    context.update(
        warning=warning,
        summaries=page_items,
        cols=cols,
        status_filter=status_filter,
        kunde_filter=kunde_filter,
        search_query=search_query,
        von=query.get("von", ""),
        bis=query.get("bis", ""),
        kunden_options=kunden_options,
        total=total,
        page_links=page_links,
        show_pagination=total_pages > 1,
        empty_message=_order_empty_message(status_filter, search_query),
    )
    return render("auftraege.html", **context)


def auftrag_details(query: dict[str, str]) -> str:
    erf_nr = query.get("erf_nr")
    summary, warning = data.get_order_detail(erf_nr) if erf_nr else (None, None)

    if summary is None:
        context = _base_context("auftraege", "Auftrag")
        context.update(message=f"Auftrag {erf_nr or ''} wurde nicht gefunden.".strip())
        return render("placeholder.html", **context)

    events = data.order_events(summary.documents)

    context = _base_context("auftraege", f"Auftrag {summary.order.erf_nr}")
    context.update(warning=warning, summary=summary, events=events)
    return render("auftrag_details.html", **context)


DOCUMENT_PAGE_SIZE = 20


def dokumente(query: dict[str, str]) -> str:
    all_entries, warning = data.get_document_entries()
    open_count = sum(1 for e in all_entries if e.row.status != "Bestätigt")

    status_filter = query.get("status") or None
    if status_filter not in ("bestaetigt", "pruefung", "nicht_zuordenbar"):
        status_filter = None
    search_query = query.get("q") or None
    date_from = _order_date_param(query, "von")
    date_to = _order_date_param(query, "bis")

    filtered = data.filter_document_entries(
        all_entries, status_filter, date_from, date_to, search_query
    )

    sort = query.get("sort", "datum")
    if sort not in data.DOCUMENT_SORT_FIELDS:
        sort = "datum"
    direction = query.get("dir", "desc")
    if direction not in {"asc", "desc"}:
        direction = "desc"
    filtered = data.sort_document_entries(
        filtered, sort, direction, prioritize_open="sort" not in query
    )

    try:
        page = max(1, int(query.get("page", "1")))
    except ValueError:
        page = 1
    total = len(filtered)
    total_pages = max(1, (total + DOCUMENT_PAGE_SIZE - 1) // DOCUMENT_PAGE_SIZE)
    page = min(page, total_pages)
    page_items = filtered[(page - 1) * DOCUMENT_PAGE_SIZE : page * DOCUMENT_PAGE_SIZE]

    cols = table.build_sort_columns("/dokumente", query, sort, direction, table.DOCUMENT_SORTABLE_COLUMNS)
    page_links = table.build_page_links("/dokumente", query, total_pages, page)

    view_rows = [{"entry": e} for e in page_items]

    context = _base_context("dokumente", "Dokumentenzuordnung")
    context.update(
        warning=warning,
        error=query.get("error"),
        open_count=open_count,
        status_filter=status_filter,
        search_query=search_query,
        von=query.get("von", ""),
        bis=query.get("bis", ""),
        cols=cols,
        view_rows=view_rows,
        page_links=page_links,
        show_pagination=total_pages > 1,
        empty_message=_empty_message(status_filter, search_query),
        notice=query.get("notice"),
    )
    return render("dokumente.html", **context)


def reprocess(form: dict[str, str]) -> str:
    """Startet einen erneuten Zuordnungsdurchlauf und leitet zurück."""
    next_url = form.get("next") or "/"
    started = data.start_reprocess()
    notice = "started" if started else "busy"
    sep = "&" if "?" in next_url else "?"
    return f"{next_url}{sep}notice={notice}"


_RANGE_PRESETS = {"7": 7, "30": 30, "90": 90, "365": 365}
_RANGE_LABELS = {"7": "Letzte 7 Tage", "30": "Letzte 30 Tage", "90": "Letzte 90 Tage", "365": "Letzte 12 Monate", "alle": "Gesamter Zeitraum"}


def _auswertungen_range(query: dict[str, str]) -> tuple[date | None, date | None, str]:
    range_key = query.get("range", "30")
    if range_key == "alle":
        return None, None, "alle"
    if range_key not in _RANGE_PRESETS:
        range_key = "30"
    date_to = date.today()
    date_from = date_to - timedelta(days=_RANGE_PRESETS[range_key])
    return date_from, date_to, range_key


def _build_trend_bars(trend: list[dict]) -> list[dict]:
    """Balken-Koordinaten in einem 0–100-Koordinatensystem (SVG viewBox),
    damit die Grafik unabhängig von der tatsächlichen Pixelbreite skaliert."""
    if not trend:
        return []
    n = len(trend)
    gap = 2.0
    bar_width = (100 - gap * (n - 1)) / n if n > 1 else 100.0
    bars = []
    x = 0.0
    for point in trend:
        bar_height = max(3.0, point["quote"] * 40)
        bars.append(
            {
                "x": round(x, 2),
                "y": round(40 - bar_height, 2),
                "width": round(bar_width, 2),
                "height": round(bar_height, 2),
                "label": point["label"],
                "pct": round(point["quote"] * 100),
            }
        )
        x += bar_width + gap
    return bars


def auswertungen(query: dict[str, str]) -> str:
    all_stats, warning = data.get_dokument_stats()
    date_from, date_to, range_key = _auswertungen_range(query)
    stats = data.filter_dokument_stats(all_stats, date_from, date_to)

    kpis = data.compute_auswertungen_kpis(stats)
    confidence = data.compute_confidence_distribution(stats, data.AUTO_MATCH_THRESHOLD)
    trend = data.compute_quality_trend(stats)
    trend_bars = _build_trend_bars(trend) if len(trend) >= 2 else []

    context = _base_context("auswertungen", "Auswertungen")
    context.update(
        warning=warning,
        kpis=kpis,
        confidence=confidence,
        trend_bars=trend_bars,
        range_key=range_key,
        range_options=[("7", _RANGE_LABELS["7"]), ("30", _RANGE_LABELS["30"]), ("90", _RANGE_LABELS["90"]), ("365", _RANGE_LABELS["365"]), ("alle", _RANGE_LABELS["alle"])],
        has_any_data=len(all_stats) > 0,
        has_range_data=len(stats) > 0,
    )
    return render("auswertungen.html", **context)


def einstellungen(query: dict[str, str]) -> str:
    tab = query.get("tab", "datenquellen")
    if tab not in ("datenquellen", "verarbeitung", "labels"):
        tab = "datenquellen"

    einstellungen_row, warning = data.get_einstellungen()
    datasources = data.get_datasources()
    from extraction.labels import labels_to_textarea

    labels = data.get_label_config()

    context = _base_context("einstellungen", "Einstellungen")
    context.update(
        warning=warning,
        tab=tab,
        einstellungen=einstellungen_row,
        datasources=datasources,
        conn_ok=query.get("conn_ok"),
        conn_msg=query.get("conn_msg"),
        saved=query.get("saved") == "1",
        save_error=query.get("save_error"),
        order_labels_text=labels_to_textarea(labels.order_labels),
    )
    return render("einstellungen.html", **context)


def einstellungen_verbindung_pruefen() -> str:
    ok, msg = data.check_database_connection()
    return f"/einstellungen?tab=datenquellen&conn_ok={'1' if ok else '0'}&conn_msg={quote(msg)}"


def einstellungen_verarbeitung_speichern(form: dict[str, str]) -> str:
    ocr_aktiv = "ocr_aktiv" in form
    matching_aktiv = "matching_aktiv" in form
    ok, msg = data.update_verarbeitung(ocr_aktiv, matching_aktiv)
    if ok:
        return "/einstellungen?tab=verarbeitung&saved=1"
    return f"/einstellungen?tab=verarbeitung&save_error={quote(msg)}"


def einstellungen_ordner_speichern(form: dict[str, str]) -> str:
    ok, msg = data.update_scan_ordner(form.get("scan_ordner", ""))
    if ok:
        return "/einstellungen?tab=datenquellen&saved=1"
    return f"/einstellungen?tab=datenquellen&save_error={quote(msg)}"


def einstellungen_labels_speichern(form: dict[str, str]) -> str:
    if form.get("reset") == "1":
        ok, msg = data.reset_label_config()
    else:
        ok, msg = data.save_label_config(form.get("order_labels", ""))
    if ok:
        return "/einstellungen?tab=labels&saved=1"
    return f"/einstellungen?tab=labels&save_error={quote(msg)}"
