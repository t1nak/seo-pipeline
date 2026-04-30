# SEO Keyword Pipeline für zvoove

## Was ist die SEO Pipeline?

Eine Daten-Pipeline für die automatisierte Erstellung von SEO Content Briefs. Vier modulare Phasen mit auswechselbaren Providern an jeder Stelle: Keyword-Quelle, LLM für Briefings, Reporting-Ziel. Die Architektur unten zeigt die wählbaren Komponenten je Phase, der Auslöser läuft per Cron-Schedule oder manuellem Trigger.

![Pipeline Architektur](landing_diagram.svg)

**Beispiel-Demo:** Diese Pipeline läuft end-to-end auf einem zuvor LLM-erzeugten Keyword Set. Daraus entstehen thematische Cluster, Content Briefs und ein interaktives Reporting. Provider per Konfiguration austauschbar. Lokale ML, Anthropic API für Briefs, GitHub Pages für die Live Demo. Der Discover-Schritt scrapt den Blog noch nicht live, das ist transparent in den [Entscheidungen](decisions.md) dokumentiert und der nächste Arbeitsblock.

[:material-rocket-launch: Go to Pipeline (GitHub Actions)](https://github.com/t1nak/seo-pipeline/actions/workflows/pipeline-full.yml){ .md-button .md-button--primary target=_blank rel=noopener }

## Häufige Fragen

### Wie wird die Pipeline getriggert?

GitHub Actions: per Cron-Schedule oder manuellem Trigger via [`workflow_dispatch`](https://github.com/t1nak/seo-pipeline/actions/workflows/pipeline-full.yml). Lokal startest du sie mit `python pipeline.py`, einzelne Schritte via `--step cluster|brief|report`.

### Wie kann ich Model und Provider ändern?

Alle Provider sind per CLI-Flag oder `PIPELINE_*` Environment-Variable wählbar.

| Komponente | CLI-Flag | Optionen |
|---|---|---|
| Brief-Provider | `--brief-provider` | `api` (Anthropic), `openai`, `max` (Agent SDK) |
| Brief-Model | `--brief-model` | beliebige Modell-ID, z.B. `claude-sonnet-4-6` |
| Keyword-Quelle | `--source` | `manual`, `live` |
| Enrich-Provider | `--provider` | `estimate` (Heuristik), `dataforseo` |

### Was kostet ein Lauf?

Bei der aktuellen Konfiguration (10 Cluster, Anthropic API mit Prompt Caching) rund **0,15 bis 0,25 USD pro Lauf** für die Brief-Generierung. Optionaler DataForSEO Live-Lookup für 500 Keywords: ~0,75 USD. Gesamt **~1 USD pro voller Lauf**, bei wöchentlicher Ausführung etwa 50 USD pro Jahr. Detail in §12 der [Case Study](case-study.md).

### Wie viele Cluster werden erkannt?

HDBSCAN bestimmt die Cluster-Anzahl selbst aus der Datendichte, ohne vorgegebene `k`. Auf der aktuellen 500-Keyword-Baseline: **10 Cluster plus rund 40 Ausreißer** (~8 Prozent als Rauschen markiert). Hyperparameter-Sweep und Wahl von `mcs=12` aus der Plateau-Klasse in der [Methodik](methodology.md).

### Welche Daten werden lokal gespeichert?

Alles bleibt im Repo, keine externen Datenbanken. Die Artefakte liegen unter:

- `data/keywords.csv` (angereicherte Keyword-Liste)
- `output/clustering/` (Embeddings, UMAP-Reduktionen, Cluster-Map, Diagnostik-Charts)
- `output/briefings/cluster_*.md` (Content-Briefings je Cluster)
- `output/reporting/index.html` (konsolidiertes Dashboard)

API-Keys liegen in `.env` (lokal) bzw. GitHub Secrets (CI), nicht im Repo.

## Schnelle Einstiegspunkte

<div class="grid cards" markdown>

-   :material-rocket-launch: __Pipeline jetzt starten__

    Workflow-Dispatch in GitHub Actions: Provider und Modell wählen, Lauf starten. Status, Logs und Artefakte direkt im Run.

    [:octicons-arrow-right-24: Pipeline ausführen](https://github.com/t1nak/seo-pipeline/actions/workflows/pipeline-full.yml)

-   :material-map-marker-radius: __Interaktive Cluster Karte__

    10 Themengruppen visuell, mit Klick auf jeden Punkt die Details. Sprache umschaltbar.

    [:octicons-arrow-right-24: Live Demo](https://t1nak.github.io/seo-pipeline/output/clustering/cluster_map.html)

-   :material-file-chart: __Reporting Dashboard__

    KPIs, Cluster Tabelle, Charts, Brief Links auf einer Seite.

    [:octicons-arrow-right-24: Live Demo](https://t1nak.github.io/seo-pipeline/output/reporting/index.html)

-   :material-card-text-outline: __Cluster Briefs Dashboard__

    Pro Cluster ein Content Brief mit Top-Keywords, Persona, Seitenstruktur, SERP-Lücken, CTA.

    [:octicons-arrow-right-24: Live Demo](https://t1nak.github.io/seo-pipeline/output/briefings/index.html)

-   :material-book-open-variant: __Case Study__

    Vollständige Schreibarbeit mit Architektur, Validierung, Empfehlungen, Reflektion.

    [:octicons-arrow-right-24: Lesen](case-study.md)

-   :material-flask: __Methodik__

    Warum HDBSCAN, warum UMAP, Hyperparameter Sweep, Validierung mit echten Zahlen.

    [:octicons-arrow-right-24: Tiefe](methodology.md)

-   :material-format-list-bulleted: __10 Cluster Katalog__

    Pro Cluster: Stats, Top Keywords, Empfehlung, Aufwand, Revenue Hypothese.

    [:octicons-arrow-right-24: Ergebnisse](results.md)

-   :material-file-tree: __Architektur__

    Datenfluss, Schnittstellen, Revenue Stack Integration, Skalierungs-Verhalten.

    [:octicons-arrow-right-24: Diagramm](architecture.md)

</div>

## Ergebnisse aus dem aktuellen Lauf

<div class="grid" markdown>

`500` Keywords (Cap aus 504 Baseline)
{ .annotate }

`10` Cluster plus 40 Ausreißer (8,0 Prozent)

`213.302` SV pro Monat (geschätzt, ohne Rauschen)

`0,67` Silhouette Score (ohne Rauschen)

`0,57` ARI gegen Ward Hierarchical (k=10)

`~25 s` voller Lauf ohne Briefs

</div>

Die fünf größten Cluster nach Suchvolumen:

| # | Cluster | Keywords | SV / Monat | Ø KD | % komm. |
|---|---|---|---|---|---|
| 10 | B2B-SaaS Kategorie-Heads | 44 | 47.989 | 49 | 82 |
| 3 | Kommerzielle Zeit/Software-Heads | 47 | 26.159 | 43 | 94 |
| 5 | Marke: zvoove Produktnamen | 34 | 23.604 | 51 | 97 |
| 6 | Operative Anleitungen (gemischt) | 30 | 13.755 | 33 | 23 |
| 4 | Recruiting & KI-Tools | 34 | 12.075 | 38 | 44 |

Plus der Catch-all Cluster 2 mit 189 Keywords (Branche & Arbeitsrecht), nach Anzahl der größte mit 64.264 SV.

[Alle 10 Cluster im Detail :octicons-arrow-right-24:](results.md)

## Aktueller Stand der Pipeline

| Schritt | Stand |
|---|---|
| Discover | Stub. `--source manual` funktioniert, `--source live` ist offen |
| Enrich | Vollständig. Heuristik plus optional DataForSEO Live Lookup |
| Cluster | Vollständig. Embeddings, UMAP, HDBSCAN, 6 Charts, interaktive Karte |
| Brief | Vollständig. Claude API mit Prompt Caching |
| Report | Vollständig. Konsolidiertes HTML Dashboard |

## Schnellstart

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Komplette Pipeline ausführen
python pipeline.py

# Einzelne Schritte
python pipeline.py --step cluster
python pipeline.py --step brief --dry-run    # ohne Claude API
python pipeline.py --step report
```

Für echte Content Briefs (sonst Stubs) wird ein Anthropic API Key gebraucht:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python pipeline.py --step brief
```

[Vollständige CLI Referenz im Repo :octicons-arrow-right-24:](https://github.com/t1nak/seo-pipeline#schnellstart)

## Tech Stack auf einen Blick

| Schicht | Werkzeug | Warum |
|---|---|---|
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` | mehrsprachig, läuft lokal ohne GPU |
| Reduktion | `umap-learn` | bessere lokale Struktur als PCA für density-based clustering |
| Clustering | `hdbscan` | wählt Clusteranzahl selbst, markiert Ausreißer als Rauschen |
| Vergleich | Ward Hierarchical (`scipy`) | transparente Granularitäts-Kontrolle, ARI als Gegenprobe |
| Visualisierung | `plotly` (interaktiv), `matplotlib` (PNG) | Plotly für Klick-Karte, matplotlib für statische Diagnostik |
| LLM Briefs | `anthropic` SDK, `claude-sonnet-4-6` | mit Prompt Caching auf System Block |
| Live Keyword Daten | DataForSEO Labs API | optional, Heuristik als Default |

## Lizenz und Kontext

Persönliches Case Study Projekt für eine Bewerbung als Revenue AI Architect bei zvoove. Nicht offiziell affiliated.
