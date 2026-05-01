"""Report step of the SEO keyword pipeline.

Produces a two-level reporting structure:

  - `output/reporting/runs/<run_id>/index.html` per-run dashboard
    (KPI summary, cluster mini-grid, diagnostic charts, brief cards).
    The folder is self-contained: charts, the interactive cluster map,
    and brief markdowns are copied in so each run stays viewable even
    after the next run overwrites `output/clustering/` and `output/briefings/`.
  - `output/reporting/index.html` the runs index, one card per run with
    keyword count, cluster count, source label, and a link into the
    per-run dashboard. This is the landing page on GitHub Pages.

A `run.json` next to each per-run dashboard captures metadata so the
runs index can render without re-reading dashboards.

CLI:
    python -m src.report [--source semrush]
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from src.logging_config import setup_logging
from src.briefs_html import build_page, LABELED_CSV

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
REPORTING = OUT / "reporting"
RUNS_DIR = REPORTING / "runs"
PROFILES_CSV = OUT / "clustering" / "cluster_profiles.csv"
CLUSTERING = OUT / "clustering"
BRIEFINGS = OUT / "briefings"
F_UMAP_2D = CLUSTERING / "umap_2d.npy"
F_VIZ = CLUSTERING / "cluster_map.html"

DEFAULT_SOURCE = "llm-generated"


def _load_cluster_labels() -> tuple[dict[int, str], dict[int, str]]:
    """LLM-generated labels (output/clustering/cluster_labels.json) win over
    the curated YAML if present. The JSON is produced by `src.labels_llm`."""
    import json as _json
    json_path = CLUSTERING / "cluster_labels.json"
    if json_path.exists():
        data = _json.loads(json_path.read_text(encoding="utf-8"))
        en = {int(k): v["en"] for k, v in data.items()}
        de = {int(k): v["de"] for k, v in data.items()}
        return en, de
    import yaml
    with open(ROOT / "data" / "cluster_labels.yaml") as f:
        data = yaml.safe_load(f)
    en = {int(k): v for k, v in data.get("en", {}).items()}
    de = {int(k): v for k, v in data.get("de", {}).items()}
    return en, de


def _render_charts() -> None:
    """Generate six diagnostic PNGs from clustering CSVs into output/clustering/."""
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "DejaVu Sans"

    labels_en, _ = _load_cluster_labels()
    df = pd.read_csv(LABELED_CSV)
    red2 = np.load(F_UMAP_2D)
    df["x"], df["y"] = red2[:, 0], red2[:, 1]

    clusters = sorted([c for c in df["hdb"].unique() if c != -1])
    cmap = plt.cm.tab20(np.linspace(0, 1, len(clusters)))

    fig, ax = plt.subplots(figsize=(13, 9))
    noise = df[df["hdb"] == -1]
    ax.scatter(noise["x"], noise["y"], c="#cccccc", s=10, alpha=0.4, label="noise")
    for i, cid in enumerate(clusters):
        sub = df[df["hdb"] == cid]
        ax.scatter(sub["x"], sub["y"], c=[cmap[i]], s=14, alpha=0.85,
                   label=f"{cid + 1}: {labels_en.get(int(cid), f'Cluster {int(cid) + 1}')[:30]}")
        cx, cy = sub["x"].mean(), sub["y"].mean()
        ax.text(cx, cy, str(cid + 1), fontsize=11, fontweight="bold",
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="black", lw=0.6))
    ax.set_title("UMAP map of HDBSCAN keyword clusters", fontsize=13)
    ax.set_xlabel("UMAP-1"); ax.set_ylabel("UMAP-2")
    ax.legend(loc="lower left", bbox_to_anchor=(1.02, 0), fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(CLUSTERING / "chart1_umap_map.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 7))
    for i, cid in enumerate(clusters):
        sub = df[df["hdb"] == cid]
        ax.scatter(sub["kd"], sub["search_volume"], c=[cmap[i]], s=sub["priority_score"] * 8,
                   alpha=0.6, edgecolors="white", linewidths=0.5)
    ax.set_xlabel("Keyword Difficulty (0-100)"); ax.set_ylabel("Search volume / month")
    ax.set_yscale("log"); ax.set_title("Per-keyword: difficulty vs. volume (size = priority)")
    fig.tight_layout()
    fig.savefig(CLUSTERING / "chart2_bubble.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

    agg = (df[df["hdb"] != -1].groupby(["hdb", "hdb_label"])
           .agg(n=("keyword", "count"), total_sv=("search_volume", "sum"))
           .reset_index().sort_values("total_sv", ascending=True))
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(agg)), agg["total_sv"], color=[cmap[clusters.index(c)] for c in agg["hdb"]])
    ax.set_yticks(range(len(agg)))
    ax.set_yticklabels([f"{c + 1}: {l}" for c, l in zip(agg["hdb"], agg["hdb_label"])], fontsize=9)
    ax.set_xlabel("Total search volume / month")
    ax.set_title("Cluster size by total search volume")
    fig.tight_layout()
    fig.savefig(CLUSTERING / "chart3_cluster_volume.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

    agg2 = (df[df["hdb"] != -1].groupby(["hdb", "hdb_label"])
            .agg(mean_kd=("kd", "mean"), tot_sv=("search_volume", "sum"))
            .reset_index())
    fig, ax = plt.subplots(figsize=(10, 7))
    for _, r in agg2.iterrows():
        i = clusters.index(int(r["hdb"]))
        ax.scatter(r["mean_kd"], r["tot_sv"], c=[cmap[i]], s=400, alpha=0.7,
                   edgecolors="white", linewidths=1.5)
        ax.annotate(f"{int(r['hdb']) + 1}: {r['hdb_label'][:22]}",
                    (r["mean_kd"], r["tot_sv"]), fontsize=8.5, ha="center", va="center")
    ax.set_xlabel("Mean Keyword Difficulty"); ax.set_ylabel("Total search volume / month")
    ax.set_yscale("log"); ax.set_title("Cluster priority matrix: difficulty vs. opportunity")
    ax.axvline(50, color="grey", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(CLUSTERING / "chart4_priority_matrix.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

    mix = (df[df["hdb"] != -1]
           .pivot_table(index=["hdb", "hdb_label"], columns="estimated_intent",
                        values="keyword", aggfunc="count", fill_value=0)
           .reset_index())
    fig, ax = plt.subplots(figsize=(11, 6))
    y = np.arange(len(mix))
    intent_cols = [c for c in mix.columns if c not in ("hdb", "hdb_label")]
    bottoms = np.zeros(len(mix))
    intent_colors = {"commercial": "#e8965e", "informational": "#5e8de8"}
    for col in intent_cols:
        ax.barh(y, mix[col], left=bottoms,
                color=intent_colors.get(col, "#888888"), label=col)
        bottoms += mix[col].values
    ax.set_yticks(y)
    ax.set_yticklabels([f"{int(c) + 1}: {l[:30]}" for c, l in zip(mix["hdb"], mix["hdb_label"])], fontsize=9)
    ax.set_xlabel("Number of keywords"); ax.set_title("Intent mix per cluster")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CLUSTERING / "chart5_intent_mix.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    mask = df["hdb"] != -1
    orig = df["category"].astype("category").cat.codes
    pairs = [
        ("HDBSCAN vs LLM", orig[mask], df["hdb"][mask]),
        ("Hier(10) vs LLM", orig, df["hier10"]),
        ("Hier(12) vs LLM", orig, df["hier12"]),
        ("HDB vs Hier(10)", df["hier10"][mask], df["hdb"][mask]),
    ]
    chart_labels = [p[0] for p in pairs]
    aris = [adjusted_rand_score(a, b) for _, a, b in pairs]
    nmis = [normalized_mutual_info_score(a, b) for _, a, b in pairs]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(chart_labels))
    ax.bar(x - 0.2, aris, 0.4, label="ARI", color="#5e8de8")
    ax.bar(x + 0.2, nmis, 0.4, label="NMI", color="#e8965e")
    ax.set_xticks(x); ax.set_xticklabels(chart_labels, rotation=15, ha="right", fontsize=9)
    ax.set_ylim(0, 1); ax.set_title("Cluster method agreement (higher = more agreement)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CLUSTERING / "chart6_method_agreement.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

    logger.info("wrote 6 PNGs to %s", CLUSTERING.relative_to(ROOT))


def _render_cluster_map() -> None:
    """Generate the interactive bilingual Plotly cluster map."""
    from src.cluster_viz import build_cluster_map_html
    labels_en, labels_de = _load_cluster_labels()
    df = pd.read_csv(LABELED_CSV)
    red2 = np.load(F_UMAP_2D)
    html = build_cluster_map_html(df, red2, labels_en=labels_en, labels_de=labels_de)
    F_VIZ.write_text(html)
    logger.info("wrote %s (%.0f KB)", F_VIZ.relative_to(ROOT), F_VIZ.stat().st_size / 1024)


_CHART_MODAL_CSS = """
.chart-thumb{cursor:zoom-in;display:block;width:100%;border:1px solid #e2e8f0;
             border-radius:6px;background:white;transition:transform .15s,box-shadow .15s}
