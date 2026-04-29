"""Run a second HDBSCAN pass on a single cluster to find sub-themes.

The main pipeline produces a Cluster 2 (Branche & Arbeitsrecht) with 189
keywords. That is too heterogeneous to write a single pillar against. This
module re-runs UMAP + HDBSCAN only on those 189 points to surface
sub-clusters, then writes a CSV summary plus a per-sub-cluster markdown
brief stub.

CLI:
    python -m src.subcluster --cluster 1
    python -m src.subcluster --cluster 1 --mcs 8 --ms 3
"""
from __future__ import annotations

import argparse
import re
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
CLUSTERING = ROOT / "output" / "clustering"


def run(cluster_id: int, mcs: int, ms: int, method: str) -> None:
    import hdbscan
    import umap
    from sklearn.metrics import silhouette_score

    emb = np.load(CLUSTERING / "embeddings.npy")
    df = pd.read_csv(CLUSTERING / "keywords_labeled.csv")

    mask = (df["hdb"] == cluster_id).values
    n = int(mask.sum())
    if n < 2 * mcs:
        raise SystemExit(f"cluster {cluster_id} has only {n} keywords, "
                         f"too few for sub-clustering with mcs={mcs}")

    sub_emb = emb[mask]
    sub_df = df[mask].reset_index(drop=True).copy()
    print(f"[subcluster] cluster {cluster_id}: {n} keywords, "
          f"label={sub_df['hdb_label_de'].iloc[0]}")

    # Re-run UMAP on just this slice (different distribution -> different reduction)
    red5 = umap.UMAP(n_neighbors=10, n_components=5, metric="cosine",
                     min_dist=0.0, random_state=42).fit_transform(sub_emb)
    red2 = umap.UMAP(n_neighbors=10, n_components=2, metric="cosine",
                     min_dist=0.1, random_state=42).fit_transform(sub_emb)

    cl = hdbscan.HDBSCAN(min_cluster_size=mcs, min_samples=ms,
                         cluster_selection_method=method, metric="euclidean")
    labs = cl.fit_predict(red5)
    sub_df["sub_cluster"] = labs
    sub_df["sub_x"] = red2[:, 0]
    sub_df["sub_y"] = red2[:, 1]

    n_clu = len(set(labs)) - (1 if -1 in labs else 0)
    noise = int((labs == -1).sum())
    sil = (silhouette_score(red5[labs != -1], labs[labs != -1])
           if n_clu > 1 and (labs != -1).sum() > 10 else float("nan"))
    print(f"[subcluster] {n_clu} sub-clusters, {noise} noise "
          f"({noise/n*100:.1f}%), silhouette={sil:.3f}")

    # Save full slice with sub-cluster label
    out_csv = CLUSTERING / f"sub_cluster_{cluster_id:02d}.csv"
    sub_df.to_csv(out_csv, index=False)
    print(f"[subcluster] wrote {out_csv.relative_to(ROOT)}")

    # Per sub-cluster top keywords + frequent terms
    print("\n=== Sub-Cluster Profiles ===")
    rows = []
    for sub_cid in sorted(sub_df["sub_cluster"].unique()):
        s = sub_df[sub_df["sub_cluster"] == sub_cid].sort_values(
            "search_volume", ascending=False)
        name = "noise" if sub_cid == -1 else f"sub_{sub_cid:02d}"
        top_kw = s.head(8)["keyword"].tolist()
        terms = _top_terms(s["keyword"].tolist(), 6)
        total_sv = int(s["search_volume"].sum())
        pct_comm = round(float((s["estimated_intent"] == "commercial").mean() * 100), 0)
        print(f"\n--- {name} (n={len(s)}, SV={total_sv:,}, {int(pct_comm)}% komm) ---")
        print(f"  top keywords: {'; '.join(top_kw[:5])}")
        print(f"  frequent terms: {', '.join(terms)}")
        rows.append({
            "parent_cluster": cluster_id,
            "sub_cluster_id": int(sub_cid),
            "label": "(zu vergeben)",
            "n_keywords": int(len(s)),
            "total_sv": total_sv,
            "median_kd": int(s["kd"].median()),
            "pct_commercial": int(pct_comm),
            "top_5_kw_by_sv": "; ".join(top_kw[:5]),
            "top_terms": "; ".join(terms),
        })

    profiles = pd.DataFrame(rows)
    out_prof = CLUSTERING / f"sub_cluster_{cluster_id:02d}_profiles.csv"
    profiles.to_csv(out_prof, index=False)
    print(f"\n[subcluster] wrote {out_prof.relative_to(ROOT)}")


def _top_terms(keywords: list[str], k: int = 6) -> list[str]:
    stop = {"software", "zeitarbeit", "personaldienstleistung",
            "personaldienstleister", "und", "für", "der", "die", "das", "im",
            "in", "am", "mit", "von", "vs", "zu", "auf", "an", "bei", "nach",
            "aus", "als"}
    words: list[str] = []
    for kw in keywords:
        for w in re.findall(r"[a-zäöüß]+", kw.lower()):
            if len(w) > 3 and w not in stop:
                words.append(w)
    return [t for t, _ in Counter(words).most_common(k)]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--cluster", type=int, required=True,
                   help="parent cluster id (0-based) to sub-cluster")
    p.add_argument("--mcs", type=int, default=8, help="HDBSCAN min_cluster_size")
    p.add_argument("--ms", type=int, default=3, help="HDBSCAN min_samples")
    p.add_argument("--method", default="eom", choices=["eom", "leaf"])
    args = p.parse_args()
    run(args.cluster, args.mcs, args.ms, args.method)


if __name__ == "__main__":
    main()
