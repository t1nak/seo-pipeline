"""Render all cluster content briefs as a single HTML dashboard.

The pipeline produces one Markdown brief per cluster in
`output/briefings/cluster_NN.md`. Markdown is the canonical, CMS-portable
format. This module produces an additional consolidated HTML view,
`output/briefings/index.html`, that displays every brief as a card in a
scannable dashboard.

Card structure per cluster (in this order):
    1. Cluster heading (DE label)
    2. Badges: intent, monthly volume, median difficulty
    3. Keywords im Cluster: top 6 from keywords_labeled, with SV / KD / CPC
    4. Suchintention (from the .md brief)
    5. Zielgruppe (from the .md brief)
    6. Empfohlene Seitenstruktur (H1 + the H2s parsed from the Outline)
    7. Inhaltliche Lücken (synthesised from the benchmark-URL annotations)
    8. Empfohlene Länge (from Empfohlene Wortanzahl)
    9. CTA (from Call to Action)

CLI:
    python -m src.briefs_html
"""
from __future__ import annotations

import argparse
import html as htmllib
import re
from pathlib import Path

import pandas as pd

import logging
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
BRIEFINGS = OUT / "briefings"
PROFILES_CSV = OUT / "clustering" / "cluster_profiles.csv"
LABELED_CSV = OUT / "clustering" / "keywords_labeled.csv"


# ---------------------------------------------------------------------------
# Markdown brief parsing
# ---------------------------------------------------------------------------


def _section(md: str, heading: str) -> str:
    """Return the body text of a `## {heading}` section."""
    pattern = rf"##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, md, re.DOTALL)
    return m.group(1).strip() if m else ""


def _meta(md: str, key: str) -> str:
    """Return the value of `**{key}:** ...` (a single-line metadata field)."""
    pattern = rf"\*\*{re.escape(key)}:\*\*\s*(.+?)(?=\n|$)"
    m = re.search(pattern, md)
    return m.group(1).strip() if m else ""


def _outline_h2(md: str) -> tuple[str, list[str]]:
    """Return (H1 text, [H2 texts]) parsed from the Outline section."""
    body = _section(md, "Outline")
    h1 = ""
    h2: list[str] = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("- H1:"):
            h1 = line[len("- H1:"):].strip()
        elif line.startswith("- H2:"):
            h2.append(line[len("- H2:"):].strip())
    return h1, h2


def _benchmark_annotations(md: str) -> list[str]:
    """Return the 'why relevant' annotations from the Benchmark URLs section.

    Each annotation often calls out what the existing top-of-SERP article does
    well or where it falls short. Combined, these read as a content-gap analysis.
    """
    body = _section(md, "Benchmark URLs")
    annotations: list[str] = []
    for line in body.splitlines():
        # Format: "1. URL — annotation" or "1. URL - annotation"
        m = re.match(r"\d+\.\s+\S+\s*[—-]\s*(.+)", line.strip())
        if m:
            annotations.append(m.group(1).strip())
    return annotations


def _intent_class(intent_text: str) -> str:
    """Map a free-text intent description to a badge color class."""
    t = intent_text.lower()
    if "commercial" in t:
        return "ok"
    if "informational" in t:
        return "warn"
    return "info"  # mixed or unknown


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------


