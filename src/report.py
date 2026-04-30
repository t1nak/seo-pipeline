"""Report step of the SEO keyword pipeline.

Generates a single self-contained `output/reporting/index.html` that pulls
the cluster_profiles, the per-cluster briefs, and the chart PNGs into one
page. This is the page a stakeholder opens to see the result of a run.

Three sections, top to bottom:

  1. Top-line numbers (total keywords, clusters, total search volume,
     mean keyword difficulty, mean priority).
  2. Cluster table, sorted by total search volume. One row per cluster
     with id, label (DE), keyword count, total SV, mean KD, mean CPC,
     percent commercial, and a link to the per-cluster brief.
  3. Embedded chart gallery (the six matplotlib PNGs) and a link to the
     interactive cluster_map.html.

Single file, no JS framework, no external dependencies beyond what is
already on disk. Open in any browser.

CLI:
    python -m src.report
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path

import pandas as pd

import logging
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
REPORTING = OUT / "reporting"
PROFILES_CSV = OUT / "clustering" / "cluster_profiles.csv"
BRIEFINGS = OUT / "briefings"
CLUSTERING = OUT / "clustering"


CSS = """*{box-sizing:border-box}html{background:#f4f4f6;min-height:100%}body{margin:0;padding:32px 24px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f4f4f6;color:#222;line-height:1.55}
.wrap{max-width:1200px;margin:0 auto}
h1{font-size:28px;margin:0 0 6px}h2{font-size:20px;margin:36px 0 12px;border-top:1px solid #e0e0e0;padding-top:24px}
.lead{color:#555;margin:0 0 28px}
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:16px 0 8px}
.kpi{background:white;border:1px solid #e0e0e0;border-radius:8px;padding:14px 16px}
.kpi .label{font-size:11px;color:#666;text-transform:uppercase;letter-spacing:0.04em}
.kpi .value{font-size:22px;font-weight:600;color:#222;margin-top:4px;font-variant-numeric:tabular-nums}
table{width:100%;border-collapse:collapse;background:white;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;font-size:13px}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid #f0f0f0}
th{background:#fafafa;font-weight:600;color:#444;font-size:11px;text-transform:uppercase;letter-spacing:0.04em}
td.num{text-align:right;font-variant-numeric:tabular-nums}
tr:hover td{background:#fafafa}
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:14px;margin-top:14px}
.charts img{width:100%;border:1px solid #e0e0e0;border-radius:6px;background:white}
a{color:#2563eb;text-decoration:none}a:hover{text-decoration:underline}
.cta{display:inline-block;background:#2563eb;color:white;padding:10px 18px;border-radius:8px;font-weight:600;margin-top:10px}
.muted{color:#888;font-size:12px}
"""


def _row(profile: dict, brief_link: str) -> str:
    cid_disp = int(profile["cluster_id"]) + 1
    label = html.escape(profile["label_de"] or "")
    return (f"<tr>"
            f"<td>{cid_disp}</td>"
            f"<td>{label}</td>"
            f"<td class='num'>{profile['n_keywords']}</td>"
            f"<td class='num'>{profile['total_sv']:,}</td>"
            f"<td class='num'>{profile['mean_kd']}</td>"
            f"<td class='num'>{profile['mean_cpc']:.2f}</td>"
            f"<td class='num'>{int(profile['pct_commercial'])} %</td>"
            f"<td>{brief_link}</td>"
            f"</tr>")


def build_html(profiles: pd.DataFrame) -> str:
    real = profiles[profiles["cluster_id"] != -1].copy().sort_values(
        "total_sv", ascending=False)

    n_clusters = len(real)
    total_kw = int(profiles["n_keywords"].sum())
    total_sv = int(real["total_sv"].sum())
    mean_kd = round(float(real["mean_kd"].mean()), 1)
    mean_priority = round(float(real["mean_priority"].mean()), 0) if "mean_priority" in real.columns else "n/a"

    rows = []
    for _, p in real.iterrows():
        cid = int(p["cluster_id"])
        brief_path = BRIEFINGS / f"cluster_{cid + 1:02d}.md"
        if brief_path.exists():
            link = f"<a href='../briefings/cluster_{cid + 1:02d}.md'>Brief lesen</a>"
        else:
            link = "<span class='muted'>kein Brief generiert</span>"
        rows.append(_row(p.to_dict(), link))

    chart_dir = CLUSTERING.relative_to(REPORTING.parent)
    charts = "".join(
        f"<img src='../clustering/{f.name}' alt='{f.name}'>"
        for f in sorted(CLUSTERING.glob("chart*.png"))
    )

    map_link = ("<a class='cta' href='../clustering/cluster_map.html'>"
                "Interaktive Cluster Karte öffnen</a>")

    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<title>SEO Pipeline Report: zvoove</title>
<style>{CSS}</style>
</head><body><div class="wrap">

<h1>SEO Pipeline Report: zvoove</h1>
<p class="lead">Ergebnisse der Keyword Pipeline: Discovery, Clustering, Content Briefs.
Dieser Report wird automatisch aus den Pipeline Artefakten erzeugt.</p>

<div class="kpi-row">
  <div class="kpi"><div class="label">Keywords</div><div class="value">{total_kw}</div></div>
  <div class="kpi"><div class="label">Cluster</div><div class="value">{n_clusters}</div></div>
  <div class="kpi"><div class="label">Gesamt SV / Monat</div><div class="value">{total_sv:,}</div></div>
  <div class="kpi"><div class="label">Mittlere KD</div><div class="value">{mean_kd}</div></div>
  <div class="kpi"><div class="label">Mittlere Priorität</div><div class="value">{mean_priority}</div></div>
</div>

<h2>Cluster nach Suchvolumen</h2>
{map_link}
<table style="margin-top:18px">
<thead><tr><th>#</th><th>Cluster (DE)</th><th>Keywords</th><th>SV / Monat</th>
<th>Ø KD</th><th>Ø CPC</th><th>% Komm.</th><th>Brief</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>

<h2>Diagnose Charts</h2>
<div class="charts">{charts}</div>

</div></body></html>"""


def run() -> None:
    if not PROFILES_CSV.exists():
        raise SystemExit(f"missing {PROFILES_CSV}. Run `python -m src.cluster --step profile` first.")
    REPORTING.mkdir(parents=True, exist_ok=True)
    profiles = pd.read_csv(PROFILES_CSV)
    html_str = build_html(profiles)
    out = REPORTING / "index.html"
    out.write_text(html_str)
    logger.info(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1024:.1f} KB)")


def main() -> None:
    setup_logging()
    argparse.ArgumentParser(description=__doc__.split("\n\n")[0]).parse_args()
    run()


if __name__ == "__main__":
    main()
