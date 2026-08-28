# Matching – Kurzüberblick

1. Extraktion liefert `IncomingDocument` (inkl. `order_number`)
2. Suche per `order_number` → DB-Feld `ErfNr`
3. Ohne Nummer: Fallback über Absender-/Empfängernamen im Dokumenttext
4. Ohne Treffer → keine Zuordnung (manuell möglich)
5. Score → `confidence` (0.0–1.0); Absender/Empfänger zählen 20 % + 20 %
6. Immer manuelle Bestätigung

## Gewichte

Jedes Merkmal zählt nur **exakt** (1.0) oder **gar nicht** (0.0).

| Merkmal | Anteil | Treffer wenn |
|---------|-------:|--------------|
| Auftragsnummer | 60 % | erkannte Nummer = `ErfNr` |
| Absender | 20 % | alle Adressfelder exakt im Text |
| Empfänger | 20 % | wie Absender |

## Start

```bash
python run_matching.py
```

`.env` braucht: `SUPABASE_URL`, `SUPABASE_KEY`, `SCAN_DIRECTORY`, …