_PAGE_CSS = """
:root {
  --bg: #fafafa;
  --bg-card: #ffffff;
  --bg-header: #0f172a;
  --bg-row: #f8fafc;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #0f172a;
  --text-muted: #64748b;
  --text-secondary: #475569;
  --primary: #0d9488;
  --primary-dark: #115e59;
  --accent: #f59e0b;
  --badge-info-bg: #dbeafe;
  --badge-info-fg: #1e40af;
  --badge-warn-bg: #fed7aa;
  --badge-warn-fg: #9a3412;
  --badge-ok-bg: #d1fae5;
  --badge-ok-fg: #065f46;
}
html { scroll-behavior: smooth; scroll-padding-top: 16px; background: var(--bg); min-height: 100%; }
* { box-sizing: border-box; }
body { margin: 0; padding: 32px 24px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       background: var(--bg); color: var(--text); line-height: 1.6; }
.wrap { max-width: 980px; margin: 0 auto; }
header { padding: 24px 32px; background: var(--bg-header); color: white; border-radius: 12px;
         margin-bottom: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
         display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; flex-wrap: wrap; }
header .header-text { flex: 1; min-width: 280px; }
header h1 { margin: 0 0 6px; font-size: 24px; letter-spacing: -0.02em; }
header p { margin: 0; color: #94a3b8; font-size: 13px; }
header .map-cta {
  display: inline-flex; align-items: center; gap: 8px;
  background: var(--primary); color: white; padding: 10px 18px;
  border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600;
  letter-spacing: 0.01em; transition: background 0.18s, transform 0.18s;
  white-space: nowrap; align-self: center;
}
header .map-cta:hover { background: var(--primary-dark); transform: translateY(-1px); }
header .map-cta::before { content: "🗺"; font-size: 14px; }
header .header-actions { display: flex; flex-direction: column; gap: 8px; align-self: center; }
header .glossar-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: transparent; color: white; padding: 8px 14px;
  border: 1px solid rgba(255,255,255,0.25); border-radius: 8px;
  text-decoration: none; font-size: 12px; font-weight: 500;
  cursor: pointer; font-family: inherit;
  transition: background 0.18s, border-color 0.18s;
  white-space: nowrap;
}
header .glossar-btn:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.4); }
header .glossar-btn::before { content: "ⓘ"; font-size: 14px; opacity: 0.85; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.65); backdrop-filter: blur(2px);
  display: none; z-index: 100; overflow-y: auto;
  padding: 40px 16px;
  animation: fadein 0.18s ease;
}
.modal-overlay.open { display: flex; align-items: flex-start; justify-content: center; }
@keyframes fadein { from { opacity: 0; } to { opacity: 1; } }
.modal {
  background: var(--bg-card); border-radius: 12px;
  max-width: 760px; width: 100%; padding: 32px 36px 28px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.35);
  position: relative; animation: slidein 0.22s ease;
}
@keyframes slidein { from { transform: translateY(-12px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.modal-close {
  position: absolute; top: 14px; right: 14px;
  width: 32px; height: 32px; border-radius: 6px;
  background: transparent; border: none; cursor: pointer;
  color: var(--text-muted); font-size: 20px; line-height: 1;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.15s, color 0.15s;
}
.modal-close:hover { background: var(--bg-row); color: var(--text); }
.modal h2 { margin: 0 0 6px; font-size: 22px; letter-spacing: -0.01em; }
.modal .modal-sub { color: var(--text-muted); font-size: 13px; margin: 0 0 24px; }
.modal h3 { font-size: 13px; margin: 24px 0 10px; color: var(--text); font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.05em; }
.modal h3:first-of-type { margin-top: 8px; }
.modal table { width: 100%; border-collapse: collapse; margin: 0 0 8px; font-size: 13px; }
.modal table th { text-align: left; padding: 8px 12px; border-bottom: 2px solid var(--border);
                  color: var(--text-muted); font-weight: 600; font-size: 11px;
                  text-transform: uppercase; letter-spacing: 0.04em; }
.modal table td { padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: top;
                  color: var(--text-secondary); line-height: 1.5; }
.modal table td:first-child { font-weight: 600; color: var(--text); white-space: nowrap; }
.modal table tr:last-child td { border-bottom: none; }
.modal .note { background: #fef9e7; border-left: 3px solid var(--accent);
               padding: 10px 14px; margin: 18px 0 4px; border-radius: 4px;
               font-size: 12px; line-height: 1.55; color: var(--text-secondary); }
.minigrid-label { font-size: 11px; font-weight: 600; color: var(--text-muted);
                  text-transform: uppercase; letter-spacing: 0.04em; margin: 0 0 12px; }
.mini-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
             gap: 12px; margin-bottom: 36px; }
.mini-card { display: flex; flex-direction: column; justify-content: space-between;
             background: var(--bg-card); border: 1px solid var(--border);
             border-radius: 10px; padding: 14px 16px; text-decoration: none;
             color: var(--text); min-height: 132px;
             transition: transform 0.18s, box-shadow 0.18s, border-color 0.18s; }
.mini-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(15,23,42,0.08);
                   border-color: var(--primary); }
.mini-id { font-size: 10px; color: var(--text-muted); text-transform: uppercase;
           letter-spacing: 0.05em; margin-bottom: 6px; font-weight: 600; }
.mini-title { font-size: 13px; font-weight: 600; line-height: 1.35;
              margin-bottom: 10px; color: var(--text); }
.mini-meta { display: flex; justify-content: space-between; align-items: center;
             gap: 6px; flex-wrap: wrap; }
.mini-sv { font-size: 11px; color: var(--text-muted); font-variant-numeric: tabular-nums;
           font-weight: 600; }
.summary-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px;
               margin: 24px 0 32px; }
.summary-cell { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px;
                padding: 12px 16px; }
.summary-cell .label { font-size: 11px; font-weight: 600; color: var(--text-muted);
                       text-transform: uppercase; letter-spacing: 0.04em; }
.summary-cell .value { font-size: 22px; font-weight: 700; margin-top: 4px;
                       font-variant-numeric: tabular-nums; color: var(--text); }
.card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px;
        padding: 24px 28px; margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(15,23,42,0.04); transition: box-shadow 0.18s, transform 0.18s; }
.card:hover { box-shadow: 0 4px 16px rgba(15,23,42,0.08); transform: translateY(-1px); }
.section-label { font-size: 11px; font-weight: 600; color: var(--text-muted);
                 text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 4px; }
.section-value { font-size: 13px; color: var(--text); margin: 0 0 16px; line-height: 1.6; }
.section-value.struct { margin-bottom: 4px; }
.cluster-title { font-size: 18px; font-weight: 600; margin: 0 0 6px; color: var(--text); letter-spacing: -0.005em; }
.cluster-id { font-size: 11px; color: var(--text-muted); font-weight: 500; letter-spacing: 0.04em;
              text-transform: uppercase; }
.brief-actions { display: flex; gap: 10px; margin: 12px 0 0; flex-wrap: wrap; }
.action-link { display: inline-flex; align-items: center; gap: 6px;
               font-size: 12px; font-weight: 500; padding: 6px 12px;
               background: var(--bg-row); color: var(--text-secondary);
               border: 1px solid var(--border); border-radius: 6px;
               text-decoration: none;
               transition: background 0.15s, border-color 0.15s, color 0.15s; }
.action-link:hover { background: var(--bg-card); color: var(--primary-dark);
                     border-color: var(--primary); }
.action-link::before { font-weight: 700; font-size: 13px; }
.action-link.download::before { content: "↓"; }
.action-link.map::before { content: "→"; }
.badge { display: inline-block; font-size: 11px; padding: 3px 9px; border-radius: 4px;
         font-weight: 600; margin-right: 4px; margin-bottom: 4px; letter-spacing: 0.01em; }
.badge-info { background: var(--badge-info-bg); color: var(--badge-info-fg); }
.badge-warn { background: var(--badge-warn-bg); color: var(--badge-warn-fg); }
.badge-ok { background: var(--badge-ok-bg); color: var(--badge-ok-fg); }
.divider { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
.kw-row { display: flex; justify-content: space-between; font-size: 12px; padding: 6px 0;
          border-bottom: 1px solid var(--border); color: var(--text-secondary); }
.kw-row:last-child { border-bottom: none; }
.kw-name { color: var(--text); font-weight: 500; }
.kw-stats { color: var(--text-muted); font-variant-numeric: tabular-nums; }
.cta-block { background: var(--bg-row); border-left: 3px solid var(--primary); padding: 12px 16px;
             border-radius: 4px; }
.gap-block { background: #fef9e7; border-left: 3px solid var(--accent); padding: 12px 16px;
             border-radius: 4px; font-size: 12px; line-height: 1.55; color: var(--text-secondary); }
.gap-block ul { margin: 4px 0 0; padding-left: 20px; }
.gap-block li { margin-bottom: 4px; }
.toc { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px;
       padding: 16px 20px; margin-bottom: 28px; }
.toc h3 { margin: 0 0 8px; font-size: 13px; color: var(--text-muted);
          text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }
.toc ol { margin: 0; padding-left: 18px; font-size: 13px; }
.toc li { padding: 3px 0; }
.toc a { color: var(--primary-dark); text-decoration: none; }
.toc a:hover { color: var(--accent); }
@media (max-width: 720px) {
  body { padding: 20px 12px; }
  .card { padding: 18px 20px; }
}
"""


