"""Discover step of the SEO keyword pipeline.

Goal: turn the live zvoove blog at https://zvoove.de/wissen/blog into a seed
keyword set that the rest of the pipeline can enrich, cluster, and brief on.

Status: STUB. Not yet implemented end to end.

What is implemented:

  * `--source manual` reads the existing `data/keywords.manual.csv`
    (the recovered baseline) and writes it to `data/keywords.csv`. This
    keeps the pipeline runnable while the live discovery step is built.

What is NOT yet implemented:

  * Crawl https://zvoove.de/wissen/blog, paginate the index, extract
    article titles and topical signals.
  * Expand each article into a seed keyword set via Claude API
    (head, body, longtail variants, German morphology aware).
  * Filter to a max of 500 keywords, ranked by relevance.
  * Write to `data/keywords.csv` with columns:
    keyword, estimated_intent, category, type, notes.

Why stubbed for now: the higher-leverage work in this case study is the
clustering and briefs. The discover step is the next focused work item;
see docs/decisions.md for the trade-off.

CLI:
    python -m src.discover --source manual
    python -m src.discover --source live      # not yet implemented
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MANUAL_CSV = DATA / "keywords.manual.csv"
CANONICAL_CSV = DATA / "keywords.csv"


def discover_manual() -> None:
    if not MANUAL_CSV.exists():
        sys.exit(f"missing {MANUAL_CSV}. The manual baseline was lost.")
    shutil.copy(MANUAL_CSV, CANONICAL_CSV)
    print(f"[discover] copied {MANUAL_CSV.relative_to(ROOT)} -> "
          f"{CANONICAL_CSV.relative_to(ROOT)}")


def discover_live() -> None:
    raise NotImplementedError(
        "Live blog scraping not implemented yet. Use --source manual for now. "
        "See docs/decisions.md for the planned design."
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--source", choices=["manual", "live"], default="manual")
    args = p.parse_args()
    if args.source == "manual":
        discover_manual()
    else:
        discover_live()


if __name__ == "__main__":
    main()
