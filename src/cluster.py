"""Cluster step of the SEO keyword pipeline.

Reads `data/keywords.csv` (the enriched keyword set from the discover/enrich
steps) and produces semantic clusters plus interpretable artifacts.

Pipeline:
    1. clean    drop dupes, coerce numeric columns, attach orig cluster names
    2. embed    sentence-transformers (multilingual MiniLM) -> embeddings.npy
    3. reduce   UMAP to 5D for clustering, 2D for visualisation
    4. sweep    HDBSCAN parameter grid (diagnostic, prints a table)
    5. cluster  final HDBSCAN with the chosen hyperparameters
    6. label    attach human-readable cluster names (DE + EN)
    7. profile  per-cluster stats CSV (size, SV, KD, CPC, intent mix)
    8. charts   six matplotlib PNGs for the case study report
    9. viz      interactive bilingual Plotly map (delegated to cluster_viz.py)

The hyperparameter choices (UMAP n_neighbors=15, HDBSCAN mcs=15 / ms=5 / eom)
are documented in docs/methodology.md, including the parameter sweep result
that justifies them.

CLI:
    python -m src.cluster --step all
    python -m src.cluster --step embed,reduce,cluster,label
    python -m src.cluster --step viz
"""
from __future__ import annotations

import argparse
import json
import re
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths and hyperparameters
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "output"
CLUSTERING = OUT / "clustering"

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

UMAP_N_NEIGHBORS = 15
UMAP_RANDOM_STATE = 42
UMAP_METRIC = "cosine"

HDBSCAN_MIN_CLUSTER_SIZE = 15
HDBSCAN_MIN_SAMPLES = 5
HDBSCAN_METHOD = "eom"
HDBSCAN_METRIC = "euclidean"

# Manual cluster labels, derived once from inspection of the recovered run.
# Keeping them stable means re-runs with random_state=42 produce the same
# IDs and the labels still apply. If keywords change materially, regenerate
# (see docs/decisions.md).
CLUSTER_LABELS_EN = {
    -1: "Noise / outliers",
    0: "Factoring fundamentals",
    1: "Industry & labour law catch-all",
    2: "Commercial Zeit/Software heads",
    3: "Recruiting & AI tooling",
    4: "Brand: zvoove product names",
    5: "Operational how-to (mixed)",
    6: "Mid-funnel HR ops",
    7: "Gebäudereinigung vertical",
    8: "Digitalisation in practice",
    9: "B2B SaaS category heads",
}

CLUSTER_LABELS_DE = {
    -1: "Rauschen / Ausreißer",
    0: "Factoring-Grundlagen",
    1: "Branche & Arbeitsrecht (Sammelbecken)",
    2: "Kommerzielle Zeit/Software-Heads",
    3: "Recruiting & KI-Tools",
    4: "Marke: zvoove Produktnamen",
    5: "Operative Anleitungen (gemischt)",
    6: "HR-Mid-Funnel",
    7: "Gebäudereinigung-Vertikale",
    8: "Digitalisierung praktisch",
    9: "B2B-SaaS Kategorie-Heads",
}

# Files written by each step. Keep a single source of truth so docs and code
# agree on what lives where.
F_CLEAN = CLUSTERING / "keywords_clean.csv"
F_EMB = CLUSTERING / "embeddings.npy"
F_UMAP_5D = CLUSTERING / "umap_5d.npy"
F_UMAP_2D = CLUSTERING / "umap_2d.npy"
F_LABELED = CLUSTERING / "keywords_labeled.csv"
F_PROFILES = CLUSTERING / "cluster_profiles.csv"
F_VIZ = CLUSTERING / "cluster_map.html"


# ---------------------------------------------------------------------------
# Step 1: clean
# ---------------------------------------------------------------------------