def _badge(label: str, kind: str) -> str:
    return f'<span class="badge badge-{kind}">{htmllib.escape(label)}</span>'


def _safe_label(value, display_id: int) -> str:
    """Return a string label, falling back when the cell is missing/NaN/empty.

    pandas reads empty CSV cells as float NaN, and `NaN or fallback`
    evaluates to NaN (NaN is truthy), so the bare `or` pattern leaks NaN
    into htmllib.escape and crashes. This helper coerces both NaN and
    empty strings to the generic "Cluster N" fallback.
    """
    if isinstance(value, str) and value.strip():
        return value
    return f"Cluster {display_id}"


def _render_card(profile_row: pd.Series, top_kw: pd.DataFrame, md: str,
                 brief_prefix: str = "", map_prefix: str = "../clustering/") -> str:
    """Build one cluster card."""
    cid = int(profile_row["cluster_id"])
    display_id = cid + 1
    label = _safe_label(profile_row["label_de"], display_id)
    n_kw = int(profile_row["n_keywords"])
    total_sv = int(profile_row["total_sv"])
    median_kd = int(profile_row["median_kd"])
    pct_comm = int(profile_row["pct_commercial"])

    # Intent badge: derive from pct_commercial
    if pct_comm >= 70:
        intent_label, intent_kind = "commercial", "ok"
    elif pct_comm <= 20:
        intent_label, intent_kind = "informational", "warn"
    else:
        intent_label, intent_kind = "mixed", "info"

    # Optional override from the brief metadata if present
    intent_meta = _meta(md, "Suchintention")
    if intent_meta:
        intent_kind = _intent_class(intent_meta)
        # Pull just the first word as the badge label
        first = re.split(r"[,\s]", intent_meta.strip(), 1)[0]
        if first.lower() in {"commercial", "informational", "mixed"}:
            intent_label = first.lower()

    # Title from the brief or fall back to the cluster label
    title_match = re.match(r"#\s+(.+)", md.strip())
    title = title_match.group(1).strip() if title_match else label

    # Keyword rows
    kw_rows = []
    for _, k in top_kw.iterrows():
        kw_rows.append(
            f'<div class="kw-row">'
            f'<span class="kw-name">{htmllib.escape(k["keyword"])}</span>'
            f'<span class="kw-stats">{int(k["search_volume"]):,}'.replace(",", ".") + " · "
            f'KD {int(k["kd"])} · €{float(k["cpc_eur"]):.2f}</span></div>'
        )
    kw_html = "\n".join(kw_rows)

    # Brief sections
    suchintention = _meta(md, "Suchintention") or intent_meta or ""
    zielgruppe = _section(md, "Zielgruppe")
    schmerz = _section(md, "Schmerzpunkt")
    ziel = _section(md, "Ziel des Artikels")
    h1, h2_list = _outline_h2(md)
    annotations = _benchmark_annotations(md)
    wortanzahl = _meta(md, "Empfohlene Wortanzahl")
    cta = _section(md, "Call to Action")

    # Structure block: H1 + the H2s
    struct_lines = []
    if h1:
        struct_lines.append(f'<p class="section-value struct"><b>H1:</b> {htmllib.escape(h1)}</p>')
    for h in h2_list[:7]:
        struct_lines.append(f'<p class="section-value struct"><b>H2:</b> {htmllib.escape(h)}</p>')
    structure_html = "\n".join(struct_lines) if struct_lines else "<p class='section-value'>—</p>"

    # Inhaltliche Lücken: derived from the benchmark URL annotations
    if annotations:
        gap_items = "".join(
            f"<li>{htmllib.escape(a)}</li>" for a in annotations
        )
        gap_html = (f'<div class="gap-block"><b>Was die Top-Wettbewerber zeigen, was Lücken sind:</b>'
                    f'<ul>{gap_items}</ul></div>')
    elif schmerz:
        gap_html = f'<div class="gap-block">{htmllib.escape(schmerz)}</div>'
    else:
        gap_html = '<div class="gap-block"><i>Keine SERP-Analyse hinterlegt.</i></div>'

    # Volume formatted
    sv_fmt = f"{total_sv:,}".replace(",", ".")

    brief_filename = f"{brief_prefix}cluster_{display_id:02d}.md"
    map_link = f"{map_prefix}cluster_map.html#cluster-{display_id}"

    return f"""
<section class="card" id="cluster-{display_id}">
  <p class="cluster-id">Cluster {display_id}</p>
  <h2 class="cluster-title">{htmllib.escape(title)}</h2>
  <div style="margin: 8px 0 0;">
    {_badge(intent_label, intent_kind)}
    {_badge(f"Volumen: {sv_fmt}/Mo", "info")}
    {_badge(f"Difficulty: {median_kd}", "info")}
    {_badge(f"{n_kw} Keywords", "info")}
    {_badge(f"{pct_comm}% kommerziell", "info" if pct_comm < 70 else "ok")}
  </div>
  <div class="brief-actions">
    <a class="action-link download" href="{brief_filename}" download>Markdown herunterladen</a>
    <a class="action-link map" href="{map_link}" target="_blank" rel="noopener">Im Cluster-Map anzeigen</a>
  </div>

  <hr class="divider">

  <p class="section-label">Top Keywords im Cluster</p>
  <div style="margin-bottom: 16px;">{kw_html}</div>

  <p class="section-label">Suchintention</p>
  <p class="section-value">{htmllib.escape(suchintention) or "—"}</p>

  <p class="section-label">Zielgruppe</p>
  <p class="section-value">{htmllib.escape(zielgruppe) or "—"}</p>

  {f'<p class="section-label">Schmerzpunkt</p><p class="section-value">{htmllib.escape(schmerz)}</p>' if schmerz else ''}

  {f'<p class="section-label">Ziel des Artikels</p><p class="section-value">{htmllib.escape(ziel)}</p>' if ziel else ''}

  <p class="section-label">Empfohlene Seitenstruktur</p>
  {structure_html}

  <hr class="divider">

  <p class="section-label">Inhaltliche Lücken (Top-3-SERP Analyse)</p>
  {gap_html}

  <p class="section-label" style="margin-top: 16px;">Empfohlene Länge</p>
  <p class="section-value">{htmllib.escape(wortanzahl) or "—"}</p>

  <p class="section-label">Call to Action</p>
  <div class="cta-block">{htmllib.escape(cta) or "—"}</div>
</section>
""".strip()


