"""Discover step of the SEO keyword pipeline.

Goal: turn the live zvoove blog at https://zvoove.de/wissen/blog into a seed
keyword set that the rest of the pipeline can enrich, cluster, and brief on.

Status: STUB. Not yet implemented end to end.

What is implemented:

  * `--source manual` reads the existing `data/keywords.manual.csv`
    (the recovered baseline), caps it at `--max-keywords` (default 500,
    per the case study brief), and writes the result to `data/keywords.csv`.
    If the baseline already carries `priority_score`, the cap keeps the
    top scoring rows; otherwise rows are kept in original order.

What is NOT yet implemented:

  * Crawl https://zvoove.de/wissen/blog, paginate the index, extract
    article titles and topical signals.
  * Expand each article into a seed keyword set via Claude API
    (head, body, longtail variants, German morphology aware).
  * Write to `data/keywords.csv` with columns:
    keyword, estimated_intent, category, type, notes.

Why stubbed for now: the higher-leverage work in this case study is the
clustering and briefs. The discover step is the next focused work item;
see docs/decisions.md for the trade-off.

CLI:
    python -m src.discover --source manual
    python -m src.discover --source manual --max-keywords 300
    python -m src.discover --source live      # not yet implemented
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from src.config import settings

import logging
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MANUAL_CSV = DATA / "keywords.manual.csv"
CANONICAL_CSV = DATA / "keywords.csv"

MAX_KEYWORDS_DEFAULT = settings.discover_max_keywords


def discover_manual(max_keywords: int = MAX_KEYWORDS_DEFAULT) -> None:
    if not MANUAL_CSV.exists():
        sys.exit(f"missing {MANUAL_CSV}. The manual baseline was lost.")
    df = pd.read_csv(MANUAL_CSV)
    n_in = len(df)
    if n_in > max_keywords:
        if "priority_score" in df.columns:
            df = (df.sort_values("priority_score", ascending=False)
                    .head(max_keywords)
                    .reset_index(drop=True))
            mode = "top by priority_score"
        else:
            df = df.head(max_keywords).reset_index(drop=True)
            mode = "first rows"
        logger.info(f"capped {n_in} -> {len(df)} keywords ({mode})")
    df.to_csv(CANONICAL_CSV, index=False)
    logger.info(f"wrote {len(df)} keywords to "
          f"{CANONICAL_CSV.relative_to(ROOT)}")


def discover_live() -> None:
    raise NotImplementedError(
        "Live blog scraping not implemented yet. Use --source manual for now. "
        "See docs/decisions.md for the planned design."
    )


def main() -> None:
    setup_logging()
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--source", choices=["manual", "live"], default="manual")
    p.add_argument("--max-keywords", type=int, default=MAX_KEYWORDS_DEFAULT,
                   help=f"hard cap on output rows (default {MAX_KEYWORDS_DEFAULT}, "
                        f"per the case study brief)")
    args = p.parse_args()
    if args.source == "manual":
        discover_manual(max_keywords=args.max_keywords)
    else:
        discover_live()


if __name__ == "__main__":
    main()
