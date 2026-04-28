# 2026-04-27 — Manual baseline run

First end-to-end pass at the case study. Keyword set was hand-authored by an
LLM (not yet derived from the live zvoove blog), then run through the
HDBSCAN/UMAP clustering pipeline.

Frozen here as a reference point so we can compare against the first real
`discover.py`-derived run later.

Source: recovered from chat transcripts on 2026-04-28 (the original working
folder `/Users/admin/Projects/seo` was deleted by accident; pipeline scripts
were reconstructed into `_recovered/`).

## Files

- `keywords.csv` — 504 keywords, enriched (SV, KD, CPC, priority_score)
- `cluster_map.html` — interactive Plotly map (was `cluster_map_interactive_v19.html`)
- `clusters.json` — 12 hand-authored cluster definitions

## Pipeline parameters

- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- UMAP: `n_neighbors=15`, `metric='cosine'`, `min_dist=0.0` (5D for clustering) / `0.1` (2D for viz), `random_state=42`
- HDBSCAN: `min_cluster_size=15`, `min_samples=5`, `cluster_selection_method='eom'`, `metric='euclidean'`
- Result: 13 clusters + noise
