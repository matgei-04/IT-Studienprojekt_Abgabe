# IT-Studienprojekt – Spedifix Document Matcher

## Datenextraktion

Eigenständiges Python-Modul zur Extraktion von Text und
Auftrags-/Sendungsnummer aus PDF-Scans. **Kein Matching, keine DB, keine UI.**

## Voraussetzungen

- Python 3.11+
- Tesseract OCR (System), Sprache `deu`
  - macOS: `brew install tesseract tesseract-lang`
  - Debian/Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-deu`
  - Windows: [UB Mannheim Installer](https://github.com/UB-Mannheim/tesseract/wiki)
    - Bei der Installation Sprache **German (`deu`)** auswählen
    - Option „Add to PATH“ aktivieren (oder Standardpfad
      `C:\Program Files\Tesseract-OCR\` – die App erkennt ihn automatisch)
    - Danach neues Terminal öffnen und prüfen: `tesseract --version`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # falls noch keine .env existiert
```

PDFs und Fotos **nur lesen** – Dateien werden weder verschoben noch gelöscht.
Lege eingehende Dokumente in den Ordner aus `SCAN_DIRECTORY` (auch Unterordner;
unterstützt: PDF, PNG, JPG, WebP, TIFF).

In `.env` können zusätzlich gesetzt werden:
- `SCAN_DIRECTORY`, `MIN_DIRECT_TEXT_LENGTH`, `OCR_LANGUAGE` (Extraktion)
- `SUPABASE_URL`, `SUPABASE_KEY` (Matching / Persistenz – lokal, nicht committen)

## Start (CLI)

```bash
python run_extraction.py
```

Pro Dokument erscheinen: Dateiname, `order_number`, `used_ocr`,
Textvorschau und kurze Ablaufhinweise.

## Öffentliche API (für Matching / UI)

```python
from extraction.config import load_settings
from extraction import extract_from_directory, extract_single_document

settings = load_settings()  # liest .env
docs = extract_from_directory(settings)
# oder: doc = extract_single_document("eingang/beispiel.pdf", settings)
```

### `IncomingDocument` (pro PDF)

| Feld | Bedeutung |
|------|-----------|
| `path` | Pfad zur Quelldatei |
| `text` | Extrahierter Volltext |
| `order_number` | erkannte Nummer oder `None` |
| `used_ocr` | `True`, wenn OCR-Fallback genutzt wurde |
| `extraction_notes` | kurze Hinweise zum Ablauf |

## Pipeline (kurz)

1. PDFs und Fotos im Scan-Ordner listen (rekursiv)
2. Eingebetteten PDF-Text lesen (PyMuPDF)
3. Wenn Textlänge &lt; `MIN_DIRECT_TEXT_LENGTH` → OCR (Tesseract); Fotos immer OCR
4. Auftragsnummer nur hinter Labels (Auftragsnummer / Auftrags-Nr. / ErfNr / …)
5. `IncomingDocument` zurückgeben

Ohne erkannte Auftragsnummer gibt es beim Matching **keinen** automatischen Vorschlag.

## Dateien

| Pfad | Rolle |
|------|--------|
| `run_extraction.py` | CLI-Einstieg |
| `domain/models.py` | `IncomingDocument`, `Settings` |
| `extraction/config.py` | `.env` laden |
| `extraction/formats.py` | unterstützte Dateiformate (PDF, Fotos) |
| `extraction/pdf_text.py` | direkter PDF-Text |
| `extraction/ocr.py` | OCR-Fallback |
| `extraction/order_number.py` | ErfNr / Auftragsnr. |
| `extraction/labels.py` | konfigurierbare Erkennungslabels (`labels.json`) |
| `extraction/pipeline.py` | Orchestrierung / öffentliche API |

## Matching (Anbindung)

```bash
python run_matching.py   # braucht SUPABASE_URL / SUPABASE_KEY in .env
```

Matching nutzt `extract_from_directory` und liefert `MatchResult` mit
`confidence` (Matching-Score). **Immer** manuelle Bestätigung über die App.
Details: `matching/README.md`.

Maßgeblich aus der Extraktion: `order_number`, `text`.
Dateien im Scan-Ordner bleiben unverändert.

## Desktop-Anwendung

```bash
python run_app.py
```

Öffnet das Dashboard in einem Desktop-Fenster (pywebview). Intern läuft ein lokaler Server auf `127.0.0.1` (`app/server.py`).

Package `app/`:

| Pfad | Rolle |
|------|--------|
| `app/data.py` | Persistenz in `Dokumente` / `DokumentZuordnung`, OCR/Matching-Pipeline, Listen und Auswertungen |
| `app/routes.py` | Query-Parameter lesen, Daten laden, Template rendern |
| `app/table.py` | Sortier-Links (URL-Query-Parameter) für die Tabelle |
| `app/render.py` | Jinja2-Rendering |
| `app/server.py` | Lokaler HTTP-Server + Router |
| `app/nav.py` | Sidebar-Menüpunkte |
| `app/templates/`, `app/static/` | HTML-Templates und CSS |
