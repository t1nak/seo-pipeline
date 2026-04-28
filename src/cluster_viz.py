"""Interactive bilingual Plotly cluster map.

Produces a self-contained HTML file that renders:

  * a 2D UMAP scatter plot, one trace per cluster, plus a "noise" trace
    that is hidden by default
  * a sidebar table that shows the keywords of any cluster the user clicks
  * a language switcher (English / German)
  * a bubble-size selector (search volume, priority, CPC, ease, uniform)

The Plotly figure is generated in Python, then embedded into a small HTML
shell with vanilla JS for the click interactions and language toggle.
Single external dependency: plotly.js loaded from the CDN.

Usage from cluster.py:

    html = build_cluster_map_html(df, red2, labels_en, labels_de)
    Path("cluster_map.html").write_text(html)
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _rescale(s: np.ndarray, lo: float = 8.0, hi: float = 40.0) -> np.ndarray:
    s = np.asarray(s, dtype=float)
    if s.max() == s.min():
        return np.full_like(s, (lo + hi) / 2)
    return lo + (s - s.min()) / (s.max() - s.min()) * (hi - lo)


def _sqrt_size(arr) -> np.ndarray:
    return 6 + np.sqrt(np.asarray(arr, dtype=float)) * 0.5


def _i18n(n_total: int, n_clusters: int, n_noise: int) -> dict:
    return {
        "en": {
            "title": "<b>HDBSCAN keyword clusters: zvoove</b>",
            "subtitle": (f"<sub>{n_total} keywords, {n_clusters} clusters, "
                         f"{n_noise} outliers. <b>Distance is similarity.</b> "
                         f"Click a dot or a legend item to inspect.</sub>"),
            "legendTitle": ('<b>Cluster</b><br><span style="font-size:10px;color:#666">'
                            "click to inspect, double-click to isolate</span>"),
            "bubbleSize": "<b>Bubble size</b>",
            "sizeOptions": ["Search Volume", "Priority", "CPC (€)", "Ease", "Uniform"],
            "viewButtons": ["All", "Hide noise"],
            "footer": ('<span style="color:#666;font-size:11px">Map produced with '
                       "<b>UMAP</b>. Axis numbers have no meaning. What matters: "
                       "two dots close together mean similar keywords.</span>"),
            "defs": ('<span style="font-size:10px;color:#666;line-height:1.55">'
                     '<b style="color:#333">What the metrics mean</b><br>'
                     "<b>Search Volume (SV)</b>: estimated avg monthly Google searches in DE<br>"
                     "<b>KD (Keyword Difficulty)</b>: 0-100 score, how hard to rank #1. "
                     "0 = trivial, 50 = medium, 80+ = brutal<br>"
                     "<b>CPC</b>: Google Ads cost per click in € (DE)<br>"
                     "<b>Priority</b>: SV ÷ KD<br>"
                     "<b>Ease</b>: 100 − KD (higher = easier)<br>"
                     '<i style="color:#999">All values estimated, not live</i></span>'),
            "noiseHoverPrefix": "<i>Outlier, not part of any dense cluster</i><br>",
            "clusterHoverPrefix": "HDBSCAN cluster",
            "hoverIntent": "Intent",
            "hoverPriority": "Priority",
            "panelTitle": "Cluster keywords",
            "placeholder": ("<b>Click any dot or cluster in the legend</b> to inspect "
                            "its keywords here.<br>Sorted by search volume."),
            "kwsCount": "keywords",
            "sumTotalSv": "Total SV",
            "sumMeanKd": "Mean KD",
            "sumMeanCpc": "Mean CPC",
            "sumComm": "Commercial",
            "tblHeaders": ["Keyword", "SV", "KD", "CPC", "Prio", "Int"],
            "pillC": "C", "pillI": "I",
            "intentLegend": "C = commercial, I = informational",
            "permo": "/mo",
            "outlierLabel": "Outliers",
        },
        "de": {
            "title": "<b>HDBSCAN Keyword-Cluster: zvoove</b>",
            "subtitle": (f"<sub>{n_total} Keywords, {n_clusters} Cluster, "
                         f"{n_noise} Ausreißer. <b>Abstand bedeutet Ähnlichkeit.</b> "
                         f"Klick auf einen Punkt oder Cluster für Details.</sub>"),
            "legendTitle": ('<b>Cluster</b><br><span style="font-size:10px;color:#666">'
                            "Klick zum Anzeigen, Doppelklick zum Isolieren</span>"),
            "bubbleSize": "<b>Bubble Größe</b>",
            "sizeOptions": ["Suchvolumen", "Priorität", "CPC (€)", "Einfachheit", "Einheitlich"],
            "viewButtons": ["Alle", "Ausreißer ausblenden"],
            "footer": ('<span style="color:#666;font-size:11px">Karte erstellt mit '
                       "<b>UMAP</b>. Achsenzahlen haben keine Bedeutung. Wichtig: "
                       "zwei Punkte nahe beieinander bedeuten ähnliche Keywords.</span>"),
            "defs": ('<span style="font-size:10px;color:#666;line-height:1.55">'
                     '<b style="color:#333">Was die Metriken bedeuten</b><br>'
                     "<b>Suchvolumen (SV)</b>: geschätzte durchschnittl. monatl. Google-Suchen in DE<br>"
                     "<b>KD (Keyword-Schwierigkeit)</b>: 0-100, wie schwer #1-Ranking ist. "
                     "0 = trivial, 50 = mittel, 80+ = brutal<br>"
                     "<b>CPC</b>: Google Ads Kosten pro Klick in € (DE)<br>"
                     "<b>Priorität</b>: SV ÷ KD<br>"
                     "<b>Einfachheit</b>: 100 − KD (höher = einfacher)<br>"
                     '<i style="color:#999">Alle Werte geschätzt, nicht live</i></span>'),
            "noiseHoverPrefix": "<i>Ausreißer, gehört zu keinem dichten Cluster</i><br>",
            "clusterHoverPrefix": "HDBSCAN-Cluster",
            "hoverIntent": "Intent",
            "hoverPriority": "Priorität",
            "panelTitle": "Cluster-Keywords",
            "placeholder": ("<b>Klick auf einen Punkt oder Cluster</b>, um seine Keywords "
                            "hier zu sehen.<br>Sortiert nach Suchvolumen."),
            "kwsCount": "Keywords",
            "sumTotalSv": "Gesamt-SV",
            "sumMeanKd": "Ø KD",
            "sumMeanCpc": "Ø CPC",
            "sumComm": "Kommerziell",
            "tblHeaders": ["Keyword", "SV", "KD", "CPC", "Prio", "Int"],
            "pillC": "K", "pillI": "I",
            "intentLegend": "K = kommerziell, I = informativ",
            "permo": "/Mo",
            "outlierLabel": "Ausreißer",
        },
    }


# Inline HTML/JS template. Placeholders __FIG_JSON__, __KW_DATA__, __I18N__,
# __PAYLOADS__ are substituted at render time.
_HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>HDBSCAN keyword clusters: zvoove</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
*{box-sizing:border-box}body{margin:0;padding:16px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f4f4f6;color:#222}
.toolbar{max-width:1620px;margin:0 auto 12px;display:flex;justify-content:flex-end;gap:8px}
.lang-switch{display:inline-flex;background:white;border:1px solid #d0d0d0;border-radius:8px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,0.04)}
.lang-switch button{background:white;border:none;padding:6px 14px;cursor:pointer;font-size:13px;font-weight:600;color:#555;font-family:inherit}
.lang-switch button:not(:last-child){border-right:1px solid #e0e0e0}
.lang-switch button.active{background:#2563eb;color:white}
.lang-switch button:not(.active):hover{background:#f0f0f0}
.wrap{display:flex;gap:16px;align-items:flex-start;max-width:1620px;margin:0 auto}
.chart-card,.table-card{background:white;border:1px solid #e0e0e0;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.04);padding:8px}
.chart-card{flex:0 0 auto}
.table-card{flex:1 1 480px;min-width:440px;max-width:540px;padding:18px;max-height:880px;overflow-y:auto}
.table-card h3{margin:0 0 4px;font-size:15px;color:#222}
.table-card .placeholder{color:#888;font-size:13px;line-height:1.55;padding:24px 8px;text-align:center;border:2px dashed #e0e0e0;border-radius:6px;margin-top:14px}
.cluster-header{display:flex;align-items:center;gap:10px;padding:8px 0 12px;border-bottom:1px solid #eee;margin-bottom:10px}
.cluster-header .swatch{width:18px;height:18px;border-radius:50%;flex:0 0 18px;border:1px solid #ccc}
.cluster-header .name{font-weight:600;font-size:15px}
.cluster-header .id{font-size:11px;color:#888}
.summary{display:grid;grid-template-columns:repeat(2,1fr);gap:6px 14px;font-size:12px;color:#555;padding:8px 0 14px}
.summary b{color:#222}
table.kws{width:100%;border-collapse:collapse;font-size:12px}
table.kws th{text-align:left;font-weight:600;color:#666;padding:6px;border-bottom:2px solid #eee;position:sticky;top:0;background:white;font-size:11px;text-transform:uppercase;letter-spacing:0.04em}
table.kws td{padding:6px;border-bottom:1px solid #f3f3f3;vertical-align:top}
table.kws td.kw{color:#222;font-weight:500}
table.kws td.num{text-align:right;color:#444;font-variant-numeric:tabular-nums}
table.kws td.intent{text-align:center}
.pill{display:inline-block;padding:1px 6px;border-radius:10px;font-size:10px;font-weight:600}
.pill.c{background:#fde7d6;color:#a04400}.pill.i{background:#dceaf7;color:#1a4f7a}
table.kws tr.hl td{background:#fff7d6;font-weight:700;color:#111;box-shadow:inset 3px 0 0 #f59e0b}
table.kws tr.hl td.kw{color:#000}
.muted{color:#999;font-style:italic}
</style></head><body>
<div class="toolbar"><div class="lang-switch"><button id="lang-en" class="active">EN</button><button id="lang-de">DE</button></div></div>
<div class="wrap">
<div class="chart-card"><div id="chart"></div></div>
<div class="table-card">
<h3 id="panel-title">Cluster keywords</h3>
<div id="panel"><div class="placeholder"><b>Click any dot or cluster in the legend</b> to inspect its keywords here.<br>Sorted by search volume.</div></div>
</div></div>
<script>
const FIG = __FIG_JSON__;
const KW = __KW_DATA__;
const I18N = __I18N__;
const PAYLOADS = __PAYLOADS__;
let LANG='en', SELECTED_CID=null, HIGHLIGHT_KW=null;
Plotly.newPlot('chart', FIG.data, FIG.layout, {displaylogo:false, scrollZoom:true, responsive:false});
function escapeHTML(s){return String(s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function showCluster(cid, highlight){
 SELECTED_CID=cid; HIGHLIGHT_KW=highlight||null;
 const c=KW[String(cid)]; if(!c) return;
 const L=I18N[LANG]; const name=LANG==='de'?c.name_de:c.name_en;
 const idLabel=c.display_id!=null ? `${L.clusterHoverPrefix} ${c.display_id}` : L.outlierLabel;
 const rows=c.kws.map(k=>{
  const isHl=HIGHLIGHT_KW && k.keyword===HIGHLIGHT_KW;
  return `<tr class="${isHl?'hl':''}"><td class="kw">${escapeHTML(k.keyword)}</td>
   <td class="num">${k.sv.toLocaleString(LANG==='de'?'de-DE':'en-US')}</td>
   <td class="num">${k.kd}</td><td class="num">€${k.cpc.toFixed(2)}</td>
   <td class="num">${k.p}</td>
   <td class="intent"><span class="pill ${k.i==='commercial'?'c':'i'}">${k.i==='commercial'?L.pillC:L.pillI}</span></td></tr>`;
 }).join('');
 document.getElementById('panel').innerHTML=`
  <div class="cluster-header"><div class="swatch" style="background:${c.color}"></div>
   <div><div class="name">${escapeHTML(name)}</div><div class="id">${idLabel} · ${c.count} ${L.kwsCount}</div></div></div>
  <div class="summary">
   <div>${L.sumTotalSv}: <b>${c.total_sv.toLocaleString(LANG==='de'?'de-DE':'en-US')}${L.permo}</b></div>
   <div>${L.sumMeanKd}: <b>${c.mean_kd}</b></div>
   <div>${L.sumMeanCpc}: <b>€${c.mean_cpc.toFixed(2)}</b></div>
   <div>${L.sumComm}: <b>${c.pct_comm}%</b></div></div>
  <table class="kws"><thead><tr>${L.tblHeaders.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>
  <p class="muted" style="font-size:10px;text-align:center;margin-top:10px">${L.intentLegend}</p>`;
 if(HIGHLIGHT_KW){const r=document.querySelector('table.kws tr.hl'); if(r) r.scrollIntoView({behavior:'smooth',block:'center'});}
}
function showPlaceholder(){const L=I18N[LANG]; document.getElementById('panel').innerHTML=`<div class="placeholder">${L.placeholder}</div>`;}
function applyLanguage(lang){
 LANG=lang; const L=I18N[lang], P=PAYLOADS[lang];
 document.getElementById('lang-en').classList.toggle('active', lang==='en');
 document.getElementById('lang-de').classList.toggle('active', lang==='de');
 document.documentElement.lang=lang;
 document.getElementById('panel-title').textContent=L.panelTitle;
 if(SELECTED_CID===null) showPlaceholder(); else showCluster(SELECTED_CID, HIGHLIGHT_KW);
 const traceIdx=P.names.map((_,i)=>i);
 Plotly.restyle('chart', {'name':P.names, 'hovertemplate':P.hovertemplate}, traceIdx);
 for(let i=0;i<P.cdField6.length;i++){
  const cd=FIG.data[i].customdata.map((row,ri)=>{const r=row.slice();r[6]=P.cdField6[i][ri];return r;});
  Plotly.restyle('chart', {'customdata':[cd]}, [i]);
 }
 const newAnns=(FIG.layout.annotations||[]).map(a=>{
  if(a.name==='ann_bubblesize') return Object.assign({},a,{text:L.bubbleSize});
  if(a.name==='ann_footer') return Object.assign({},a,{text:L.footer});
  if(a.name==='ann_defs') return Object.assign({},a,{text:L.defs});
  return a;
 });
 const um=JSON.parse(JSON.stringify(FIG.layout.updatemenus));
 for(let i=0;i<L.sizeOptions.length;i++) um[0].buttons[i].label=L.sizeOptions[i];
 um[1].buttons[0].label=L.viewButtons[0]; um[1].buttons[1].label=L.viewButtons[1];
 Plotly.relayout('chart',{'title.text':L.title+'<br>'+L.subtitle,'legend.title.text':L.legendTitle,'annotations':newAnns,'updatemenus':um});
}
const chartDiv=document.getElementById('chart');
function cidFromTraceName(name){
 if(name==='Outliers'||name==='Ausreißer') return -1;
 const m=name.match(/^(\\d+):/); return m?parseInt(m[1])-1:null;
}
chartDiv.on('plotly_click', ev=>{if(!ev.points||!ev.points.length)return;const pt=ev.points[0];const cid=cidFromTraceName(pt.fullData.name);const kw=pt.customdata?pt.customdata[0]:null;if(cid!==null) showCluster(cid,kw);});
chartDiv.on('plotly_legendclick', ev=>{const cid=cidFromTraceName(ev.fullData[ev.curveNumber].name);if(cid!==null) showCluster(cid,null);return true;});
chartDiv.on('plotly_legenddoubleclick', ev=>{const cid=cidFromTraceName(ev.fullData[ev.curveNumber].name);if(cid!==null) showCluster(cid,null);return true;});
document.getElementById('lang-en').addEventListener('click',()=>applyLanguage('en'));
document.getElementById('lang-de').addEventListener('click',()=>applyLanguage('de'));
</script></body></html>"""