.chart-thumb:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(15,23,42,0.08)}
.chart-modal{position:fixed;inset:0;background:rgba(15,23,42,0.85);display:none;
             align-items:center;justify-content:center;z-index:9999;padding:24px;cursor:zoom-out}
.chart-modal.open{display:flex}
.chart-modal img{max-width:100%;max-height:100%;border-radius:8px;background:white;
                 box-shadow:0 20px 60px rgba(0,0,0,0.5)}
.chart-modal-close{position:absolute;top:16px;right:20px;background:none;border:0;
                   color:white;font-size:32px;line-height:1;cursor:pointer;padding:8px}
"""

_CHART_MODAL_JS = """
(function(){
  const modal=document.getElementById('chart-modal');
  const modalImg=modal.querySelector('img');
  document.querySelectorAll('.chart-thumb').forEach(img=>{
    img.addEventListener('click',()=>{modalImg.src=img.src;modalImg.alt=img.alt;modal.classList.add('open');});
  });
  modal.addEventListener('click',e=>{if(e.target===modal||e.target.classList.contains('chart-modal-close'))modal.classList.remove('open');});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')modal.classList.remove('open');});
})();
"""


def _charts_section(chart_dir: str = "charts/") -> str:
    imgs = "".join(
        f"<img class='chart-thumb' src='{chart_dir}{f.name}' alt='{f.name}'>"
        for f in sorted(CLUSTERING.glob("chart*.png"))
    )
    if not imgs:
        return ""
    return (
        f'<style>{_CHART_MODAL_CSS}</style>'
        '<div style="margin-bottom:40px;border-top:1px solid #e2e8f0;padding-top:28px;">'
        '<p style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;'
        'letter-spacing:0.04em;margin:0 0 12px;">Diagnose Charts</p>'
        '<p style="font-size:13px;margin:0 0 14px;color:#64748b;">'
        '<a href="cluster_map.html" style="color:#0d9488">'
        'Interaktive Cluster Map öffnen →</a> · '
        '<span>Klick auf ein Chart öffnet die Großansicht.</span></p>'
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:14px;">'
        f'{imgs}</div></div>'
        '<div class="chart-modal" id="chart-modal" role="dialog" aria-label="Chart Vollbild">'
        '<button class="chart-modal-close" aria-label="Schließen">×</button>'
        '<img src="" alt=""></div>'
        f'<script>{_CHART_MODAL_JS}</script>'
    )


def _copy_assets(run_dir: Path) -> None:
    """Copy artifacts so the per-run dashboard is self-contained."""
    charts_dst = run_dir / "charts"
    charts_dst.mkdir(parents=True, exist_ok=True)
    for png in sorted(CLUSTERING.glob("chart*.png")):
        shutil.copy2(png, charts_dst / png.name)

    map_src = CLUSTERING / "cluster_map.html"
    if map_src.exists():
        shutil.copy2(map_src, run_dir / "cluster_map.html")

    briefs_dst = run_dir / "briefings"
    briefs_dst.mkdir(parents=True, exist_ok=True)
    for md in sorted(BRIEFINGS.glob("cluster_*.md")):
        shutil.copy2(md, briefs_dst / md.name)


def _write_run_metadata(run_dir: Path, run_id: str, source: str,
                        profiles: pd.DataFrame, labeled: pd.DataFrame) -> dict:
    real = profiles[profiles["cluster_id"] != -1]
    n_clusters = int(len(real))
    n_outliers = int((labeled["hdb"] == -1).sum()) if "hdb" in labeled.columns else 0
    n_keywords = int(len(labeled))
    total_sv = int(real["total_sv"].sum()) if "total_sv" in real.columns else 0
    meta = {
        "run_id": run_id,
        "date": "-".join(run_id.split("-")[:3]),
        "source": source,
        "n_keywords": n_keywords,
        "n_clusters": n_clusters,
        "n_outliers": n_outliers,
        "total_search_volume": total_sv,
    }
    (run_dir / "run.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return meta


def _load_runs() -> list[dict]:
    if not RUNS_DIR.exists():
        return []
    runs = []
    for run_dir in sorted(RUNS_DIR.iterdir(), reverse=True):
        meta_file = run_dir / "run.json"
        if not meta_file.is_file():
            continue
        try:
            runs.append(json.loads(meta_file.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            logger.warning("could not parse %s, skipping", meta_file)
    return runs


_INDEX_CSS = """
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;
     color:#0f172a;background:#f8fafc;margin:0;padding:32px 24px;line-height:1.5}
