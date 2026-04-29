"""Enrich step of the SEO keyword pipeline.

Adds search_volume, keyword difficulty (KD), CPC, SERP feature flags, and
a priority score to each keyword in `data/keywords.csv`.

Two modes:

  * `estimate` (default): deterministic heuristics seeded by the keyword's
    SHA256 hash. Repeatable, free, and good enough for shaping clusters and
    drafting briefs. Marked `data_source=estimated` so downstream code knows.
  * `dataforseo`: live lookup via the DataForSEO Labs API. Requires
    DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD env vars. Marked `data_source=dataforseo`.

Heuristic ranges were calibrated by looking at a handful of zvoove-relevant
keywords on free Keyword.io / Google Trends to keep numbers within a sane
order of magnitude. Documented in docs/methodology.md.

CLI:
    python -m src.enrich
    python -m src.enrich --provider dataforseo
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
from pathlib import Path
from typing import Iterable

from src.config import settings

import logging
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DEFAULT_CSV = DATA / "keywords.csv"

# ---------------------------------------------------------------------------
# Heuristic estimator (deterministic via keyword hash)
# ---------------------------------------------------------------------------

VOL_RANGE = {
    "head": (800, 6000),
    "body": (80, 800),
    "longtail": (10, 200),
}
KD_RANGE_BY_INTENT = {
    "commercial": (35, 75),
    "informational": (15, 55),
    "transactional": (50, 85),
    "navigational": (5, 30),
}
CPC_RANGE_BY_INTENT = {
    "commercial": (2.00, 12.00),
    "transactional": (4.00, 18.00),
    "informational": (0.30, 2.50),
    "navigational": (0.10, 1.00),
}
SERP_FEATURES_BY_INTENT = {
    "commercial": ["ads", "shopping", "site-links"],
    "informational": ["featured-snippet", "people-also-ask", "video"],
    "transactional": ["ads", "reviews", "shopping"],
    "navigational": ["knowledge-panel", "site-links"],
}


def _seed(keyword: str) -> int:
    return int(hashlib.sha256(keyword.encode("utf-8")).hexdigest()[:8], 16)


def _frand(keyword: str, salt: str, lo: float, hi: float) -> float:
    h = int(hashlib.sha256((salt + "|" + keyword).encode()).hexdigest()[:8], 16)
    return lo + (h / 0xFFFFFFFF) * (hi - lo)


def estimate(row: dict) -> dict:
    kw = row["keyword"]
    typ = row.get("type", "body")
    intent = row.get("estimated_intent", "informational")

    vlo, vhi = VOL_RANGE.get(typ, VOL_RANGE["body"])
    volume = int(_frand(kw, "vol", vlo, vhi))

    kdlo, kdhi = KD_RANGE_BY_INTENT.get(intent, (20, 50))
    type_bonus = {"head": 12, "body": 0, "longtail": -8}.get(typ, 0)
    kd = max(1, min(95, int(_frand(kw, "kd", kdlo, kdhi) + type_bonus)))

    clo, chi = CPC_RANGE_BY_INTENT.get(intent, (0.5, 3.0))
    cpc = round(_frand(kw, "cpc", clo, chi), 2)

    pool = SERP_FEATURES_BY_INTENT.get(intent, ["people-also-ask"])
    n = 1 + (_seed(kw) % 3)
    feats = []
    for i in range(min(n, len(pool))):
        feats.append(pool[(_seed(kw + str(i))) % len(pool)])
    serp_features = "|".join(sorted(set(feats)))

    priority = round(volume / max(kd, 5), 1)

    return {
        "search_volume": volume,
        "kd": kd,
        "cpc_eur": cpc,
        "serp_features": serp_features,
        "priority_score": priority,
        "data_source": "estimated",
    }


# ---------------------------------------------------------------------------
# DataForSEO live provider
# ---------------------------------------------------------------------------


def fetch_dataforseo(keywords: Iterable[str]) -> dict[str, dict]:
    """Live lookup via DataForSEO Google Ads search-volume endpoint.

    Returns: {keyword: {search_volume, kd, cpc_eur, serp_features}}.
    The KD here is `competition_index` (0-100), close enough to Ahrefs/Semrush
    KD for prioritisation. SERP features need a separate endpoint, left empty.
    """
    import base64
    import json
    import urllib.request

    login = os.environ.get("DATAFORSEO_LOGIN")
    pwd = os.environ.get("DATAFORSEO_PASSWORD")
    if not (login and pwd):
        raise RuntimeError("DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD not set.")

    auth = base64.b64encode(f"{login}:{pwd}".encode()).decode()
    url = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
    out: dict[str, dict] = {}
    BATCH = 1000
    kws = list(keywords)
    for i in range(0, len(kws), BATCH):
        chunk = kws[i:i + BATCH]
        payload = json.dumps([{
            "language_code": "de",
            "location_code": 2276,
            "keywords": chunk,
        }]).encode()
        req = urllib.request.Request(
            url, data=payload,
            headers={"Authorization": f"Basic {auth}",
                     "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        for item in (data.get("tasks") or [{}])[0].get("result") or []:
            kw = item.get("keyword")
            if not kw:
                continue
            out[kw] = {
                "search_volume": item.get("search_volume") or 0,
                "kd": item.get("competition_index") or 0,
                "cpc_eur": round(item.get("cpc") or 0.0, 2),
                "serp_features": "",
            }
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run(provider: str, in_csv: Path, out_csv: Path) -> None:
    rows = list(csv.DictReader(open(in_csv, encoding="utf-8")))
    logger.info(f"read {len(rows)} keywords from {in_csv.relative_to(ROOT)}")

    live: dict[str, dict] = {}
    if provider == "dataforseo":
        logger.info("fetching live data from DataForSEO ...")
        live = fetch_dataforseo(r["keyword"] for r in rows)
        logger.info(f"enriched {len(live)} keywords from DataForSEO")

    fieldnames = list(rows[0].keys())
    new_cols = ["search_volume", "kd", "cpc_eur", "serp_features",
                "priority_score", "data_source"]
    for c in new_cols:
        if c not in fieldnames:
            fieldnames.append(c)

    for r in rows:
        if provider == "dataforseo" and r["keyword"] in live:
            d = live[r["keyword"]]
            r["search_volume"] = d["search_volume"]
            r["kd"] = d["kd"]
            r["cpc_eur"] = d["cpc_eur"]
            r["serp_features"] = d["serp_features"]
            r["priority_score"] = round(
                (d["search_volume"] or 0) / max(d["kd"] or 5, 5), 1)
            r["data_source"] = "dataforseo"
        else:
            r.update(estimate(r))

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    logger.info(f"wrote {out_csv.relative_to(ROOT)}")


def main() -> None:
    setup_logging()
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--provider", choices=["estimate", "dataforseo"], default=None,
                   help=f"default from settings: {settings.enrich_provider}")
    p.add_argument("--in", dest="inp", default=str(DEFAULT_CSV))
    p.add_argument("--out", dest="outp", default=str(DEFAULT_CSV))
    args = p.parse_args()
    provider = args.provider or settings.enrich_provider
    run(provider, Path(args.inp), Path(args.outp))


if __name__ == "__main__":
    sys.exit(main())