def _render_summary(prof: pd.DataFrame) -> str:
    real = prof[prof["cluster_id"] != -1]
    n_clusters = len(real)
    total_sv = int(real["total_sv"].sum())
    total_kw = int(real["n_keywords"].sum())
    avg_kd = round(float(real["mean_kd"].mean()), 1) if len(real) else 0
    return f"""
<div class="summary-row">
  <div class="summary-cell"><div class="label">Cluster</div><div class="value">{n_clusters}</div></div>
  <div class="summary-cell"><div class="label">Keywords</div><div class="value">{total_kw}</div></div>
  <div class="summary-cell"><div class="label">SV / Monat</div><div class="value">{total_sv:,}</div></div>
  <div class="summary-cell"><div class="label">Mittlere KD</div><div class="value">{avg_kd}</div></div>
</div>
""".replace(",", ".").strip()


def _render_minicards(prof: pd.DataFrame, titles: dict[int, str]) -> str:
    """Mini cluster cards at the top. Click a card to jump to the full brief below."""
    real = prof[prof["cluster_id"] != -1].sort_values("total_sv", ascending=False)
    cards = []
    for _, r in real.iterrows():
        cid = int(r["cluster_id"])
        display_id = cid + 1
        title = titles.get(cid, _safe_label(r["label_de"], display_id))
        sv = int(r["total_sv"])
        pct_comm = int(r["pct_commercial"])

        # Same intent logic as the full card
        if pct_comm >= 70:
            intent_label, intent_kind = "commercial", "ok"
        elif pct_comm <= 20:
            intent_label, intent_kind = "informational", "warn"
        else:
            intent_label, intent_kind = "mixed", "info"

        sv_fmt = f"{sv:,}".replace(",", ".")
        cards.append(
            f'<a href="#cluster-{display_id}" class="mini-card">'
            f'<div>'
            f'<div class="mini-id">Cluster {display_id}</div>'
            f'<div class="mini-title">{htmllib.escape(title)}</div>'
            f'</div>'
            f'<div class="mini-meta">'
            f'{_badge(intent_label, intent_kind)}'
            f'<span class="mini-sv">{sv_fmt}/Mo</span>'
            f'</div>'
            f'</a>'
        )
    return (
        '<p class="minigrid-label">Cluster im Überblick · Klick öffnet den Brief</p>'
        f'<div class="mini-grid">{"".join(cards)}</div>'
    )


