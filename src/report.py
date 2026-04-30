"""Report step of the SEO keyword pipeline.

Generates a single combined HTML dashboard at `output/reporting/index.html`
that merges the KPI summary, diagnostic chart gallery, and all cluster content
briefs into one scrollable page.

Page structure (top to bottom):

  1. Header with title, cluster-map CTA, and glossary button.
  2. KPI row: total keywords, clusters, search volume, mean KD.
  3. Mini-grid: clickable cluster navigation cards sorted by search volume.
  4. Diagnose Charts: the six matplotlib PNGs + link to interactive cluster map.
  5. Cluster brief cards: one full card per cluster, sorted by search volume,
     with top keywords, intent, target audience, page structure, SERP gaps, CTA.
  6. Glossary modal (JS, no external deps).

Single file, no JS framework, no external dependencies beyond what is
already on disk. Open in any browser.

CLI:
    python -m src.report
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import logging
from src.logging_config import setup_logging
from src.briefs_html import build_page, LABELED_CSV

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
REPORTING = OUT / "reporting"
PROFILES_CSV = OUT / "clustering" / "cluster_profiles.csv"
CLUSTERING = OUT / "clustering"


def _charts_section() -> str:
    imgs = "".join(
        f"<img src='../clustering/{f.name}' alt='{f.name}' "
        f"style='width:100%;border:1px solid #e2e8f0;border-radius:6px;background:white'>"
        for f in sorted(CLUSTERING.glob("chart*.png"))
    )
    if not imgs:
        return ""
    return (
        '<div style="margin-bottom:40px;border-top:1px solid #e2e8f0;padding-top:28px;">'
        '<p style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;'
        'letter-spacing:0.04em;margin:0 0 12px;">Diagnose Charts</p>'
        '<p style="font-size:13px;margin:0 0 14px;">'
        '<a href="../clustering/cluster_map.html" style="color:#0d9488">'
        'Interaktive Cluster Map öffnen →</a></p>'
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:14px;">'
        f'{imgs}</div></div>'
    )


def run() -> None:
    if not PROFILES_CSV.exists():
        raise SystemExit(
            f"missing {PROFILES_CSV}. Run `python -m src.cluster --step profile` first."
        )
    REPORTING.mkdir(parents=True, exist_ok=True)
    profiles = pd.read_csv(PROFILES_CSV)
    labeled = pd.read_csv(LABELED_CSV)
    charts_html = _charts_section()
    page = build_page(
        profiles,
        labeled,
        brief_prefix="../briefings/",
        extra_section=charts_html,
    )
    out = REPORTING / "index.html"
    out.write_text(page, encoding="utf-8")
    logger.info("wrote %s (%.1f KB)", out.relative_to(ROOT), out.stat().st_size / 1024)


def main() -> None:
    setup_logging()
    argparse.ArgumentParser(description=__doc__.split("\n\n")[0]).parse_args()
    run()


if __name__ == "__main__":
    main()
