"""Push the export step's CSV-shaped output into a Google Sheet.

Lädt `output/reporting/clusters.json` und `output/reporting/keywords.json`
in zwei Tabs eines vorgegebenen Google Sheets. Strategie wie beim
Airtable-Sync: Tab leeren, dann alle aktuellen Records als Zeilen
einfügen. Jeder Pipeline-Lauf liefert einen vollständigen Snapshot.

Steuerung über Umgebungsvariablen (Pydantic-Settings, Prefix `PIPELINE_`):

    PIPELINE_SHEETS_SYNC_ENABLED      true|false (Default false, no-op-Schalter)
    PIPELINE_SHEETS_ID                Sheet-ID aus der Sheet-URL
    PIPELINE_SHEETS_CLUSTERS_TAB      Default 'Clusters'
    PIPELINE_SHEETS_KEYWORDS_TAB      Default 'Keywords'

Plus eines von beiden für die Service-Account-Credentials:

    GOOGLE_SHEETS_CREDENTIALS_FILE    Pfad zur Service-Account-JSON
    GOOGLE_SHEETS_CREDENTIALS_JSON    JSON-Inhalt direkt (für CI-Secrets)

Wenn `PIPELINE_SHEETS_SYNC_ENABLED` nicht `true` ist, beendet sich das
Modul ohne Fehler. So bleibt `python pipeline.py` lokal lauffähig, ohne
dass jemand vorher GCP einrichten muss.

Setup (einmalig):
  1. Google-Cloud-Projekt anlegen, Sheets-API aktivieren.
  2. Service Account erstellen, JSON-Key herunterladen.
  3. Ziel-Sheet mit der `…@…iam.gserviceaccount.com`-Adresse teilen
     (Editor-Rechte).
  4. Tabs `Clusters` und `Keywords` im Sheet anlegen (oder Namen über
     die Env-Vars überschreiben). Headerzeile wird automatisch gesetzt.

CLI:
    python -m src.sync_sheets                  # Sync (wenn enabled)
    python -m src.sync_sheets --dry-run        # Vorschau, kein API-Call
    python -m src.sync_sheets --force          # umgeht den Enabled-Schalter
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

from src.config import settings
from src.export import _flatten_for_csv
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
REPORTING = ROOT / "output" / "reporting"


def _records_to_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    """Build a list-of-lists matrix from the records, ready for Sheets.

    First row is the header (union of all keys, in insertion order). All
    data rows align to the header. Missing values become empty strings.
    """
    flat = [_flatten_for_csv(r) for r in records]
    columns: list[str] = []
    seen: set[str] = set()
    for row in flat:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)

    matrix: list[list[Any]] = [columns]
    for row in flat:
        matrix.append([_cell(row.get(col, "")) for col in columns])
    return matrix


def _cell(value: Any) -> Any:
    """Coerce a flattened value to something the Sheets API accepts."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return value  # Sheets renders TRUE/FALSE
    if isinstance(value, (int, float, str)):
        return value
    return str(value)


def _load_credentials() -> dict[str, Any] | None:
    """Resolve the service-account JSON.

    Priority: inline JSON env (CI-friendly) -> file path (local-friendly).
    Returns None if neither is set.
    """
    inline = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON", "").strip()
    if inline:
        return json.loads(inline)
    path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_FILE", "").strip()
    if path and Path(path).is_file():
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return None


def _ensure_tab(spreadsheet, name: str, n_cols: int):
    """Return a worksheet by name, creating it if missing."""
    try:
        return spreadsheet.worksheet(name)
    except Exception:
        return spreadsheet.add_worksheet(title=name, rows=1000, cols=max(n_cols, 26))


def _write_tab(spreadsheet, tab_name: str, matrix: list[list[Any]]) -> None:
    if not matrix:
        logger.info("tab %s: nothing to write", tab_name)
        return
    n_rows, n_cols = len(matrix), len(matrix[0])
    ws = _ensure_tab(spreadsheet, tab_name, n_cols)
    ws.clear()
    if n_rows > ws.row_count or n_cols > ws.col_count:
        ws.resize(rows=max(n_rows + 50, ws.row_count), cols=max(n_cols, ws.col_count))
    ws.update(values=matrix, range_name="A1")
    logger.info("tab %s: wrote %d rows x %d cols", tab_name, n_rows, n_cols)


def run(dry_run: bool = False, force: bool = False) -> None:
    """Push the latest exports to Google Sheets.

    No-op (with an info log) if PIPELINE_SHEETS_SYNC_ENABLED is false,
    unless `force=True`.
    """
    if not (settings.sheets_sync_enabled or force):
        logger.info("sheets sync disabled (PIPELINE_SHEETS_SYNC_ENABLED=false). "
                    "Skipping.")
        return

    if not settings.sheets_id:
        raise SystemExit(
            "PIPELINE_SHEETS_ID is required when sheets sync is enabled."
        )

    clusters_path = REPORTING / "clusters.json"
    keywords_path = REPORTING / "keywords.json"
    if not clusters_path.exists() or not keywords_path.exists():
        raise SystemExit(
            "missing export files. Run `python -m src.export` first."
        )

    clusters = json.loads(clusters_path.read_text(encoding="utf-8"))
    keywords = json.loads(keywords_path.read_text(encoding="utf-8"))
    cluster_matrix = _records_to_rows(clusters)
    keyword_matrix = _records_to_rows(keywords)

    logger.info("Clusters tab '%s': %d rows (incl. header), %d cols",
                settings.sheets_clusters_tab,
                len(cluster_matrix), len(cluster_matrix[0]))
    logger.info("Keywords tab '%s': %d rows (incl. header), %d cols",
                settings.sheets_keywords_tab,
                len(keyword_matrix), len(keyword_matrix[0]))

    if dry_run:
        logger.info("DRY RUN. Skipping Sheets API call.")
        return

    creds = _load_credentials()
    if not creds:
        raise SystemExit(
            "GOOGLE_SHEETS_CREDENTIALS_JSON or GOOGLE_SHEETS_CREDENTIALS_FILE "
            "must be set. See docs/reporting-integration.md for setup."
        )

    # Imported lazily so the module loads without gspread installed (e.g.
    # in unit tests that exercise just the helpers).
    import gspread  # noqa: PLC0415

    client = gspread.service_account_from_dict(creds)
    spreadsheet = client.open_by_key(settings.sheets_id)
    logger.info("opened sheet '%s' (id=%s)", spreadsheet.title, settings.sheets_id)

    _write_tab(spreadsheet, settings.sheets_clusters_tab, cluster_matrix)
    _write_tab(spreadsheet, settings.sheets_keywords_tab, keyword_matrix)


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="show row/col counts, don't call the Sheets API.")
    parser.add_argument("--force", action="store_true",
                        help="ignore PIPELINE_SHEETS_SYNC_ENABLED=false.")
    args = parser.parse_args()
    run(dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
