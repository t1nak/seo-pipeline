# Prozessarchitektur

Diese Datei beschreibt den Datenfluss durch die Pipeline, die Schnittstellen zwischen Schritten und die Einbindung in externe Systeme.

## Pipeline auf einen Blick

![Pipeline Architektur](landing_diagram.svg)

Vier modulare Phasen, an jeder Stelle sind Provider per Konfiguration austauschbar (Keyword-Quelle, LLM für Briefings, Reporting-Ziel). Auslöser: GitHub Actions per Cron-Schedule oder manueller Trigger.

## Implementierungs-Detail

Die folgende SVG zeigt links die externen Provider (jede Spalte mit den heute aktiven und alternativen Optionen), in der Mitte die sechs entkoppelten Skripte (Discover, Enrich, Cluster, Brief, Report, Export) mit den jeweiligen Sub-Schritten von `cluster.py`, rechts die produzierten Datenartefakte. Diese Skripte realisieren die vier modularen Phasen aus dem Diagramm oben; Discover und Enrich liegen heute als zwei Skripte vor, weil das Discover-Stub auf Heuristik arbeitet, würden bei Providern wie SEMrush oder DataForSEO mit erweitertem Endpoint aber zusammenfallen. Report und Export gehören beide zur Reporting-Phase: Report erzeugt ein menschlich lesbares HTML-Dashboard, Export ein maschinenlesbares JSON-Trio für externe Reporting-Tools. Markierte Artefakte (★ gelb) sind über GitHub Pages live deployed.

![Architektur Diagramm](architecture.svg){ .zoomable }

*Klick auf das Diagramm öffnet eine Vollbild-Ansicht zum Zoomen.*

## Module und Aufgaben

| Schicht | Modul | Verantwortlich für |
|---|---|---|
| **Quelle** | `src/discover.py` | Welche Keywords sind überhaupt relevant. Aktuell Stub mit `--source manual`. |
| **Anreicherung** | `src/enrich.py` | Pro Keyword: SV, KD, CPC, SERP Features, Priority Score. Heuristik oder DataForSEO. |
| **Strukturierung** | `src/cluster.py` | Embeddings, Dimensionsreduktion, Density-based Clustering, Soft-Assignment der Rand-Keywords (Schritt `assign_noise`), Profiling. Charts und interaktive Karte werden im Report-Schritt aus `src/cluster_viz.py` aufgerufen. |
| **Beschriftung** | `src/labels_llm.py` | Pro Cluster ein DE- und EN-Label per Anthropic-Batch-Call. Schreibt `cluster_labels.json` und aktualisiert die Label-Spalten in `cluster_profiles.csv` und `keywords_labeled.csv`. |
| **Aktivierung** | `src/brief.py` | Pro Cluster ein redaktions-fertiger Content Brief. Claude API mit Prompt Caching. |
| **Reporting** | `src/report.py` | Konsolidiertes HTML-Dashboard, das alle Artefakte verbindet. |
| **Reporting (JSON)** | `src/export.py` | Bündelt alle Ergebnisse als `clusters.json`, `keywords.json` und `report.json` zum direkten Import in Airtable, Notion, Google Sheets oder Looker Studio. |
| **Orchestrierung** | `pipeline.py` plus Workflow `pipeline-full.yml` | `pipeline.py` orchestriert die sechs Pipeline-Schritte, der Workflow ruft den Label-Schritt zwischen `cluster` und `brief` auf (`Step 3b`). |

## Schnittstellen zwischen Schritten

Jeder Schritt liest und schreibt explizite Dateien. Das macht jeden Schritt einzeln testbar und einzeln re-runnbar.

### Discover -> Enrich

**Schnittstelle:** `data/keywords.csv` mit Spalten `keyword, estimated_intent, category, type, notes`.

| Spalte | Werte | Pflicht |
|---|---|---|
| `keyword` | Freitext, deutsch | Ja |
| `estimated_intent` | `commercial`, `informational`, `transactional`, `navigational` | Ja |
| `category` | Original-Cluster-ID aus dem Discover-Stub. Dient nur als Vergleichsbasis und ist nicht identisch mit den später per HDBSCAN gefundenen Clustern. | Ja |
| `type` | `head`, `body`, `longtail` | Ja |
| `notes` | Freitext | Optional |

### Enrich -> Cluster

**Schnittstelle:** `data/keywords.csv` plus die neuen Spalten.

| Neue Spalte | Werte |
|---|---|
| `search_volume` | Integer, monatliches Suchvolumen |
| `kd` | Integer 0 bis 100, Keyword Difficulty |
| `cpc_eur` | Float, Cost per Click in EUR |
| `serp_features` | Pipe-separated Liste (`ads\|featured-snippet\|...`) |
| `priority_score` | Float, `volume / max(kd, 5)` |
| `data_source` | `estimated` oder `dataforseo` |