def step_clean(input_csv: Path = DATA / "keywords.csv",
               clusters_json: Path = OUT / "clusters.json") -> pd.DataFrame:
    """Load keywords, drop duplicates, coerce numerics, attach orig cluster names."""
    CLUSTERING.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv)
    print(f"[clean] loaded {len(df)} rows, {df.shape[1]} cols")
    print(f"[clean] dupes (keyword): {df.duplicated(subset=['keyword']).sum()}")

    for col in ("search_volume", "kd", "cpc_eur", "priority_score"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.drop_duplicates(subset=["keyword"]).reset_index(drop=True)
    df["keyword_clean"] = df["keyword"].str.lower().str.strip()

    if clusters_json.exists():
        names = {c["id"]: c["name"] for c in json.loads(clusters_json.read_text())["clusters"]}
        df["orig_cluster_name"] = df["category"].map(names)

    df.to_csv(F_CLEAN, index=False)
    print(f"[clean] wrote {F_CLEAN.relative_to(ROOT)} ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# Step 2: embed
# ---------------------------------------------------------------------------


def step_embed() -> np.ndarray:
    """Compute multilingual sentence embeddings for each keyword.

    The L6 English-only MiniLM was rejected because zvoove keywords are German.
    L12 multilingual handles German morphology well enough for clustering at
    this scale, runs locally without a GPU, and weighs ~120 MB.
    """
    from sentence_transformers import SentenceTransformer

    df = pd.read_csv(F_CLEAN)
    print(f"[embed] encoding {len(df)} keywords with {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)
    emb = model.encode(df["keyword"].tolist(), show_progress_bar=False,
                       normalize_embeddings=True)
    np.save(F_EMB, emb)
    print(f"[embed] wrote {F_EMB.relative_to(ROOT)}, shape={emb.shape}")
    return emb


# ---------------------------------------------------------------------------
# Step 3: reduce (UMAP)
# ---------------------------------------------------------------------------


def step_reduce() -> tuple[np.ndarray, np.ndarray]:
    """Reduce embeddings to 5D for clustering and 2D for visualisation.

    Two reductions because the optima differ: density-based clustering wants
    a few more dimensions to keep local structure (5D), the map needs exactly 2.
    """
    import umap

    emb = np.load(F_EMB)
    print(f"[reduce] UMAP {emb.shape[1]}D -> 5D (clustering) + 2D (viz)")
    red5 = umap.UMAP(n_neighbors=UMAP_N_NEIGHBORS, n_components=5,
                     metric=UMAP_METRIC, min_dist=0.0,
                     random_state=UMAP_RANDOM_STATE).fit_transform(emb)
    red2 = umap.UMAP(n_neighbors=UMAP_N_NEIGHBORS, n_components=2,
                     metric=UMAP_METRIC, min_dist=0.1,
                     random_state=UMAP_RANDOM_STATE).fit_transform(emb)
    np.save(F_UMAP_5D, red5)
    np.save(F_UMAP_2D, red2)
    print(f"[reduce] wrote {F_UMAP_5D.relative_to(ROOT)}, {F_UMAP_2D.relative_to(ROOT)}")
    return red5, red2


# ---------------------------------------------------------------------------
# Step 4: sweep (diagnostic)
# ---------------------------------------------------------------------------


def step_sweep() -> pd.DataFrame:
    """HDBSCAN hyperparameter sweep. Prints a table, returns it as a DataFrame.

    Diagnostic only. The chosen final params (mcs=15, ms=5, eom) were picked
    from this sweep on the recovered manual run. See docs/methodology.md.
    """
    import hdbscan
    from sklearn.metrics import silhouette_score

    red5 = np.load(F_UMAP_5D)
    rows = []
    print(f"{'mcs':>4} {'ms':>4} {'method':>6} {'n_clu':>6} {'noise':>6} "
          f"{'noise%':>7} {'sil':>7}")
    for mcs in (5, 8, 10, 12, 15, 20):
        for ms in (1, 5):
            for method in ("eom", "leaf"):
                cl = hdbscan.HDBSCAN(min_cluster_size=mcs, min_samples=ms,
                                     cluster_selection_method=method,
                                     metric=HDBSCAN_METRIC)
                labs = cl.fit_predict(red5)
                n_clu = len(set(labs)) - (1 if -1 in labs else 0)
                noise = int((labs == -1).sum())
                mask = labs != -1
                sil = (silhouette_score(red5[mask], labs[mask])
                       if (mask.sum() > 10 and n_clu > 1) else float("nan"))
                rows.append({"mcs": mcs, "ms": ms, "method": method,
                             "n_clusters": n_clu, "noise": noise,
                             "noise_pct": noise / len(labs), "silhouette": sil})
                print(f"{mcs:>4} {ms:>4} {method:>6} {n_clu:>6} {noise:>6} "
                      f"{noise / len(labs) * 100:>6.1f}% {sil:>7.3f}")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 5: cluster (final HDBSCAN + Ward comparison)
# ---------------------------------------------------------------------------


def step_cluster() -> pd.DataFrame:
    """Run the final HDBSCAN, plus a Ward hierarchical comparison for the writeup."""
    import hdbscan
    from scipy.cluster.hierarchy import fcluster, linkage
    from sklearn.metrics import (adjusted_rand_score,
                                 normalized_mutual_info_score, silhouette_score)

    red5 = np.load(F_UMAP_5D)
    df = pd.read_csv(F_CLEAN)

    print(f"[cluster] HDBSCAN mcs={HDBSCAN_MIN_CLUSTER_SIZE} "
          f"ms={HDBSCAN_MIN_SAMPLES} method={HDBSCAN_METHOD}")
    cl = hdbscan.HDBSCAN(min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE,
                         min_samples=HDBSCAN_MIN_SAMPLES,
                         cluster_selection_method=HDBSCAN_METHOD,
                         metric=HDBSCAN_METRIC)
    labs = cl.fit_predict(red5)
    df["hdb"] = labs
    n_clu = len(set(labs)) - (1 if -1 in labs else 0)
    noise = int((labs == -1).sum())
    print(f"[cluster] {n_clu} clusters, {noise} noise points "
          f"({noise / len(labs) * 100:.1f}%)")
    print(f"[cluster] sizes: {sorted(Counter(labs).items())}")

    print("[cluster] Ward hierarchical comparison (k=8,10,12)")
    Z = linkage(red5, method="ward")
    for k in (8, 10, 12):
        h = fcluster(Z, t=k, criterion="maxclust")
        sil = silhouette_score(red5, h)
        print(f"          k={k}: silhouette={sil:.3f}")
    df["hier10"] = fcluster(Z, t=10, criterion="maxclust")
    df["hier12"] = fcluster(Z, t=12, criterion="maxclust")

    mask = df["hdb"] != -1
    orig = df["category"].astype("category").cat.codes
    print("[cluster] agreement metrics (excluding HDBSCAN noise)")
    print(f"          HDB vs LLM original  ARI={adjusted_rand_score(orig[mask], df['hdb'][mask]):.3f}, "
          f"NMI={normalized_mutual_info_score(orig[mask], df['hdb'][mask]):.3f}")
    print(f"          Hier(10) vs LLM      ARI={adjusted_rand_score(orig, df['hier10']):.3f}, "
          f"NMI={normalized_mutual_info_score(orig, df['hier10']):.3f}")
    print(f"          HDB vs Hier(10)      ARI={adjusted_rand_score(df['hier10'][mask], df['hdb'][mask]):.3f}")

    df.to_csv(F_LABELED, index=False)
    print(f"[cluster] wrote {F_LABELED.relative_to(ROOT)}")
    return df


# ---------------------------------------------------------------------------
# Step 6: label
# ---------------------------------------------------------------------------


def step_label() -> pd.DataFrame:
    """Attach human-readable EN and DE labels by joining on cluster id."""
    df = pd.read_csv(F_LABELED)
    df["hdb_label"] = df["hdb"].map(CLUSTER_LABELS_EN)
    df["hdb_label_de"] = df["hdb"].map(CLUSTER_LABELS_DE)
    df.to_csv(F_LABELED, index=False)
    n = df["hdb_label"].notna().sum()
    print(f"[label] attached labels to {n}/{len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# Step 7: profile
# ---------------------------------------------------------------------------


def _top_terms(keywords: list[str], k: int = 6) -> list[str]:
    """Frequent stems across a cluster, useful for sanity-checking labels."""
    stop = {"software", "zeitarbeit", "zeitarbeitnehmer", "personaldienstleistung",
            "personaldienstleister", "und", "für", "der", "die", "das", "im", "in",
            "am", "mit", "von", "vs", "zu", "auf", "an", "bei", "nach", "aus"}
    words: list[str] = []
    for kw in keywords:
        for w in re.findall(r"[a-zäöüß]+", kw.lower()):
            if len(w) > 3 and w not in stop:
                words.append(w)
    return [t for t, _ in Counter(words).most_common(k)]


def step_profile() -> pd.DataFrame:
    """Per-cluster stats, useful for the writeup and for the brief step."""
    df = pd.read_csv(F_LABELED)
    rows = []
    for cid in sorted(df["hdb"].unique()):
        sub = df[df["hdb"] == cid].sort_values("search_volume", ascending=False)
        rows.append({
            "cluster_id": int(cid),
            "label_en": CLUSTER_LABELS_EN.get(cid, ""),
            "label_de": CLUSTER_LABELS_DE.get(cid, ""),
            "n_keywords": int(len(sub)),
            "total_sv": int(sub["search_volume"].sum()),
            "median_sv": int(sub["search_volume"].median()),
            "mean_kd": round(float(sub["kd"].mean()), 1),
            "median_kd": int(sub["kd"].median()),
            "mean_cpc": round(float(sub["cpc_eur"].mean()), 2),
            "mean_priority": round(float(sub["priority_score"].mean()), 1),
            "pct_commercial": round(float((sub["estimated_intent"] == "commercial").mean() * 100), 0),
            "top_5_kw_by_sv": "; ".join(sub.head(5)["keyword"].tolist()),
            "top_3_kw_by_priority": "; ".join(sub.nlargest(3, "priority_score")["keyword"].tolist()),
            "top_terms": "; ".join(_top_terms(sub["keyword"].tolist())),
        })
    prof = pd.DataFrame(rows)
    prof.to_csv(F_PROFILES, index=False)
    print(f"[profile] wrote {F_PROFILES.relative_to(ROOT)} ({len(prof)} clusters)")
    return prof


# ---------------------------------------------------------------------------
# Step 8: charts (six PNGs for the report)
# ---------------------------------------------------------------------------


def step_charts() -> None:
    """Render the six diagnostic charts referenced by docs/results.md."""
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "DejaVu Sans"

    df = pd.read_csv(F_LABELED)
    red2 = np.load(F_UMAP_2D)
    df["x"], df["y"] = red2[:, 0], red2[:, 1]

    clusters = sorted([c for c in df["hdb"].unique() if c != -1])
    cmap = plt.cm.tab20(np.linspace(0, 1, len(clusters)))

    # Chart 1: 2D UMAP scatter coloured by cluster
    fig, ax = plt.subplots(figsize=(13, 9))
    noise = df[df["hdb"] == -1]
    ax.scatter(noise["x"], noise["y"], c="#cccccc", s=10, alpha=0.4, label="noise")
    for i, cid in enumerate(clusters):
        sub = df[df["hdb"] == cid]
        ax.scatter(sub["x"], sub["y"], c=[cmap[i]], s=14, alpha=0.85,
                   label=f"{cid + 1}: {CLUSTER_LABELS_EN[cid][:30]}")
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

    # Chart 2: bubble (KD vs SV, sized by priority)
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

    # Chart 3: cluster volume bars
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

    # Chart 4: priority matrix (mean KD vs total SV per cluster)
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

    # Chart 5: intent mix per cluster
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

    # Chart 6: method agreement (HDBSCAN vs hierarchical vs LLM)
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    mask = df["hdb"] != -1
    orig = df["category"].astype("category").cat.codes
    pairs = [
        ("HDBSCAN vs LLM", orig[mask], df["hdb"][mask]),
        ("Hier(10) vs LLM", orig, df["hier10"]),
        ("Hier(12) vs LLM", orig, df["hier12"]),
        ("HDB vs Hier(10)", df["hier10"][mask], df["hdb"][mask]),
    ]
    labels = [p[0] for p in pairs]
    aris = [adjusted_rand_score(a, b) for _, a, b in pairs]
    nmis = [normalized_mutual_info_score(a, b) for _, a, b in pairs]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(labels))
    ax.bar(x - 0.2, aris, 0.4, label="ARI", color="#5e8de8")
    ax.bar(x + 0.2, nmis, 0.4, label="NMI", color="#e8965e")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=9)
    ax.set_ylim(0, 1); ax.set_title("Cluster method agreement (higher = more agreement)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CLUSTERING / "chart6_method_agreement.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

    print(f"[charts] wrote 6 PNGs to {CLUSTERING.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Step 9: viz (interactive Plotly map)
# ---------------------------------------------------------------------------


def step_viz() -> Path:
    """Build the interactive bilingual cluster map. Heavy lifting in cluster_viz."""
    from src.cluster_viz import build_cluster_map_html

    df = pd.read_csv(F_LABELED)
    red2 = np.load(F_UMAP_2D)
    html = build_cluster_map_html(df, red2,
                                  labels_en=CLUSTER_LABELS_EN,
                                  labels_de=CLUSTER_LABELS_DE)
    F_VIZ.write_text(html)
    size_kb = F_VIZ.stat().st_size / 1024
    print(f"[viz] wrote {F_VIZ.relative_to(ROOT)} ({size_kb:.0f} KB)")
    return F_VIZ


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


STEPS = {
    "clean": step_clean,
    "embed": step_embed,
    "reduce": step_reduce,
    "sweep": step_sweep,
    "cluster": step_cluster,
    "label": step_label,
    "profile": step_profile,
    "charts": step_charts,
    "viz": step_viz,
}

# Default --all sequence (sweep is diagnostic, not part of all)
DEFAULT_SEQUENCE = ("clean", "embed", "reduce", "cluster", "label", "profile",
                    "charts", "viz")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--step", default="all",
                   help="comma-separated steps from: " + ", ".join(STEPS) + " (or 'all')")
    args = p.parse_args()

    requested = (DEFAULT_SEQUENCE if args.step == "all"
                 else tuple(s.strip() for s in args.step.split(",")))
    unknown = [s for s in requested if s not in STEPS]
    if unknown:
        raise SystemExit(f"unknown step(s): {unknown}. valid: {list(STEPS)}")

    for name in requested:
        print(f"\n=== {name} ===")
        STEPS[name]()


if __name__ == "__main__":
    main()
