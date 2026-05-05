"""Sync the export step's JSON output into an Airtable base.

Lädt `output/reporting/clusters.json` und `output/reporting/keywords.json`
hoch in zwei Airtable-Tabellen. Strategie ist absichtlich einfach: alle
existierenden Records werden gelöscht, dann werden alle aktuellen
Records in Batches (max. 10 pro Call, Airtable-Limit) eingefügt.

Das passt zum Modell der Pipeline: jeder Lauf erzeugt einen frischen,
vollständigen Snapshot. Inkrementelle Updates wären komplexer (Mapping
Cluster-ID auf Airtable-Record-ID, Konflikt-Auflösung) und für die
Lauffrequenz (täglich oder seltener) nicht nötig.

Konfiguration über Umgebungsvariablen oder CLI-Flags:
    AIRTABLE_TOKEN              Personal Access Token (https://airtable.com/create/tokens)
    AIRTABLE_BASE_ID            Base-ID, beginnt mit 'app...'
    AIRTABLE_CLUSTERS_TABLE     Default: 'Clusters'
    AIRTABLE_KEYWORDS_TABLE     Default: 'Keywords'

Vorbedingung: Beide Tabellen müssen vorab im Airtable-UI angelegt sein,
mit den Feldnamen aus der jeweiligen JSON-Datei (Brief-Felder mit
Prefix `brief_`). Ein Setup-Hilfsbefehl gibt die erwarteten Feldnamen
aus.

CLI:
    python -m src.sync_airtable                         # voller Sync
    python -m src.sync_airtable --dry-run               # nur Vorschau
    python -m src.sync_airtable --print-schema          # Feldnamen anzeigen
    python -m src.sync_airtable --tables clusters       # nur Cluster-Tabelle
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.export import _flatten_for_csv
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
REPORTING = ROOT / "output" / "reporting"

AIRTABLE_API = "https://api.airtable.com/v0"
BATCH_SIZE = 10
RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY = 2.0


def _airtable_value(value: Any) -> Any:
    """Convert Python values to JSON values Airtable accepts.

    Airtable accepts native types for most fields (Number, Checkbox,
    Single line text). Lists of strings would map to multi-select if
    the field is configured that way, but to keep the user setup
    simple, we always join lists into a single string with " | ".
    Same for nested dicts (benchmark_urls).
    """
    if isinstance(value, list):
        if not value:
            return ""
        if all(isinstance(item, dict) and "url" in item for item in value):
            return " | ".join(
                f"{item.get('url', '')} — {item.get('note', '')}".rstrip(" —")
                for item in value
            )
        return " | ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return value


def _to_airtable_fields(record: dict[str, Any]) -> dict[str, Any]:
    """Flatten a record (same as CSV) and coerce values for Airtable."""
    flat = _flatten_for_csv(record)
    out: dict[str, Any] = {}
    for key, value in flat.items():
        if value == "" or value is None:
            continue
        if isinstance(value, str) and value.lower() in ("true", "false"):
            out[key] = value.lower() == "true"
        else:
            out[key] = value
    return out


def _request(method: str, url: str, token: str,
             body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Issue one Airtable API call with simple retry on 429 and 5xx."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    last_err: Exception | None = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read().decode("utf-8")
                return json.loads(payload) if payload else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            if e.code in (429, 500, 502, 503, 504) and attempt < RETRY_ATTEMPTS:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning("airtable %s %s -> HTTP %s, retry in %.1fs",
                               method, url, e.code, delay)
                time.sleep(delay)
                last_err = e
                continue
            raise RuntimeError(
                f"airtable {method} {url} failed: HTTP {e.code} {err_body}"
            ) from e
        except urllib.error.URLError as e:
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_BASE_DELAY * (2 ** (attempt - 1)))
                last_err = e
                continue
            raise
    if last_err:
        raise RuntimeError(f"airtable {method} {url} failed after retries") from last_err
    return {}


def _list_record_ids(base_id: str, table: str, token: str) -> list[str]:
    """Page through every record in the table and return its ID."""
    ids: list[str] = []
    offset: str | None = None
    table_url = f"{AIRTABLE_API}/{base_id}/{urllib.parse.quote(table)}"
    while True:
        url = f"{table_url}?pageSize=100"
        if offset:
            url += f"&offset={urllib.parse.quote(offset)}"
        resp = _request("GET", url, token)
        for rec in resp.get("records", []):
            ids.append(rec["id"])
        offset = resp.get("offset")
        if not offset:
            break
    return ids


def _delete_records(base_id: str, table: str, token: str,
                    record_ids: list[str]) -> int:
    if not record_ids:
        return 0
    table_url = f"{AIRTABLE_API}/{base_id}/{urllib.parse.quote(table)}"
    deleted = 0
    for i in range(0, len(record_ids), BATCH_SIZE):
        chunk = record_ids[i:i + BATCH_SIZE]
        query = "&".join(f"records[]={urllib.parse.quote(rid)}" for rid in chunk)
        _request("DELETE", f"{table_url}?{query}", token)
        deleted += len(chunk)
    return deleted


def _insert_records(base_id: str, table: str, token: str,
                    records: list[dict[str, Any]]) -> int:
    if not records:
        return 0
    table_url = f"{AIRTABLE_API}/{base_id}/{urllib.parse.quote(table)}"
    inserted = 0
    for i in range(0, len(records), BATCH_SIZE):
        chunk = records[i:i + BATCH_SIZE]
        body = {
            "records": [{"fields": _to_airtable_fields(r)} for r in chunk],
            "typecast": True,
        }
        _request("POST", table_url, token, body=body)
        inserted += len(chunk)
    return inserted


def _sync_table(base_id: str, table: str, token: str,
                records: list[dict[str, Any]], dry_run: bool) -> None:
    logger.info("=== %s ===", table)
    logger.info("local records to sync: %d", len(records))

    if dry_run:
        sample = _to_airtable_fields(records[0]) if records else {}
        logger.info("DRY RUN. Sample record fields: %s",
                    list(sample.keys())[:10])
        return

    existing = _list_record_ids(base_id, table, token)
    logger.info("existing records to clear: %d", len(existing))
    deleted = _delete_records(base_id, table, token, existing)
    logger.info("deleted %d records", deleted)

    inserted = _insert_records(base_id, table, token, records)
    logger.info("inserted %d records", inserted)


def _print_schema(records: list[dict[str, Any]], table_label: str) -> None:
    if not records:
        print(f"# {table_label}: no records to derive schema from")
        return
    sample = _to_airtable_fields(records[0])
    print(f"# {table_label} fields ({len(sample)} columns):")
    for key, value in sample.items():
        kind = "Checkbox" if isinstance(value, bool) else (
            "Number" if isinstance(value, (int, float)) else "Long text")
        print(f"  - {key}  ({kind})")
    print()


def run(token: str | None = None, base_id: str | None = None,
        clusters_table: str | None = None, keywords_table: str | None = None,
        tables: tuple[str, ...] = ("clusters", "keywords"),
        dry_run: bool = False, print_schema: bool = False) -> None:
    clusters_path = REPORTING / "clusters.json"
    keywords_path = REPORTING / "keywords.json"
    if not clusters_path.exists() or not keywords_path.exists():
        raise SystemExit(
            f"missing export files. Run `python -m src.export` first."
        )

    clusters = json.loads(clusters_path.read_text(encoding="utf-8"))
    keywords = json.loads(keywords_path.read_text(encoding="utf-8"))

    if print_schema:
        _print_schema(clusters, "Clusters")
        _print_schema(keywords, "Keywords")
        return

    token = token or os.environ.get("AIRTABLE_TOKEN")
    base_id = base_id or os.environ.get("AIRTABLE_BASE_ID")
    clusters_table = (clusters_table
                      or os.environ.get("AIRTABLE_CLUSTERS_TABLE", "Clusters"))
    keywords_table = (keywords_table
                      or os.environ.get("AIRTABLE_KEYWORDS_TABLE", "Keywords"))

    if not dry_run and (not token or not base_id):
        raise SystemExit(
            "AIRTABLE_TOKEN and AIRTABLE_BASE_ID env vars are required.\n"
            "  Token: https://airtable.com/create/tokens (scope: data.records:read/write)\n"
            "  Base ID: https://airtable.com/api -> URL contains 'app...'\n"
            "Or use --dry-run to preview without uploading."
        )

    if "clusters" in tables:
        _sync_table(base_id, clusters_table, token, clusters, dry_run)
    if "keywords" in tables:
        _sync_table(base_id, keywords_table, token, keywords, dry_run)


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="show what would happen, don't call the API.")
    parser.add_argument("--print-schema", action="store_true",
                        help="print the field names + types Airtable should "
                             "be configured with, then exit.")
    parser.add_argument("--tables", default="clusters,keywords",
                        help="comma-separated tables to sync. "
                             "Valid: clusters, keywords. Default: both.")
    parser.add_argument("--token", default=None,
                        help="Airtable Personal Access Token. "
                             "Falls back to env AIRTABLE_TOKEN.")
    parser.add_argument("--base-id", default=None,
                        help="Airtable Base ID (app...). "
                             "Falls back to env AIRTABLE_BASE_ID.")
    parser.add_argument("--clusters-table", default=None,
                        help="Cluster table name. Falls back to "
                             "AIRTABLE_CLUSTERS_TABLE or 'Clusters'.")
    parser.add_argument("--keywords-table", default=None,
                        help="Keyword table name. Falls back to "
                             "AIRTABLE_KEYWORDS_TABLE or 'Keywords'.")
    args = parser.parse_args()

    tables = tuple(t.strip() for t in args.tables.split(",") if t.strip())
    invalid = [t for t in tables if t not in ("clusters", "keywords")]
    if invalid:
        raise SystemExit(f"unknown table(s): {invalid}. valid: clusters, keywords")

    run(token=args.token, base_id=args.base_id,
        clusters_table=args.clusters_table, keywords_table=args.keywords_table,
        tables=tables, dry_run=args.dry_run, print_schema=args.print_schema)


if __name__ == "__main__":
    main()