.wrap{max-width:1100px;margin:0 auto}
.back-nav{display:flex;gap:14px;margin:0 0 18px;flex-wrap:wrap}
.back-link{font-size:13px;color:#0d9488;text-decoration:none;font-weight:500}
.back-link:hover{text-decoration:underline}
header{margin-bottom:32px}
h1{font-size:28px;margin:0 0 8px;letter-spacing:-0.01em}
.lead{color:#475569;margin:0;max-width:680px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;margin-top:24px}
.card{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:20px;
      transition:border-color .15s,transform .15s;display:flex;flex-direction:column;gap:10px}
.card:hover{border-color:#0d9488;transform:translateY(-1px)}
.card-id{font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;
         letter-spacing:0.04em;margin:0}
.card-title{font-size:18px;font-weight:600;margin:0;color:#0f172a;text-decoration:none}
.card-title:hover{color:#0d9488}
.kpi-row{display:flex;flex-wrap:wrap;gap:14px;margin-top:6px}
.kpi{font-size:13px}
.kpi b{display:block;font-size:18px;color:#0f172a}
.kpi span{color:#64748b;font-size:12px}
.source-badge{display:inline-block;font-size:11px;padding:3px 8px;border-radius:4px;
              background:#ecfdf5;color:#047857;font-weight:600;letter-spacing:0.02em}
.card-actions{display:flex;gap:14px;margin-top:auto;padding-top:12px;
              border-top:1px solid #f1f5f9;font-size:13px}
.card-actions a{color:#0d9488;text-decoration:none;font-weight:500}
.card-actions a:hover{text-decoration:underline}
.empty{padding:40px;text-align:center;color:#64748b;border:1px dashed #cbd5e1;border-radius:10px}
"""


_SOURCE_LABELS = {
    "llm-generated": "LLM-kuratiertes Set",
    "manual": "Manuelle CSV",
    "semrush": "SEMrush API",
    "ahrefs": "Ahrefs API",
    "dataforseo": "DataForSEO API",
}

_SOURCE_TOOLTIPS = {
    "llm-generated": ("Eintrittspunkt: vorab mit Hilfe eines LLM aus den "
                      "zvoove-Blog-Themen abgeleitete Keyword-Liste "
                      "(data/keywords.manual.csv, frozen)."),
    "manual": "Eintrittspunkt: handgepflegte CSV.",
    "semrush": "Eintrittspunkt: SEMrush Domain-Analytics-API.",
    "ahrefs": "Eintrittspunkt: Ahrefs Keywords-Explorer-API.",
    "dataforseo": "Eintrittspunkt: DataForSEO Labs API.",
}


def _render_runs_index(runs: list[dict]) -> str:
    if not runs:
        body = '<div class="empty">Keine Läufe gefunden. Pipeline ausführen, dann erscheint hier eine Karte je Lauf.</div>'
    else:
        cards = []
        for r in runs:
            sv = f"{r.get('total_search_volume', 0):,}".replace(",", ".")
            run_id = r['run_id']
            source_key = r.get('source', DEFAULT_SOURCE)
            source_label = _SOURCE_LABELS.get(source_key, source_key)
            source_tooltip = _SOURCE_TOOLTIPS.get(source_key, f"Eintrittspunkt: {source_key}")
            cards.append(f"""
<article class="card">
  <p class="card-id">Lauf {run_id}</p>
  <a class="card-title" href="runs/{run_id}/index.html">{r['n_keywords']} Keywords · {r['n_clusters']} Cluster</a>
  <span class="source-badge" title="{source_tooltip}">Quelle: {source_label}</span>
  <div class="kpi-row">
    <div class="kpi"><b>{r['n_keywords']}</b><span>Keywords</span></div>
    <div class="kpi"><b>{r['n_clusters']}</b><span>Cluster</span></div>
    <div class="kpi"><b>{r['n_outliers']}</b><span>Ausreißer</span></div>
    <div class="kpi"><b>{sv}</b><span>SV gesamt</span></div>
  </div>
  <div class="card-actions">
    <a href="runs/{run_id}/index.html">Dashboard öffnen →</a>
    <a href="runs/{run_id}/cluster_map.html">Cluster Map öffnen →</a>
  </div>
</article>""")
        body = f'<div class="grid">{"".join(cards)}</div>'

    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pipeline-Läufe · zvoove SEO Pipeline</title>
<style>{_INDEX_CSS}</style>
</head><body><div class="wrap">
<nav class="back-nav">
  <a class="back-link" href="../../index.html">← Zurück zur Doku</a>
</nav>
<header>
  <h1>Pipeline-Läufe</h1>
  <p class="lead">Übersicht aller Läufe der SEO-Keyword-Pipeline. Jeder Lauf hat seinen eigenen
  Eintrittspunkt (LLM-erzeugte Liste, Semrush-Export, etc.) und ein eigenes Dashboard mit
  Clustern, Briefs, Diagnose-Charts und einer interaktiven Cluster-Karte. Karte anklicken,
  um den Lauf zu öffnen.</p>
</header>
{body}
</div></body></html>"""


def run(source: str = DEFAULT_SOURCE, run_id: str | None = None) -> None:
    if not PROFILES_CSV.exists():
        raise SystemExit(
            f"missing {PROFILES_CSV}. Run `python -m src.cluster --step profile` first."
        )
    REPORTING.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    profiles = pd.read_csv(PROFILES_CSV)
    labeled = pd.read_csv(LABELED_CSV)

    run_id = run_id or date.today().isoformat()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    _render_cluster_map()
    _copy_assets(run_dir)

    page = build_page(
        profiles,
        labeled,
        brief_prefix="briefings/",
        extra_section="",
        map_prefix="",
        briefings_dir=run_dir / "briefings",
        back_links=[
            ("Zurück zur Lauf-Übersicht", "../../index.html"),
            ("Zurück zur Doku", "../../../../index.html"),
        ],
    )
    (run_dir / "index.html").write_text(page, encoding="utf-8")

    meta = _write_run_metadata(run_dir, run_id, source, profiles, labeled)
    logger.info("wrote run %s (%d keywords, %d clusters)",
                run_id, meta["n_keywords"], meta["n_clusters"])

    runs = _load_runs()
    index_html = _render_runs_index(runs)
    (REPORTING / "index.html").write_text(index_html, encoding="utf-8")
    logger.info("wrote runs index with %d run(s)", len(runs))


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", default=DEFAULT_SOURCE,
                        help="Label for the keyword source (e.g. llm-generated, semrush, ahrefs).")
    parser.add_argument("--run-id", default=None,
                        help="Run folder name. Defaults to today's date; pass a custom id "
                             "(e.g. 2026-04-30-semrush) for parallel same-day runs.")
    args = parser.parse_args()
    run(source=args.source, run_id=args.run_id)


if __name__ == "__main__":
    main()
