# SEO Keyword Pipeline for zvoove

!!! abstract "What this pipeline does"
    Turns the zvoove blog into a prioritised keyword set, into thematic clusters, into content briefs, into an interactive report. Five decoupled steps. Local ML, Anthropic API for briefs, GitHub Pages for the live demo.

![Cluster Overview](assets/cluster_overview.png)

## The problem in one sentence

The goal is to win organic traffic in the temp staffing and HR services space, traffic that brings real buyers. That requires a clear answer to one question: which topics are worth pursuing, and in what order?

## Quick entry points

<div class="grid cards" markdown>

-   :material-map-marker-radius: __Interactive cluster map__

    13 thematic groups visualised. Click any dot for keyword details. Language toggle EN/DE.

    [:octicons-arrow-right-24: Live demo](https://t1nak.github.io/seo-pipeline/output/clustering/cluster_map.html)

-   :material-file-chart: __Reporting dashboard__

    KPIs, cluster table, charts, brief links on a single page.

    [:octicons-arrow-right-24: Live demo](https://t1nak.github.io/seo-pipeline/output/reporting/index.html)

-   :material-book-open-variant: __Case Study__

    Long-form writeup with architecture, validation, recommendations, reflection.

    [:octicons-arrow-right-24: Read](case-study.md)

-   :material-flask: __Methodology__

    Why HDBSCAN, why UMAP, hyperparameter sweep, validation with real numbers.

    [:octicons-arrow-right-24: Depth](methodology.md)

-   :material-format-list-bulleted: __13 cluster catalogue__

    Per cluster: stats, top keywords, recommendation, effort, revenue hypothesis.

    [:octicons-arrow-right-24: Results](results.md)

-   :material-file-tree: __Architecture__

    Data flow, interfaces, revenue stack integration, scaling behaviour.

    [:octicons-arrow-right-24: Diagram](architecture.md)

</div>

!!! info "Detail docs are German"
    The detailed documentation pages (Methodology, Results, Architecture, Decisions, Case Study) are written in German because the case study brief and the target audience are German. This English overview is a quick orientation for international readers. Most pages link back to the original German source.

## Results from the current run

<div class="grid" markdown>

`504` keywords

`13` clusters plus 71 outliers

`240,025` SV per month (estimated)

`0.64` silhouette score (without noise)

`0.75` ARI vs Ward hierarchical (k=10)

`~25 s` full run without briefs

</div>

The five largest clusters by search volume:

| # | Cluster | Keywords | SV / month | Avg KD | % comm. |
|---|---|---|---|---|---|
| 11 | B2B SaaS category heads | 52 | 48,945 | 48 | 77 |
| 3 | Commercial SaaS heads (Zeit/Software) | 46 | 26,062 | 48 | 93 |
| 13 | Industry & operations catch-all | 82 | 24,589 | 38 | 38 |
| 5 | Brand: zvoove product names | 32 | 23,432 | 54 | 100 |
| 9 | Digitalisation umbrella | 22 | 12,979 | 38 | 45 |

[All 13 clusters in detail :octicons-arrow-right-24:](results.md)

## Current pipeline state

| Step | State |
|---|---|
| Discover | Stub. `--source manual` works, `--source live` not yet implemented |
| Enrich | Complete. Heuristic plus optional DataForSEO live lookup |
| Cluster | Complete. Embeddings, UMAP, HDBSCAN, 6 charts, interactive map |
| Brief | Complete. Claude API with prompt caching |
| Report | Complete. Consolidated HTML dashboard |

This pipeline runs end-to-end on a previously LLM-derived keyword set. The discover step does not scrape the live blog yet. That is documented transparently in [decisions](decisions.md) and is the next high-leverage piece of work.

## Quickstart

```bash
# install dependencies
pip install -r requirements.txt

# run the full pipeline
python pipeline.py

# run individual steps
python pipeline.py --step cluster
python pipeline.py --step brief --dry-run    # without Claude API
python pipeline.py --step report
```

For real content briefs (otherwise stubs), an Anthropic API key is needed:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python pipeline.py --step brief
```

[Full CLI reference in the repo :octicons-arrow-right-24:](https://github.com/t1nak/seo-pipeline#schnellstart)

## Tech stack at a glance

| Layer | Tool | Why |
|---|---|---|
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` | multilingual, runs locally without GPU |
| Reduction | `umap-learn` | better local structure than PCA for density-based clustering |
| Clustering | `hdbscan` | picks number of clusters itself, marks outliers as noise |
| Comparison | Ward hierarchical (`scipy`) | transparent granularity control, ARI as cross-check |
| Visualisation | `plotly` (interactive), `matplotlib` (PNG) | Plotly for the click map, matplotlib for static diagnostics |
| LLM briefs | `anthropic` SDK, `claude-sonnet-4-6` | with prompt caching on the system block |
| Live keyword data | DataForSEO Labs API | optional, heuristic as default |

## Licence and context

Personal case study project for an application as Revenue AI Architect at zvoove. Not officially affiliated.
