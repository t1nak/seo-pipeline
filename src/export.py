"""Export step of the SEO keyword pipeline.

Bündelt alle Pipeline-Ergebnisse in flache JSON- und CSV-Dateien, die
ohne weitere Aufbereitung in ein filterbares Reporting (Airtable,
Notion, Google Sheets, Looker Studio etc.) importiert werden können.

Fünf Dateien werden geschrieben, jeweils in `output/reporting/`:

  - `clusters.json` flaches Array, eine Zeile pro Cluster, inklusive
    der aus dem Markdown-Brief geparsten Felder (Hauptkeyword,
    Zielgruppe, H1, H2-Outline, Wortanzahl, CTA, Benchmark-URLs). Das
    ist die Hauptquelle für das Cluster-Reporting (Airtable, Notion).
  - `keywords.json` flaches Array, eine Zeile pro Keyword, mit
    Cluster-Zuordnung und allen Metriken.
  - `report.json` konsolidiertes Bundle aus Run-Metadaten plus beiden
    Listen, falls ein Tool alles in einem Rutsch lesen will.
  - `clusters.csv` und `keywords.csv` dieselben Inhalte wie die JSONs,
    aber mit verschachtelten Feldern aufgelöst (Brief-Felder mit Prefix
    `brief_`, Listen mit Pipe `|` separiert). Direkt in Google Sheets
    via `Datei → Importieren` oder via `=IMPORTDATA(...)` einlesbar.

Zusätzlich werden alle Dateien nach `output/reporting/runs/<run_id>/`
gespiegelt, damit historische Läufe denselben Schnappschuss behalten
wie die HTML-Dashboards.

CLI:
    python -m src.export [--run-id 2026-05-01] [--source semrush]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.briefs_html import (
    LABELED_CSV,
    PROFILES_CSV,
    _benchmark_annotations,
    _meta,
    _outline_h2,
    _safe_label,
    _section,
)
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
REPORTING = OUT / "reporting"
RUNS_DIR = REPORTING / "runs"
BRIEFINGS = OUT / "briefings"

DEFAULT_SOURCE = "llm-generated"


def _split_kw_list(value: Any) -> list[str]:
    """Parse semicolon-separated keyword strings from cluster_profiles.csv."""
    if not isinstance(value, str) or not value.strip():
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def _split_secondary(line: str) -> list[str]:
    """Parse a 'Nebenkeywords:' line into a list."""
    return [part.strip() for part in line.split(",") if part.strip()]


def _parse_benchmark_urls(md: str) -> list[dict[str, str]]:
    """Pull (url, annotation) pairs out of the Benchmark URLs section."""
    body = _section(md, "Benchmark URLs")
    out: list[dict[str, str]] = []
    for line in body.splitlines():
        m = re.match(r"\d+\.\s+(\S+)\s*[—-]\s*(.+)", line.strip())
        if m:
            out.append({"url": m.group(1).strip(), "note": m.group(2).strip()})
    return out


def _parse_word_count(value: str) -> int | None:
    """Recommended word count is sometimes '2500', sometimes '2500 Wörter'."""
    if not value:
        return None
    m = re.search(r"\d{3,5}", value)
    return int(m.group(0)) if m else None


def _intent_from_pct(pct_commercial: float) -> str:
    if pct_commercial >= 70:
        return "commercial"
    if pct_commercial <= 20:
        return "informational"
    return "mixed"


def _read_brief(cluster_id: int) -> tuple[str, dict[str, Any]]:
    """Return (raw_md, parsed_fields) for one cluster brief.

    Returns ("", {}) when the markdown file is missing (e.g. dry-run with no
    briefs yet, or noise cluster -1).
    """
    display_id = cluster_id + 1
    path = BRIEFINGS / f"cluster_{display_id:02d}.md"
    if not path.is_file():
        return "", {}
    md = path.read_text(encoding="utf-8")

    title_match = re.match(r"#\s+(.+)", md.strip())
    title = title_match.group(1).strip() if title_match else ""
    h1, h2_list = _outline_h2(md)
    fields = {
        "title": title,
        "main_keyword": _meta(md, "Hauptkeyword"),
        "secondary_keywords": _split_secondary(_meta(md, "Nebenkeywords")),
        "search_intent_text": _meta(md, "Suchintention"),
        "recommended_word_count": _parse_word_count(_meta(md, "Empfohlene Wortanzahl")),
        "target_audience": _section(md, "Zielgruppe"),
        "pain_point": _section(md, "Schmerzpunkt"),
        "article_goal": _section(md, "Ziel des Artikels"),
        "h1": h1,
        "h2_outline": h2_list,
        "content_gaps": _benchmark_annotations(md),
        "benchmark_urls": _parse_benchmark_urls(md),
        "cta": _section(md, "Call to Action"),
        "source_path": str(path.relative_to(ROOT)),
    }
    return md, fields


def _build_cluster_record(row: pd.Series, rank: int) -> dict[str, Any]:
    cid = int(row["cluster_id"])
    display_id = cid + 1 if cid >= 0 else cid
    pct_comm = float(row["pct_commercial"])
    _, brief = _read_brief(cid)
    return {
        "cluster_id": cid,
        "display_id": display_id,
        "rank_by_sv": rank,
        "is_noise": cid == -1,
        "label_de": _safe_label(row.get("label_de"), display_id),
        "label_en": _safe_label(row.get("label_en"), display_id),
        "n_keywords": int(row["n_keywords"]),
        "total_search_volume": int(row["total_sv"]),
        "median_search_volume": int(row["median_sv"]),
        "mean_kd": round(float(row["mean_kd"]), 1),
        "median_kd": int(row["median_kd"]),
        "mean_cpc_eur": round(float(row["mean_cpc"]), 2),
        "mean_priority": round(float(row["mean_priority"]), 1),
        "pct_commercial": round(pct_comm, 1),
        "intent_dominant": _intent_from_pct(pct_comm),
        "top_keywords_by_sv": _split_kw_list(row.get("top_5_kw_by_sv")),
        "top_keywords_by_priority": _split_kw_list(row.get("top_3_kw_by_priority")),
        "top_terms": _split_kw_list(row.get("top_terms")),
        "brief": brief,
        "brief_md_path": (
            f"briefings/cluster_{display_id:02d}.md" if cid != -1 and brief else None
        ),
    }


def _build_keyword_record(row: pd.Series, labels_de: dict[int, str],
                          labels_en: dict[int, str]) -> dict[str, Any]:
    cid = int(row["hdb"])
    display_id = cid + 1 if cid >= 0 else cid
    serp = row.get("serp_features")
    serp_list = (
        [s.strip() for s in str(serp).split("|") if s.strip()]
        if isinstance(serp, str) and serp.strip()
        else []
    )

    def _opt_int(v: Any) -> int | None:
        try:
            if pd.isna(v):
                return None
            return int(v)
        except (TypeError, ValueError):
            return None

    def _opt_float(v: Any, ndigits: int = 2) -> float | None:
        try:
            if pd.isna(v):
                return None
            return round(float(v), ndigits)
        except (TypeError, ValueError):
            return None

    return {
        "keyword": str(row["keyword"]),
        "estimated_intent": str(row.get("estimated_intent") or ""),
        "type": str(row.get("type") or ""),
        "notes": str(row.get("notes") or "") if not pd.isna(row.get("notes")) else "",
        "search_volume": _opt_int(row.get("search_volume")),
        "kd": _opt_int(row.get("kd")),
        "cpc_eur": _opt_float(row.get("cpc_eur")),
        "serp_features": serp_list,
        "priority_score": _opt_float(row.get("priority_score"), 1),
        "data_source": str(row.get("data_source") or ""),
        "cluster_id": cid,
        "cluster_display_id": display_id,
        "is_noise": cid == -1,
        "cluster_label_de": labels_de.get(cid, ""),
        "cluster_label_en": labels_en.get(cid, ""),
    }


def _flatten_for_csv(record: dict[str, Any]) -> dict[str, Any]:
    """Flatten a record so it can be written as one CSV row.

    Strategy:
      - Nested dicts (e.g. cluster["brief"]) are merged with `brief_` prefix.
      - Lists of strings are joined with " | " (chosen because semicolons
        and commas appear inside German keywords and would mis-split in
        Sheets).
      - Lists of dicts (benchmark_urls) are serialized as
        "url1 — note1 | url2 — note2".
      - Booleans become "true"/"false" so they import as text consistently.
    """
    out: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                out[f"{key}_{sub_key}"] = _csv_value(sub_value)
        else:
            out[key] = _csv_value(value)
    return out


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        if not value:
            return ""
        if all(isinstance(item, dict) and "url" in item for item in value):
            return " | ".join(
                f"{item.get('url', '')} — {item.get('note', '')}".rstrip(" —")
                for item in value
            )
        return " | ".join(str(item) for item in value)
    return value


def _write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    """Write a list of records to a CSV file, flattening nested fields.

    All rows share the same column set (union of all keys), with empty
    strings for missing values. UTF-8 with a BOM, because Excel and
    Google Sheets handle that more gracefully on Windows.
    """
    flat = [_flatten_for_csv(r) for r in records]
    columns: list[str] = []
    seen: set[str] = set()
    for row in flat:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in flat:
        writer.writerow({c: row.get(c, "") for c in columns})

    path.write_text(buf.getvalue(), encoding="utf-8-sig")
    logger.info("wrote %s (%.1f KB)", path.relative_to(ROOT),
                path.stat().st_size / 1024)


def run(source: str = DEFAULT_SOURCE, run_id: str | None = None) -> None:
    """Write clusters.json, keywords.json, and report.json.

    Mirror copies are placed under reporting/runs/<run_id>/ if the per-run
    folder already exists (i.e. report step has been executed for this run).
    """
    if not PROFILES_CSV.exists():
        raise SystemExit(
            f"missing {PROFILES_CSV}. Run `python -m src.cluster --step profile` first."
        )
    if not LABELED_CSV.exists():
        raise SystemExit(
            f"missing {LABELED_CSV}. Run `python -m src.cluster --step profile` first."
        )

    REPORTING.mkdir(parents=True, exist_ok=True)
    run_id = run_id or date.today().isoformat()

    profiles = pd.read_csv(PROFILES_CSV).sort_values("total_sv", ascending=False)
    labeled = pd.read_csv(LABELED_CSV)

    cluster_records: list[dict[str, Any]] = []
    rank = 0
    for _, row in profiles.iterrows():
        if int(row["cluster_id"]) != -1:
            rank += 1
            cluster_records.append(_build_cluster_record(row, rank))
    for _, row in profiles.iterrows():
        if int(row["cluster_id"]) == -1:
            cluster_records.append(_build_cluster_record(row, 0))

    labels_de = {int(r["cluster_id"]): _safe_label(r.get("label_de"), int(r["cluster_id"]) + 1)
                 for _, r in profiles.iterrows()}
    labels_en = {int(r["cluster_id"]): _safe_label(r.get("label_en"), int(r["cluster_id"]) + 1)
                 for _, r in profiles.iterrows()}

    keyword_records = [
        _build_keyword_record(row, labels_de, labels_en)
        for _, row in labeled.iterrows()
    ]

    real = profiles[profiles["cluster_id"] != -1]
    totals = {
        "n_keywords": int(len(labeled)),
        "n_clusters": int(len(real)),
        "n_outliers": int((labeled["hdb"] == -1).sum()) if "hdb" in labeled.columns else 0,
        "total_search_volume": int(real["total_sv"].sum()) if len(real) else 0,
        "mean_kd": round(float(real["mean_kd"].mean()), 1) if len(real) else 0.0,
    }

    bundle = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "totals": totals,
        "clusters": cluster_records,
        "keywords": keyword_records,
    }

    def _write(path: Path, data: Any) -> None:
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        logger.info("wrote %s (%.1f KB)", path.relative_to(ROOT),
                    path.stat().st_size / 1024)

    _write(REPORTING / "clusters.json", cluster_records)
    _write(REPORTING / "keywords.json", keyword_records)
    _write(REPORTING / "report.json", bundle)
    _write_csv(REPORTING / "clusters.csv", cluster_records)
    _write_csv(REPORTING / "keywords.csv", keyword_records)

    run_dir = RUNS_DIR / run_id
    if run_dir.is_dir():
        for name in ("clusters.json", "keywords.json", "report.json",
                     "clusters.csv", "keywords.csv"):
            shutil.copy2(REPORTING / name, run_dir / name)
        logger.info("mirrored exports into %s", run_dir.relative_to(ROOT))
    else:
        logger.info("per-run folder %s does not exist yet, skipped mirror copy",
                    run_dir.relative_to(ROOT))


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", default=DEFAULT_SOURCE,
                        help="Label for the keyword source (e.g. llm-generated, semrush).")
    parser.add_argument("--run-id", default=None,
                        help="Run folder name. Defaults to today's date.")
    args = parser.parse_args()
    run(source=args.source, run_id=args.run_id)


if __name__ == "__main__":
    main()