# ---------------------------------------------------------------------------
# Public page builder (used by src.report for the combined dashboard)
# ---------------------------------------------------------------------------


def build_page(profiles: pd.DataFrame, labeled: pd.DataFrame,
               brief_prefix: str = "", extra_section: str = "",
               map_prefix: str = "../clustering/",
               briefings_dir: Path | None = None,
               back_links: list[tuple[str, str]] | None = None) -> str:
    """Assemble the full dashboard HTML and return it as a string.

    brief_prefix: prepended to brief download links (e.g. "../briefings/" when
                  the page is served from a sibling directory).
    extra_section: optional HTML block inserted between the mini-grid and the
                   cluster cards (used by src.report to inject chart PNGs).
    back_links: optional list of (label, href) rendered as small back-buttons
                above the header (e.g. "Zurück zur Übersicht").
    """
    real = profiles[profiles["cluster_id"] != -1].sort_values("total_sv", ascending=False)
    briefs_root = briefings_dir if briefings_dir is not None else BRIEFINGS
    cards = []
    titles: dict[int, str] = {}
    for _, row in real.iterrows():
        cid = int(row["cluster_id"])
        display_id = cid + 1
        md_path = briefs_root / f"cluster_{display_id:02d}.md"
        if not md_path.exists():
            logger.info("WARN: brief missing for cluster %d, skipping", cid)
            continue
        md = md_path.read_text(encoding="utf-8")
        title_match = re.match(r"#\s+(.+)", md.strip())
        if title_match:
            titles[cid] = title_match.group(1).strip()
        top_kw = labeled.loc[labeled["hdb"] == cid].sort_values(
            "search_volume", ascending=False).head(6)
        cards.append(_render_card(row, top_kw, md, brief_prefix=brief_prefix,
                                  map_prefix=map_prefix))

    summary = _render_summary(profiles)
    minicards = _render_minicards(profiles, titles)
    cards_html = "\n".join(cards)

    back_html = ""
    if back_links:
        items = "".join(
            f'<a class="back-link" href="{href}">← {label}</a>'
            for label, href in back_links
        )
        back_html = f'<nav class="back-nav">{items}</nav>'

    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cluster Briefs · zvoove SEO Pipeline</title>
