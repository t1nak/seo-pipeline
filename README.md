# SEO Keyword Pipeline für zvoove

Eine Pipeline, die aus dem zvoove Blog ein priorisiertes Keyword Set, thematische Cluster, Content Briefs und ein interaktives Reporting macht.

![Cluster Map Vorschau](output/clustering/chart1_umap_map.png)

## Das Problem in einem Satz

Das Ziel ist es, im Bereich Zeitarbeit und Personaldienstleistung organischen Traffic zu gewinnen, der echte Kaufinteressenten bringt. Dafür braucht es eine klare Antwort auf die Frage: Welche Themen lohnen sich wirklich, und in welcher Reihenfolge?

## Was diese Pipeline tut

```
Discover  ->  Enrich     ->  Cluster      ->  Brief         ->  Report
Blog          SV/KD/CPC      HDBSCAN          Claude API        Dashboard
zvoove.de     Heuristik      Embeddings       pro Cluster       konsolidiert
              + DataForSEO   + UMAP           ein Brief         alle Schritte
```

Sie nimmt den bestehenden Blog [zvoove.de/wissen/blog](https://zvoove.de/wissen/blog), entwickelt daraus bis zu 500 thematisch passende Keywords, gruppiert sie automatisch nach Bedeutung, schreibt für jede Gruppe einen Content Brief und liefert ein interaktives Dashboard mit Empfehlungen.

## Schnelle Einstiegspunkte

| Was | Wo |
|---|---|
| Interaktive Cluster Karte | [`output/clustering/cluster_map.html`](output/clustering/cluster_map.html) (lokal im Browser öffnen) |
| Konsolidierter Report | [`output/reporting/index.html`](output/reporting/index.html) |
| Beispiel Content Brief | [`output/briefings/cluster_05.md`](output/briefings/cluster_05.md) |
| Cluster Profile (CSV) | [`output/clustering/cluster_profiles.csv`](output/clustering/cluster_profiles.csv) |
| Methodische Begründung | [`docs/methodology.md`](docs/methodology.md) |
| Vollständige Case Study | [`CASE_STUDY.md`](CASE_STUDY.md) |

## Ergebnisse aus dem aktuellen Lauf

- 504 Keywords, 13 thematische Cluster plus 71 Ausreißer
- Gesamt Suchvolumen: 240.025 pro Monat (geschätzt)
- Größter Cluster nach SV: B2B SaaS Kategorie-Heads (48.945 SV / Monat, 52 Keywords)
- Höchste kommerzielle Dichte: Marke zvoove (100 Prozent kommerziell, 23.432 SV)
- Methodische Validierung: Silhouette Score 0.64 auf der 5D UMAP (ohne Rauschen), 0.46 inklusive Rauschen. ARI gegen die ursprünglichen LLM Cluster bei 0.14, NMI bei 0.33. Diese Werte sind erwartet niedrig, weil HDBSCAN und die LLM Cluster unterschiedliche Granularität haben. Details in [`docs/methodology.md`](docs/methodology.md)

## Aktueller Stand

Diese Pipeline läuft end-to-end auf einem zuvor LLM-erzeugten Keyword Set. Der Discover Schritt scrapt den Blog noch nicht live, sondern liest die kuratierte Datei `data/keywords.manual.csv`. Das ist transparent dokumentiert in [`docs/decisions.md`](docs/decisions.md) und der nächste hochwertige Arbeitsblock.

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

# Cluster Sub-Schritte einzeln
python -m src.cluster --step embed,reduce,cluster,label,profile
python -m src.cluster --step viz              # nur die interaktive Karte neu bauen
python -m src.cluster --step sweep            # diagnostischer Hyperparameter Sweep
```

Für echte Content Briefs (sonst Stubs) wird ein Anthropic API Key gebraucht:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python pipeline.py --step brief
```

Für Live Keyword Daten statt Heuristik:

```bash
export DATAFORSEO_LOGIN=...
export DATAFORSEO_PASSWORD=...
python pipeline.py --step enrich --provider dataforseo
```

## Repo Struktur

```
seo-pipeline/
├── README.md              dieses Dokument
├── CASE_STUDY.md          ausführliche Schreibarbeit zum Vorgehen
├── pipeline.py            Orchestrator für alle 5 Schritte
├── requirements.txt
├── data/
│   ├── keywords.csv             aktueller Stand (überschreibbar durch discover)
│   └── keywords.manual.csv      kuratierter Baseline Datensatz, bleibt frozen
├── docs/
│   ├── methodology.md     warum HDBSCAN, warum UMAP, Parameter Sweep, Validierung
│   ├── results.md         13 Cluster Katalog mit Revenue Empfehlung
│   ├── architecture.md    Pipeline Diagramm, Datenfluss, Integration
│   └── decisions.md       Architecture Decision Records, knappe ADRs
├── output/
│   ├── clustering/        Embeddings, UMAP, Charts, interaktive Karte
│   ├── briefings/         13 Content Briefs als Markdown
│   ├── reporting/         konsolidiertes Dashboard
│   └── _archive/          gepinnte Snapshots vergangener Läufe
├── src/
│   ├── discover.py        Blog -> Seed Keywords (STUB)
│   ├── enrich.py          SV / KD / CPC / Priority
│   ├── cluster.py         Pipeline (clean, embed, UMAP, HDBSCAN, label, profile, charts, viz)
│   ├── cluster_viz.py     interaktive bilinguale Plotly Karte
│   ├── brief.py           Content Briefs via Claude API
│   └── report.py          konsolidiertes Reporting
└── tests/
```

## Tech Stack

| Schicht | Werkzeug | Warum |
|---|---|---|
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | mehrsprachig, läuft lokal ohne GPU, ausreichend für deutsche Keywords |
| Dimensionsreduktion | `umap-learn` | bessere lokale Struktur als PCA für density-based clustering |
| Clustering | `hdbscan` | wählt Clusteranzahl selbst, markiert Ausreißer als Rauschen statt Zwangszuordnung |
| Hierarchischer Vergleich | `scipy.cluster.hierarchy` (Ward) | transparente Granularitätskontrolle für Stakeholder, plus ARI als Gegenprobe |
| Visualisierung | `plotly` (interaktiv), `matplotlib` (PNG) | Plotly für die HTML Karte mit Klick und Sprache, matplotlib für die statischen Diagnose Charts |
| LLM Briefs | `anthropic` SDK, `claude-sonnet-4-6` | mit Prompt Caching auf System Block, ungefähr 90 Prozent Token Ersparnis bei wiederholten Läufen |
| Live Keyword Daten | DataForSEO Labs API | optional, Heuristik als Default |

## Was diese Pipeline bewusst nicht tut

- Keine direkte Anbindung an einen Search Console Account. Wenn echte Click und Impression Daten gewünscht sind, ist das eine Erweiterung des Discover Schritts.
- Kein Auto-Publishing der Briefs in ein CMS. Die Briefs sind Markdown, eine Anbindung an Sanity, Contentful oder WordPress wäre ein eigener Schritt.
- Kein Tracking der Pipeline Läufe in einer Datenbank. Für Produktion wäre ein einfacher SQLite Run-Log sinnvoll, aktuell sind Snapshots die Persistenz Schicht.

Diese Lücken sind dokumentiert in [`docs/decisions.md`](docs/decisions.md), nicht zufällig.

## Lizenz und Kontext

Persönliches Case Study Projekt im Rahmen einer Bewerbung als Revenue AI Architect bei zvoove. Nicht offiziell affiliated.