def _build_hover(intent_lbl: str, prio_lbl: str) -> str:
    return ("<b>%{customdata[0]}</b><br>%{customdata[6]}"
            f"{intent_lbl}: %{{customdata[1]}}<br>"
            "SV: %{customdata[2]:,} · KD: %{customdata[3]} · CPC: €%{customdata[4]:.2f}<br>"
            f"{prio_lbl}: %{{customdata[5]}}<extra></extra>")


def _customdata(sub: pd.DataFrame, header: str) -> np.ndarray:
    return np.stack([
        sub["keyword"], sub["estimated_intent"],
        sub["search_volume"], sub["kd"], sub["cpc_eur"], sub["priority_score"],
        np.array([header] * len(sub)),
    ], axis=-1)


def build_cluster_map_html(df: pd.DataFrame, red2: np.ndarray,
                           labels_en: dict[int, str],
                           labels_de: dict[int, str]) -> str:
    """Return the full self-contained HTML string for the cluster map."""
    df = df.copy()
    df["x"], df["y"] = red2[:, 0], red2[:, 1]
    clusters = sorted(int(c) for c in df["hdb"].unique() if c != -1)
    palette = px.colors.qualitative.Light24[:len(clusters)]
    color_map: dict[int, str] = {c: palette[i] for i, c in enumerate(clusters)}
    color_map[-1] = "#cccccc"

    n_total = len(df)
    n_noise = int((df["hdb"] == -1).sum())
    i18n = _i18n(n_total, len(clusters), n_noise)
    L = i18n["en"]

    # Bubble-size encodings, restyled by the dropdown
    size_metrics = {
        "sv": _sqrt_size(df["search_volume"]),
        "priority": _rescale(np.sqrt(df["priority_score"].clip(lower=0.1))),
        "cpc": _rescale(df["cpc_eur"]),
        "ease": _rescale(100 - df["kd"]),
        "uniform": np.full(len(df), 10.0),
    }
    default_size = size_metrics["sv"]

    fig = go.Figure()
    noise = df[df["hdb"] == -1]
    fig.add_trace(go.Scatter(
        x=noise["x"], y=noise["y"], mode="markers",
        marker=dict(size=default_size[df["hdb"] == -1], color="#cccccc",
                    opacity=0.45, line=dict(width=0)),
        name="Outliers", visible="legendonly",
        customdata=_customdata(noise, L["noiseHoverPrefix"]),
        hovertemplate=_build_hover(L["hoverIntent"], L["hoverPriority"]),
    ))
    for cid in clusters:
        sub_mask = df["hdb"] == cid
        sub = df[sub_mask]
        d = cid + 1
        header_en = f"<b>{L['clusterHoverPrefix']} {d}: {labels_en[cid]}</b><br>"
        fig.add_trace(go.Scatter(
            x=sub["x"], y=sub["y"], mode="markers",
            marker=dict(size=default_size[sub_mask.values], color=color_map[cid],
                        opacity=0.78, line=dict(width=0.7, color="white")),
            name=f"{d}: {labels_en[cid]}",
            customdata=_customdata(sub, header_en),
            hovertemplate=_build_hover(L["hoverIntent"], L["hoverPriority"]),
        ))
        cx, cy = sub["x"].mean(), sub["y"].mean()
        fig.add_annotation(x=cx, y=cy, text=f"<b>{d}</b>", showarrow=False,
                           bgcolor="white", bordercolor="black",
                           borderwidth=1, borderpad=2,
                           font=dict(size=11, color="black"))

    # Per-language payloads for the JS to swap between
    def make_payloads(lang: str) -> dict:
        L_ = i18n[lang]
        labs = labels_en if lang == "en" else labels_de
        names = [L_["outlierLabel"]]
        cd6 = [[L_["noiseHoverPrefix"]] * len(noise)]
        for cid in clusters:
            d = cid + 1
            names.append(f"{d}: {labs[cid]}")
            sub = df[df["hdb"] == cid]
            cd6.append([f"<b>{L_['clusterHoverPrefix']} {d}: {labs[cid]}</b><br>"] * len(sub))
        return {"names": names, "cdField6": cd6,
                "hovertemplate": _build_hover(L_["hoverIntent"], L_["hoverPriority"])}

    payloads = {"en": make_payloads("en"), "de": make_payloads("de")}

    # Bubble-size and view dropdown buttons
    size_buttons = []
    for key, label in zip(["sv", "priority", "cpc", "ease", "uniform"], L["sizeOptions"]):
        arr = size_metrics[key]
        new_sizes = [arr[df["hdb"] == -1]] + [arr[df["hdb"] == c] for c in clusters]
        size_buttons.append(dict(label=label, method="restyle",
                                 args=[{"marker.size": new_sizes}]))
    n_traces = 1 + len(clusters)
    view_buttons = [
        dict(label=L["viewButtons"][0], method="restyle",
             args=[{"visible": [True] * n_traces}]),
        dict(label=L["viewButtons"][1], method="restyle",
             args=[{"visible": ["legendonly"] + [True] * len(clusters)}]),
    ]

    fig.update_layout(
        title=dict(text=L["title"] + "<br>" + L["subtitle"], x=0.01, xanchor="left"),
        width=1100, height=820, plot_bgcolor="white",
        xaxis=dict(title="", gridcolor="#eee", zeroline=False, showticklabels=False),
        yaxis=dict(title="", gridcolor="#eee", zeroline=False, showticklabels=False),
        legend=dict(title=L["legendTitle"], bgcolor="rgba(255,255,255,0.95)",
                    bordercolor="#ccc", borderwidth=1, font=dict(size=13),
                    title_font=dict(size=12), itemsizing="constant",
                    yanchor="top", y=1.0, x=1.005, xanchor="left"),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="monospace"),
        margin=dict(l=60, r=440, t=80, b=80),
        updatemenus=[
            dict(buttons=size_buttons, direction="down", showactive=True,
                 x=1.005, xanchor="left", y=0.41, yanchor="top",
                 bgcolor="white", bordercolor="#ccc", borderwidth=1,
                 font=dict(size=11), pad=dict(t=3, b=3, l=6, r=6)),
            dict(buttons=view_buttons, direction="right", showactive=True,
                 type="buttons", x=1.27, xanchor="left", y=0.405, yanchor="top",
                 bgcolor="white", bordercolor="#ccc", borderwidth=1,
                 font=dict(size=11), pad=dict(t=3, b=3, l=6, r=6), active=1),
        ],
    )
    fig.add_annotation(x=1.005, y=0.45, xref="paper", yref="paper", xanchor="left",
                       text=L["bubbleSize"], showarrow=False,
                       font=dict(size=12, color="#333"), name="ann_bubblesize")
    fig.add_annotation(x=0.5, y=-0.06, xref="paper", yref="paper", xanchor="center",
                       text=L["footer"], showarrow=False, name="ann_footer")
    fig.add_annotation(x=1.005, y=0.32, xref="paper", yref="paper",
                       xanchor="left", yanchor="top",
                       text=L["defs"], showarrow=False, align="left",
                       bordercolor="#e0e0e0", borderwidth=1, bgcolor="#fafafa",
                       borderpad=8, name="ann_defs")

    # Per-cluster keyword data, surfaced in the JS sidebar table
    kw_data: dict[str, dict] = {}
    for cid in [-1, *clusters]:
        sub = df[df["hdb"] == cid].sort_values("search_volume", ascending=False)
        d = int(cid + 1) if cid >= 0 else None
        kw_data[str(cid)] = {
            "display_id": d,
            "name_en": labels_en[cid],
            "name_de": labels_de[cid],
            "color": color_map[cid],
            "count": int(len(sub)),
            "total_sv": int(sub["search_volume"].sum()),
            "mean_kd": round(float(sub["kd"].mean()), 1),
            "mean_cpc": round(float(sub["cpc_eur"].mean()), 2),
            "pct_comm": round(float((sub["estimated_intent"] == "commercial").mean() * 100), 0),
            "kws": (sub[["keyword", "search_volume", "kd", "cpc_eur",
                         "priority_score", "estimated_intent"]]
                    .rename(columns={"search_volume": "sv", "cpc_eur": "cpc",
                                     "priority_score": "p", "estimated_intent": "i"})
                    .to_dict(orient="records")),
        }

    return (_HTML_TEMPLATE
            .replace("__FIG_JSON__", fig.to_json())
            .replace("__KW_DATA__", json.dumps(kw_data, ensure_ascii=False))
            .replace("__I18N__", json.dumps(i18n, ensure_ascii=False))
            .replace("__PAYLOADS__", json.dumps(payloads, ensure_ascii=False)))