<style>{_PAGE_CSS}
.back-nav{{display:flex;gap:14px;margin:0 0 18px;flex-wrap:wrap}}
.back-link{{font-size:13px;color:#0d9488;text-decoration:none;font-weight:500}}
.back-link:hover{{text-decoration:underline}}
</style>
</head><body><div class="wrap">
{back_html}
<header>
  <div class="header-text">
    <h1>Cluster Briefs</h1>
    <p>Pro Cluster ein Content Brief: Top-Keywords, Persona, Seitenstruktur, SERP-Lücken, CTA.
    Sortiert nach Suchvolumen pro Monat.</p>
  </div>
  <div class="header-actions">
    <a class="map-cta" href="{map_prefix}cluster_map.html">Cluster Karte öffnen</a>
    <button type="button" class="glossar-btn" onclick="openGlossar()">Glossar: was heißen die Zahlen?</button>
  </div>
</header>

<!-- Glossar Modal -->
<div class="modal-overlay" id="glossar-modal" onclick="if(event.target===this)closeGlossar()">
  <div class="modal" role="dialog" aria-labelledby="glossar-title">
    <button class="modal-close" onclick="closeGlossar()" aria-label="Schließen">×</button>
    <h2 id="glossar-title">Glossar</h2>
    <p class="modal-sub">Was die Kennzahlen im Dashboard bedeuten, in einfachem Deutsch.</p>

    <h3>KPI-Box ganz oben</h3>
    <table>
      <thead><tr><th>Feld</th><th>Bedeutung</th></tr></thead>
      <tbody>
        <tr><td>Cluster</td><td>Anzahl der thematischen Gruppen, in die HDBSCAN die Keywords sortiert hat</td></tr>
        <tr><td>Keywords</td><td>Summe aller Keywords über alle Cluster</td></tr>
        <tr><td>SV / Monat</td><td>Geschätztes Suchvolumen pro Monat: wie oft alle Keywords zusammen monatlich auf Google in Deutschland gesucht werden</td></tr>
        <tr><td>Mittlere KD</td><td>Durchschnittliche Keyword Difficulty über alle Keywords. Skala 0 bis 100</td></tr>
      </tbody>
    </table>

    <h3>Pro Cluster</h3>
    <table>
      <thead><tr><th>Feld</th><th>Bedeutung</th></tr></thead>
      <tbody>
        <tr><td>Volumen</td><td>Suchvolumen pro Monat über alle Keywords im Cluster zusammen</td></tr>
        <tr><td>Difficulty</td><td>Median Keyword Difficulty: wie schwer es im Schnitt ist, in den Top 10 von Google zu landen</td></tr>
        <tr><td>Keywords</td><td>Anzahl der Keywords in diesem Cluster</td></tr>
        <tr><td>% kommerziell</td><td>Anteil der Keywords, deren Suchintention "commercial" ist (Nutzer will kaufen oder vergleichen, nicht nur Wissen sammeln)</td></tr>
      </tbody>
    </table>

    <h3>Intent-Badges</h3>
    <table>
      <thead><tr><th>Badge</th><th>Bedeutung</th></tr></thead>
      <tbody>
        <tr><td>commercial</td><td>Cluster mehrheitlich kaufnah, mindestens 70 Prozent kommerziell. Bottom-of-Funnel</td></tr>
        <tr><td>informational</td><td>Cluster mehrheitlich Wissens-Suche, maximal 20 Prozent kommerziell. Top-of-Funnel</td></tr>
        <tr><td>mixed</td><td>Mischung, zwischen 20 und 70 Prozent kommerziell. Mid-Funnel</td></tr>
      </tbody>
    </table>

    <h3>Pro Keyword (in der Tabelle)</h3>
    <table>
      <thead><tr><th>Wert</th><th>Bedeutung</th></tr></thead>
      <tbody>
        <tr><td>SV</td><td>Suchvolumen: geschätzte monatliche Suchen für genau dieses Keyword</td></tr>
        <tr><td>KD</td><td>Keyword Difficulty 0 bis 100. 0-30 leicht, 30-60 mittel, 60-100 schwer</td></tr>
        <tr><td>CPC</td><td>Cost Per Click in Euro: was Werbetreibende auf Google Ads pro Klick zahlen. Hoch heißt kommerziell wertvoll</td></tr>
      </tbody>
    </table>

    <h3>Suchvolumen-Skala</h3>
    <table>
      <thead><tr><th>Bereich</th><th>Was es heißt</th></tr></thead>
      <tbody>
        <tr><td>unter 100</td><td>Nische, wenig Traffic, oft hoch konvertierend</td></tr>
        <tr><td>100 bis 1.000</td><td>Sweet-Spot, oft Long-Tail mit klarer Intention</td></tr>
        <tr><td>1.000 bis 5.000</td><td>Starkes Volumen, oft Head-Terms</td></tr>
        <tr><td>über 5.000</td><td>Top-Volumen, oft generisch und stark umkämpft</td></tr>
      </tbody>
    </table>

    <h3>KD-Skala</h3>
    <table>
      <thead><tr><th>Bereich</th><th>Was es heißt</th></tr></thead>
      <tbody>
        <tr><td>0 bis 30</td><td>Leicht, mit gutem Content rankt man oft schnell auf Seite 1</td></tr>
        <tr><td>30 bis 60</td><td>Mittel, braucht solide Optimierung und Backlinks</td></tr>
        <tr><td>60 bis 80</td><td>Schwer, etablierte Wettbewerber, lange Aufbauzeit</td></tr>
        <tr><td>80 bis 100</td><td>Brutal, oft nur große Brands oder Nachrichten-Sites ranken</td></tr>
      </tbody>
    </table>

    <div class="note">
      <b>Wichtig:</b> Die Werte sind Schätzungen aus einer deterministischen Heuristik (SHA256 Hash des Keywords als Seed), nicht echte DataForSEO Daten. Spalte <code>data_source</code> in den CSV-Dateien markiert das. In Produktion stehen hier echte Werte, die Größenordnungen sind aber realistisch genug, um die Cluster-Strategie zu bewerten.
    </div>
  </div>
</div>

<script>
function openGlossar() {{ document.getElementById('glossar-modal').classList.add('open'); document.body.style.overflow = 'hidden'; }}
function closeGlossar() {{ document.getElementById('glossar-modal').classList.remove('open'); document.body.style.overflow = ''; }}
document.addEventListener('keydown', function(e) {{ if (e.key === 'Escape') closeGlossar(); }});
</script>

{summary}

{minicards}

{extra_section}

{cards_html}

</div></body></html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run() -> None:
    if not PROFILES_CSV.exists():
        raise SystemExit(f"missing {PROFILES_CSV}. Run `python -m src.cluster --step profile` first.")
    profiles = pd.read_csv(PROFILES_CSV)
    labeled = pd.read_csv(LABELED_CSV)
    page = build_page(profiles, labeled)
    out = BRIEFINGS / "index.html"
    out.write_text(page, encoding="utf-8")
    size_kb = out.stat().st_size / 1024
    logger.info("wrote %s (%.1f KB)", out.relative_to(ROOT), size_kb)


def main() -> None:
    setup_logging()
    argparse.ArgumentParser(description=__doc__.split("\n\n")[0]).parse_args()
    run()


if __name__ == "__main__":
    main()