### Cluster -> Labels

**Schnittstelle:** `cluster_profiles.csv` (Top-Keywords und Top-Terms pro Cluster) wird vom Label-Schritt gelesen. Output: `output/clustering/cluster_labels.json` mit DE- und EN-Label pro Cluster-ID, plus die aktualisierten Spalten `label_en` / `label_de` in `cluster_profiles.csv` und `hdb_label` / `hdb_label_de` in `keywords_labeled.csv`. Details in [ADR-5](decisions.md#adr-5-llm-generierte-cluster-labels-pro-lauf-yaml-als-fallback).

### Labels (oder Cluster) -> Brief

**Schnittstelle:** `output/clustering/cluster_profiles.csv` plus `output/clustering/keywords_labeled.csv`.

`cluster_profiles.csv` ist die aggregierte Sicht: eine Zeile pro Cluster mit Stats, Top Keywords, Labels.
`keywords_labeled.csv` ist die per-Keyword Sicht mit `hdb` (Cluster ID), `hdb_label` (EN), `hdb_label_de`, `hier10`, `hier12`.

### Cluster -> Report und Brief -> Report

`report.py` liest:

- `output/clustering/cluster_profiles.csv` (Tabellen Daten)
- `output/clustering/cluster_map.html` (Link)
- `output/clustering/chart*.png` (eingebettete Bilder)
- `output/briefings/*.md` (Liste, für die Brief-Spalte in der Tabelle)

### Report (oder Cluster und Brief direkt) -> Export

`export.py` liest dieselben Quellen wie `report.py` und schreibt drei flache JSON-Dateien nach `output/reporting/`:

- `clusters.json` eine Zeile pro Cluster mit allen KPIs plus den geparsten Brief-Feldern (Hauptkeyword, Zielgruppe, H1, H2-Outline, Wortanzahl, CTA, Benchmark-URLs als Liste).
- `keywords.json` eine Zeile pro Keyword mit Cluster-Zuordnung und allen Metriken (SV, KD, CPC, Priority, SERP Features).
- `report.json` Bundle aus Run-Metadaten plus beiden Listen.

Wenn `report.py` für denselben Lauf zuvor lief, werden die drei Dateien zusätzlich nach `output/reporting/runs/<run_id>/` gespiegelt, damit der Export pro Lauf erhalten bleibt.

## Datenflüsse: was läuft wann

| Phase | Wer löst aus | Was wird neu berechnet | Was bleibt |
|---|---|---|---|
| Wöchentliche Aktualisierung | Cron | `enrich` (für SV/KD Updates), `report` | Cluster, Labels, Briefs |
| Re-Clustering | Manuell oder geplant | Alles, inklusive frischer LLM-Labels | Nichts (mit Snapshot in `output/_archive/`) |
| Label-Refresh ohne Re-Clustering | Manuell | nur `labels_llm` (Cluster-IDs bleiben, neue Labels) | Embeddings, UMAP, HDBSCAN, Briefs |
| Brief Update für einen Cluster | Manuell | nur ein Brief | Alles andere |

Der Snapshot-Mechanismus in `output/_archive/` schützt vor unbeabsichtigtem Datenverlust: vor jedem `cluster --step all` wird der aktuelle Output Stand pinned.

## Einbindung in externe Systeme

Diese Pipeline ist bewusst als Datenquelle gebaut, nicht als geschlossenes System. Pro Schritt gibt es eine klare Andockung an externe Systeme:

| Pipeline Output | Beispiel | Anbindung |
|---|---|---|
| `data/keywords.csv` | Google Ads | Direkter CSV Import in Keyword Planner für Search Kampagnen |
| `data/keywords.csv` | Ahrefs / Semrush | CSV Import für Rank Tracking auf den 500 Keywords |
| `output/reporting/clusters.json` | Airtable, Notion-Datenbank | Content-Kalender-Anker, ein Eintrag pro Cluster mit allen Brief-Feldern |
| `output/reporting/keywords.json` | Google Sheets, Airtable | Filterbare Keyword-Tabelle, sortier- und gruppierbar nach Cluster, Intent, Priorität |
| `output/reporting/report.json` | Looker Studio, Metabase, BI-Tools | Konsolidierte Datenquelle für ein SEO-Dashboard inkl. Run-Metadaten |
| `output/clustering/cluster_profiles.csv` | Looker Studio (CSV-Connector) | Klassischer CSV-Import als Alternative zu `report.json` |
| `output/briefings/*.md` | Sanity / Contentful | Draft Eintrag pro Cluster für die Redaktion |
| `output/clustering/cluster_map.html` | Slack, Notion, Confluence | Embed in Marketing Wiki oder wöchentliche Stand-up Updates |
| `output/reporting/index.html` | Internes Wiki | Self-service Dashboard, Stakeholder können selbst nachschauen |

## Cost und Performance

### Zeit pro Schritt (lokaler Lauf, 500 Keywords)

| Schritt | Zeit | Wovon abhängig |
|---|---|---|
| `clean` | < 1 Sekunde | Keyword Anzahl |
| `embed` | 5 bis 8 Sekunden (erstes Mal: zusätzlich Modell-Download ~120 MB) | Keyword Anzahl, CPU |
| `reduce` | 3 bis 4 Sekunden | Anzahl plus Embedding Dimension |
| `cluster` | 2 bis 3 Sekunden | UMAP Dimension |
| `assign_noise` (Soft-Assignment) | < 1 Sekunde | Anzahl Rand-Keywords mal Cluster |
| `label` (HDBSCAN-Output) | < 1 Sekunde | Keyword Anzahl |
| `profile` | < 1 Sekunde | Cluster Anzahl |
| `labels_llm` (Anthropic Haiku, Batch-Call) | 4 bis 8 Sekunden | API-Latenz |
| `report` (Charts, Cluster-Map, Dashboard) | 8 bis 12 Sekunden | matplotlib- und Plotly-Rendering |
| `export` (drei JSON-Dateien) | < 1 Sekunde | Cluster- und Keyword-Anzahl |
| `brief` (alle Cluster, mit API) | 60 bis 130 Sekunden | Anthropic API Latenz, linear in Cluster-Anzahl |

Voller Lauf ohne Briefs (Demo, kein Label-Call): ungefähr 25 Sekunden. Voller Lauf mit Labels und Briefs: ungefähr 2 bis 3 Minuten (13 Cluster).

### Kosten pro Lauf, je Provider-Kombination

Embeddings, UMAP und HDBSCAN laufen lokal (0 USD). Variabel sind Enrichment, Label-Step und Brief-Provider.

| Enrichment | Label-Step | Brief-Provider | Enrichment | Label | Brief | Gesamt pro Lauf |
|---|---|---|---|---|---|---|
| Heuristik | aus (`dry_run=true`) | Stub | 0 USD | 0 USD | 0 USD | **0 USD** |
| Heuristik | Anthropic Haiku | Anthropic Sonnet (Caching) | 0 USD | ~0,01 USD | ~0,18 USD | **~0,19 USD** |
| Heuristik | Anthropic Haiku | OpenAI (gpt-5) | 0 USD | ~0,01 USD | ~0,40 USD | **~0,41 USD** |
| DataForSEO | Anthropic Haiku | Anthropic Sonnet | ~0,75 USD | ~0,01 USD | ~0,18 USD | **~0,94 USD** |
| DataForSEO | Anthropic Haiku | OpenAI | ~0,75 USD | ~0,01 USD | ~0,40 USD | **~1,16 USD** |
| SEMrush / Ahrefs | Anthropic Haiku | je Brief-Provider | abhängig vom Plan | ~0,01 USD | abhängig | abhängig |

Annahmen: 500 Keywords (alle in Clustern dank Soft-Assignment, siehe [ADR-15](decisions.md#adr-15-soft-assignment-fur-noise-keywords)), 13 Cluster, Sonnet mit Prompt Caching auf System Block. Brief-Kosten skalieren linear mit der Cluster-Anzahl. Der Label-Step ist ein einziger Batch-Call und bleibt nahezu konstant (~1 Cent), egal wie viele Cluster entstehen.

## Skalierung

Was ändert sich, wenn das Keyword Set wächst auf 5000 Keywords?

| Schritt | Skaliert wie | Bei 5000 KW |
|---|---|---|
| `embed` | linear | ungefähr 60 Sekunden |
| `reduce` | n log n | ungefähr 30 Sekunden |
| `cluster` | n log n | ungefähr 20 Sekunden |
| `brief` | linear in Cluster Anzahl | falls 30 Cluster: ungefähr 5 Minuten |

Skalierungs-Bottleneck: nicht die Pipeline selbst, sondern die Brief Generation. Bei 50 Cluster wären das 50 API Calls. Mit Concurrency und Prompt Caching beherrschbar.

Speicher: Embeddings sind 384 float32 pro Keyword, also 1,5 KB pro Keyword. 5000 Keywords sind 7,5 MB. Vernachlässigbar.

## Reproduktion

Die Pipeline ist deterministisch innerhalb derselben Plattform und Library-Version (siehe `docs/methodology.md`). Ein zweiter Lauf auf derselben Maschine produziert byte-identische Artefakte.

```bash
git clone https://github.com/t1nak/seo-pipeline.git
cd seo-pipeline
pip install -r requirements.txt
python pipeline.py
```

Erwartung: identische Cluster Aufteilung, identische Charts, identisches Reporting (modulo Zeitstempel im Reporting).
