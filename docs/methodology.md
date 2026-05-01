# Methodik

Diese Seite erklärt die methodischen Entscheidungen in der Cluster Pipeline mit technischer Tiefe. Die [Übersicht](index.md) gibt den Einstieg, die [Case Study](case-study.md) verbindet die Methodik mit dem Geschäftsproblem, hier geht es um das technische Warum.

## Begriffe kurz erklärt

| Begriff | Bedeutung |
|---|---|
| **Embedding** | Eine Liste von Zahlen (Vektor), die die Bedeutung eines Textes kodiert. Semantisch ähnliche Texte liegen im Vektorraum nahe beieinander. |
| **UMAP** | Ein Algorithmus, der hochdimensionale Vektoren auf wenige Dimensionen komprimiert und dabei die Nachbarschaftsstruktur erhält. |
| **HDBSCAN** | Ein Clustering-Algorithmus, der Gruppen anhand von Dichte erkennt und Punkte ohne klare Zugehörigkeit als Rauschen markiert. |
| **Silhouette Score** | Eine Zahl von -1 bis +1. Misst, wie gut jeder Punkt zu seinem eigenen Cluster passt verglichen mit dem nächstgelegenen anderen Cluster. Höher ist besser. |
| **ARI** | Adjusted Rand Index. Misst die Übereinstimmung zweier Cluster-Einteilungen. 0 bedeutet zufällig, 1 bedeutet identisch. Bestraft zufällige Übereinstimmungen stärker als NMI. |
| **NMI** | Normalized Mutual Information. Misst ebenfalls die Übereinstimmung zweier Einteilungen, reagiert aber weniger empfindlich auf Unterschiede in der Cluster-Anzahl. Deshalb ist NMI typischerweise höher als ARI für dieselben Daten. |

## Inhaltsübersicht

1. Pipeline auf einen Blick
2. Embeddings: warum dieses Modell
3. Dimensionsreduktion: warum UMAP
4. Clustering: warum HDBSCAN
5. Hyperparameter Sweep: die volle Tabelle
6. Validierung: Silhouette, ARI, NMI, manuelle Spot Checks
7. Reproduktion und Determinismus
8. Bekannte Schwächen der Methodik

## 1. Pipeline auf einen Blick

```
Entry-Point Optionen (austauschbar):
  ┌─ keywords.manual.csv      (LLM-erzeugte Liste, aktueller Demo-Lauf)
  ├─ Semrush Export (CSV)
  ├─ Ahrefs Export (CSV)
  ├─ DataForSEO API
  └─ Blog-Scrape (geplant, siehe Entscheidungen)
        │
        ▼
    discover ──▶ enrich ──▶ cluster ──▶ labels_llm ──▶ brief ──▶ report
                   │            │           │             │          │
                   ▼            ▼           ▼             ▼          ▼
              keywords.csv  profiles.csv cluster_      briefings/ reporting/
              SV · KD · CPC labeled.csv  labels.json   *.md       runs/<id>/
              priority                   (DE/EN)                  + index.html
```

Der **Entry Point** ist über die Konfiguration austauschbar. Im Demo-Lauf liest `discover` eine LLM-erzeugte Liste aus `keywords.manual.csv`. Produktiv kann derselbe Schritt einen Semrush- oder Ahrefs-Export laden, eine DataForSEO-Abfrage absetzen oder den zvoove-Blog scrapen. Die nachfolgenden Schritte sind quellunabhängig.

Sechs Schritte, jeder einzeln re-runnbar via `python pipeline.py --step <name>` bzw. `python -m src.labels_llm` für den Label-Schritt. Der `cluster`-Schritt enthält die internen Teilschritte (clean, embed, reduce, cluster, label, profile). `labels_llm` läuft danach als eigener Schritt und ersetzt die generischen Labels durch DE/EN-Labels aus einem Anthropic-Batch-Call (siehe [ADR-5](decisions.md#adr-5-llm-generierte-cluster-labels-pro-lauf-yaml-als-fallback)). Der `report`-Schritt erzeugt Charts, Cluster-Map und Dashboard und akzeptiert `--source <label>` und `--run-id <id>`, damit Läufe mit unterschiedlichen Entry Points im Reporting-Index nebeneinander sichtbar sind.

## 2. Embeddings: warum [`paraphrase-multilingual-MiniLM-L12-v2`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)

Ein Embedding bildet einen Text auf einen Punkt in einem hochdimensionalen Raum ab, in dem semantisch ähnliche Texte nahe beieinander liegen. Beispiel: `lohnabrechnung software` und `payroll tool` haben fast identische Embedding-Vektoren, obwohl sie kein Wort teilen.

### Anforderungen

- **Mehrsprachig.** Das Keyword Set ist durchgehend Deutsch. Englische Modelle wie [`all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) handhaben deutsche Komposita schlechter (zum Beispiel werden `arbeitnehmerüberlassungsgesetz` und `aüg` ungleich gut zugeordnet).
- **Klein und schnell.** Das Modell muss auf einem normalen Laptop ohne GPU laufen, damit die Pipeline lokal reproduzierbar bleibt.
- **Etabliert.** [Sentence Transformers](https://www.sbert.net/) sind das Standardwerkzeug für semantische Ähnlichkeit. Kein experimentelles Setup, das erklärungsbedürftig wäre.

### Auswahl

| Modell | Größe | Mehrsprachig | Note |
|---|---|---|---|
| [`all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | 80 MB | Englisch only | Verworfen, deutsche Morphologie schwach |
| [`paraphrase-multilingual-MiniLM-L12-v2`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) | 120 MB | 50 Sprachen | **Gewählt.** Guter Kompromiss aus Qualität, Größe, Geschwindigkeit |
| [`intfloat/multilingual-e5-large`](https://huggingface.co/intfloat/multilingual-e5-large) | 2,3 GB | 100+ Sprachen | Wahrscheinlich höhere Qualität, in Backlog für Produktion |

Embedding Dimension: 384. Bei 500 Keywords also eine 500 × 384 Matrix, ungefähr 770 KB als float32.

Alle Embeddings werden mit `normalize_embeddings=True` erzeugt. Das bedeutet: die Länge jedes Vektors wird auf 1 normiert, er liegt damit auf einer Einheitssphäre. Auf einer Einheitssphäre sind Cosine-Ähnlichkeit und euklidischer Abstand mathematisch äquivalent. Das vereinfacht die Wahl der Distanzmetrik im nachgelagerten Clustering, weil beide Maße dasselbe Ergebnis liefern.

## 3. Dimensionsreduktion: warum [UMAP](https://umap-learn.readthedocs.io/)

384 Dimensionen sind für Density-based Clustering zu viel ([Curse of Dimensionality](https://en.wikipedia.org/wiki/Curse_of_dimensionality): In hohen Dimensionen werden alle Abstände ähnlich groß, sodass Dichte nicht mehr sinnvoll messbar ist). Eine Reduktion auf 5 bis 10 Dimensionen ist Standard.

### UMAP, PCA, t-SNE im Vergleich

| Methode | Stärke | Schwäche | Eignung hier |
|---|---|---|---|
| PCA | Lineare Projektion auf maximale Varianz, schnell, deterministisch | Verliert lokale Struktur, weil sie nur global optimiert | Nicht ideal, weil Keyword Cluster lokal definiert sind |
| t-SNE | Sehr gute Visualisierung lokaler Cluster | Abstände sind nicht interpretierbar (zwei nah aussehende Punkte sind nicht zwingend ähnlich); nicht deterministisch ohne aufwendige Initialisierung | Nicht ideal für nachgelagerte Analyse |
| UMAP | Erhält lokale und globale Struktur, deterministisch mit `random_state`, Abstände sind lokal interpretierbar | Etwas langsamer als PCA, mehr Hyperparameter | **Gewählt.** Bestes Werkzeug für nachgelagertes Density-based Clustering |

### Zwei Reduktionen, nicht eine

```python
red5 = umap.UMAP(n_neighbors=15, n_components=5, metric="cosine", min_dist=0.0, random_state=42)
red2 = umap.UMAP(n_neighbors=15, n_components=2, metric="cosine", min_dist=0.1, random_state=42)
```

- **5D für Clustering.** Density-based Verfahren wie HDBSCAN profitieren von etwas mehr Dimensionen, um lokale Struktur zu erhalten. `min_dist=0.0` erlaubt Punkten, sich zu überlagern, was für Clustering wichtiger ist als visuelle Separation.
- **2D für Visualisierung.** Die Karte braucht genau zwei Dimensionen. `min_dist=0.1` zieht Punkte leicht auseinander, damit man sie auf der Karte unterscheiden kann.

`random_state=42` macht beide Reduktionen reproduzierbar zwischen Läufen.

## 4. Clustering: warum [HDBSCAN](https://hdbscan.readthedocs.io/)

[HDBSCAN](https://hdbscan.readthedocs.io/) (Hierarchical Density-Based Spatial Clustering of Applications with Noise) clustert nach Dichte: ein Cluster ist eine Region im Raum, in der Punkte dicht beieinander liegen. Punkte in dünn besiedelten Regionen werden als Rauschen markiert.

### Vergleich mit Alternativen

| Methode | Vorab-K nötig | Variable Dichte | Echte Ausreißer | Reproduzierbar |
|---|---|---|---|---|
| k-means | Ja, muss man raten | Nein, alle Cluster gleich groß | Nein, alles wird einem Cluster zugeordnet | Ja |
| Agglomerative (Ward) | Ja, muss man raten | Eingeschränkt | Nein | Ja |
| DBSCAN | Nein, aber `eps` ist global | Nein, eine Dichte für alle | Ja | Ja |
| **HDBSCAN** | **Nein** | **Ja** | **Ja** | **Ja** mit `random_state` |

HDBSCAN ist hier die beste Wahl, weil:

- **Keine Vorab-Anzahl.** Bei 500 Keywords zu raten, ob es 8 oder 10 oder 20 Cluster gibt, wäre eine implizite Annahme, die das Ergebnis verzerrt.
- **Variable Dichte.** Manche Themen sind eng (zvoove Marke: 32 Begriffe, alle teilen Wortteile), manche breit (Branche und Betrieb: 82 Begriffe, lose verbunden). Ein globaler `eps` wie bei DBSCAN würde entweder die engen Cluster überfeuern oder die breiten verlieren.
- **Echte Ausreißer.** 130 Keywords (ca. 26 Prozent) gehören zu keinem dichten Cluster. Das sind Begriffe wie `fachkräftemangel deutschland`, ein Top-Funnel Begriff ohne klare Nachbarn. k-means würde sie zwanghaft einem Cluster zuordnen und damit dessen Profil verwässern. Die Rauschrate ist beim aktuellen Default `leaf` höher als bei `eom` und ist eine bewusste Entscheidung für Brief-Granularität, siehe Abschnitt 5.

### Parameter Wahl

```python
HDBSCAN(min_cluster_size=15, min_samples=5,
        cluster_selection_method="leaf", metric="euclidean")
```

- `min_cluster_size=15`: ein Cluster braucht mindestens 15 Punkte. Niedrigere Werte produzieren mehr Mikro-Cluster, höhere Werte verschmelzen Themen.
- `min_samples=5`: ein Punkt gilt als Kern-Punkt, wenn mindestens 5 Nachbarn in seinem Radius sind. Höhere Werte machen die Dichte-Schätzung konservativer.
- `cluster_selection_method="leaf"`: schneidet den HDBSCAN-Hierarchiebaum auf Blatt-Ebene. Die Alternative `eom` (Excess of Mass) wählt die persistenteste Ebene und bevorzugt damit wenige stabile Cluster. `leaf` liefert hier feinere Aufteilungen, was für Content-Briefs handlungsfähiger ist (siehe Abschnitt 5).
- `metric="euclidean"`: passt zu normalisierten Embeddings nach UMAP.

## 5. Hyperparameter Sweep: die volle Tabelle

Die HDBSCAN Parameter wurden nicht geraten, sondern gemessen. Reproduzierbar mit `python -m src.cluster --step sweep`.

```
 mcs   ms method  n_clu  noise  noise%     sil
   5    1    eom     35     77   15.4%   0.546
   5    1   leaf     43    125   25.0%   0.535
   5    5    eom     25     62   12.4%   0.623
   5    5   leaf     32    181   36.2%   0.658
   8    1    eom     17     42    8.4%   0.579
   8    1   leaf     26    147   29.4%   0.498
   8    5    eom     16     82   16.4%   0.633
   8    5   leaf     18    144   28.8%   0.653
  10    1    eom     14     58   11.6%   0.603
  10    1   leaf     19    102   20.4%   0.566
  10    5    eom     13     72   14.4%   0.647
  10    5   leaf     14    120   24.0%   0.663
  12    1    eom     12     78   15.6%   0.620
  12    1   leaf     15    129   25.8%   0.625
  12    5    eom     10     40    8.0%   0.660
  12    5   leaf     13    130   26.0%   0.668
  15    1    eom     12     78   15.6%   0.620
  15    1   leaf     14    115   23.0%   0.625
  15    5    eom      7     12    2.4%   0.593
  15    5   leaf     13    130   26.0%   0.668  <-- gewählt
  20    1    eom      8     41    8.2%   0.613
  20    1   leaf     10    114   22.8%   0.576
  20    5    eom      6     27    5.4%   0.582
  20    5   leaf     10    112   22.4%   0.649
```

### Wie der zentrale Parameter gewählt wurde

Die Wahl fällt auf **`mcs=15, ms=5, leaf`**: 13 Cluster, 130 Noise-Punkte (26 Prozent), Silhouette 0,668. Die Begründung folgt aus drei Beobachtungen.

**1. Granularität schlägt Stabilität, wenn jeder Cluster ein Content-Brief wird.** Die `eom`-Spalte mit ms=5 produziert auf den aktuellen Daten zwar wenige stabile Cluster (10 bei mcs=12, 7 bei mcs=15), aber dabei entsteht ein Sammelcluster, der mehrere Sub-Themen vermischt (AÜG, Equal Pay, Höchstüberlassungsdauer, Debitorenmanagement). Ein einziger Brief darüber wäre zu breit, um redaktionell handlungsfähig zu sein. `leaf` bricht diesen Sammelcluster in feinere Sub-Themen auf, sodass ein Brief pro Cluster sinnvoll bleibt.

**2. mcs=15 ist die robuste `leaf`-Position.** Die `leaf`-Spalte mit ms=5 zeigt eine klare Tendenz: kleine mcs erzeugen viele kleine Cluster mit hohem Noise (mcs=5: 32 Cluster, 36 Prozent Noise), große mcs kollabieren auf wenige (mcs=20: 10 Cluster). `mcs=12, ms=5, leaf` und `mcs=15, ms=5, leaf` liefern auf der aktuellen Datenbasis dasselbe Ergebnis (13 Cluster, 130 Noise, Silhouette 0,668). `mcs=15` ist als Default gewählt, weil es bei einem leicht veränderten Datensatz robuster gegen das Aufsplitten in Mikro-Cluster ist.

**3. Noise als bewusste Designentscheidung.** Mit 26 Prozent Noise rauschen 130 von 500 Keywords aus den finalen Clustern raus. Das klingt nach Verlust, ist aber methodisch gewollt: HDBSCAN markiert Punkte als Noise (Cluster-Label `-1`), wenn sie keinem Cluster zuverlässig zugeordnet werden können. Diese Keywords ins nächste Cluster zu zwingen, würde die Cluster-Schärfe verwässern. Im Reporting werden Noise-Keywords als „Ausreißer" sichtbar gemacht, nicht versteckt, und können als Hinweis auf Themen dienen, die noch nicht genug Volumen für einen eigenen Cluster haben.

**Tradeoff bewusst gewählt.** Die Alternative `mcs=12, ms=5, eom` mit 10 Clustern und 8 Prozent Noise hat eine niedrigere Silhouette (0,660 vs 0,668), aber deutlich weniger Rauschen. Wer einen Forschungs-Report mit möglichst hoher Abdeckung braucht, sollte sie nehmen. Wer Content-Briefs pro Cluster produziert, gewinnt mit `leaf` drei zusätzliche Themen-Differenzierungen, die direkt in drei zusätzliche Briefs übersetzt werden können.

Die Wahl ist über `cluster_hdbscan_mcs` (Default 15) und `cluster_hdbscan_method` (Default leaf) bzw. die Environment-Variablen `PIPELINE_CLUSTER_HDBSCAN_MCS` / `PIPELINE_CLUSTER_HDBSCAN_METHOD` veränderbar, ohne Code-Änderung.

### Was nicht ausgewählt wurde und warum

- **mcs=12, ms=5, eom (10 Cluster, 8 Prozent Noise, sil 0,660).** Hohe Abdeckung, niedriges Rauschen. Verworfen, weil ein einziger Sammelcluster mehrere Sub-Themen mischt und die Briefe dadurch zu breit werden.
- **mcs=15, ms=5, eom (7 Cluster, 2,4 Prozent Noise).** Sehr saubere Cluster-Grenzen, aber 7 Cluster sind zu wenig für eine Content-Strategie auf 500 Keywords.
- **mcs=20, ms=5, leaf (10 Cluster, 22 Prozent Noise).** Weniger Cluster und ähnlicher Noise wie der gewählte Punkt. Verliert eine sinnvolle Themen-Differenzierung im Vergleich.
- **mcs=5, ms=5, eom (25 Cluster, sil 0,623).** Sehr feines Clustering, aber 25 Cluster sind operativ zu viel: zu wenig Differenzierung zwischen benachbarten Sub-Themen.
- **mcs=10/15, ms=1, eom (12 Cluster, 16 Prozent Noise).** Plausibler Kompromiss, aber `min_samples=1` ist sehr aggressiv und die Cluster-Grenzen sind weniger robust als mit ms=5.

## 6. Validierung

Die Cluster-Qualität wird auf drei unabhängigen Wegen geprüft.

### 6.1 [Silhouette Score](https://en.wikipedia.org/wiki/Silhouette_(clustering))

Der Silhouette Score misst pro Punkt, wie gut er in seinem eigenen Cluster sitzt verglichen mit dem nächsten anderen Cluster. Werte nahe +1 bedeuten: der Punkt gehört klar dazu. Werte nahe 0 liegen auf einer Cluster-Grenze. Negative Werte deuten auf Fehlzuordnung hin.

| Setup | Silhouette |
|---|---|
| HDBSCAN ohne Rauschen | 0,668 |
| HDBSCAN inklusive Rauschen | ~0,55 |

0,668 ist für reale Textdaten sehr gut. Werte über 0,5 gelten als belastbare Cluster-Trennung. Cross-Platform (lokal macOS gegen Ubuntu-CI) variiert der Silhouette-Score um wenige Hundertstel wegen unterschiedlicher BLAS-Implementierungen.

Der Unterschied zwischen beiden Werten ist informativ: wenn das Rauschen tatsächlich Rauschen ist (Punkte, die wirklich keinem Cluster zugehören), drückt es den Silhouette Score, weil es als Pseudo-Cluster mitgemessen wird.

### 6.2 ARI und NMI gegen die LLM Cluster

ARI (Adjusted Rand Index) und NMI (Normalized Mutual Information) messen beide, wie ähnlich zwei Cluster-Einteilungen derselben Daten sind. ARI bestraft zufällige Übereinstimmungen stärker als NMI; NMI misst gemeinsame Information ohne diese Strafe. Deshalb ist ARI bei realen Daten typischerweise kleiner als NMI.

| Vergleich | ARI | NMI |
|---|---|---|
| HDBSCAN gegen LLM Cluster (ohne Rauschen) | 0,193 | 0,372 |

Diese Werte sind nicht hoch, und das ist methodisch interessant. HDBSCAN findet andere Cluster-Grenzen als die LLM-Definition. Beide sind gültige Sichten:

- Die LLM-Definition gruppiert nach **Geschäfts-Logik** (zvoove Produktbereiche).
- HDBSCAN gruppiert nach **semantischer Ähnlichkeit** im Embedding-Raum.

Beispiel: Der ursprüngliche LLM Cluster „Recruiting & Bewerbermanagement" wird von HDBSCAN aufgeteilt in „KI-gestützte Recruiting-Automatisierung" und „HR- und Bewerbermanagementsoftware KMU", weil ATS- und SaaS-Begriffe semantisch näher an Software-Kategorien liegen als an Recruiting-Workflows.

Das ist eine empirische Erkenntnis, die ohne diese Analyse nicht sichtbar wäre, und sie hat Konsequenzen für die Content-Strategie: ein gemeinsamer Pillar für "Recruiting" wäre semantisch falsch zugeschnitten.

### 6.3 Hierarchischer Vergleich (Ward)

Als zweite unabhängige Methode rechne ich [Ward Hierarchical Clustering](https://en.wikipedia.org/wiki/Ward%27s_method) auf denselben UMAP-Daten mit `k=8`, `k=10`, `k=12`. Ward minimiert die Varianz innerhalb der Cluster und produziert kompakte, klar getrennte Gruppen.

| k | Silhouette |
|---|---|
| 8 | 0,552 |
| 10 | 0,562 |
| 12 | 0,590 |

Ward erreicht 0,590 bei k=12, HDBSCAN liegt bei 0,668. HDBSCAN ist klar besser. Der wichtigere Vorteil von HDBSCAN ist die Rauschen-Klasse: Ward muss alle 500 Keywords einem Cluster zuordnen, auch die 130 Ausreißer.

ARI HDBSCAN gegen Ward(k=10) auf den Nicht-Rauschen-Punkten: 0,786. Beide Methoden stimmen auf einer großen Mehrheit der Cluster-Zuordnungen überein. Die methodische Aussage: zwei unabhängige Verfahren finden ähnliche Cluster-Grenzen, das stärkt das Vertrauen in die zugrunde liegende Struktur.

### 6.4 Manuelle Spot Checks

Pro Cluster wurden die Top 10 Keywords gelesen und gegen das vergebene Label gegengeprüft (Cluster-IDs 0 bis 12).

- **11 von 13 Clustern sind eindeutig sauber.** Beispiel Cluster 0 (Factoring Geschäftsmodelle und Genehmigung): `factoring buchen`, `factoring erlaubnis`, `offenes factoring`, `echtes factoring`, `factoring kfw`. Klar ein einziges Thema. Beispiel Cluster 1 (Zeiterfassungs- und Zeitarbeitssoftware): `zeiterfassung software`, `mobile zeiterfassung`, `zeitarbeitssoftware`, `roi zeitarbeit software`. Klar Bottom-Funnel-Software-Begriffe.
- **Cluster 4 (Lohnabrechnung und Candidate Sourcing) ist heterogen.** Enthält `aüg`, `bewerber finden`, `lohnabrechnung sage`, `indeed alternative`. Mehrere Sub-Themen (Compliance, Recruiting, Lohn). HDBSCAN hat hier keine ausreichende Dichte gefunden, um sie zu trennen — empfohlene Bearbeitung: Top-Keywords einzeln statt Pillar.
- **Cluster 12 (Zeitarbeit Branchentrends und Einsatzplanung) hat einen breiten thematischen Bogen.** Mischt Trend-Themen mit operativen Begriffen. Brauchbar für Thought-Leadership-Inhalte, aber kein klarer Pillar-Kandidat ohne Sub-Editorial.

Der manuelle Check ist subjektiv, aber notwendig, weil quantitative Maße wie Silhouette nicht alles erfassen. Hohe Silhouette-Werte können durch breite Cluster mit niedriger interner Kohäsion entstehen.

## 7. Reproduktion und Determinismus

Die Pipeline ist auf Reproduzierbarkeit ausgelegt:

- **`random_state=42`** in beiden UMAP Aufrufen.
- **HDBSCAN ist deterministisch** (keine zufällige Initialisierung).
- **Embeddings sind deterministisch** (Sentence Transformer im Inference-Modus).
- **Heuristische Enrichment** ist deterministisch (SHA256 Hash des Keywords als Seed).

Ein zweiter Lauf mit identischer `data/keywords.csv` produziert auf derselben Plattform byte-identische `embeddings.npy`, `umap_*.npy` und `keywords_labeled.csv`. Cross-Platform (z.B. lokale macOS-Entwicklung gegen Ubuntu-CI) sind die Embeddings byte-identisch, die UMAP-Koordinaten weichen wegen unterschiedlicher BLAS/LAPACK-Implementierungen minimal ab. Die Cluster-Anzahl mit `mcs=15, leaf` bleibt über Plattformen hinweg robust, auch wenn einzelne Keywords je Plattform leicht zwischen Cluster und Noise springen können.

Reproduktion auf einem fremden Rechner:

```bash
git clone https://github.com/t1nak/seo-pipeline.git
cd seo-pipeline
pip install -r requirements.txt
python -m src.cluster --step all
```

Erwartetes Ergebnis: 13 Cluster, Silhouette ~0,67, ~26 Prozent Noise.

## 8. Bekannte Schwächen

- **Embedding Modell ist nicht state of the art.** `paraphrase-multilingual-MiniLM-L12-v2` ist zwei Jahre alt. Aktuelle Modelle wie `intfloat/multilingual-e5-large` würden vermutlich bessere Cluster produzieren, sind aber 20-fach größer. In Backlog für Produktion.
- **UMAP `n_neighbors=15` ist nicht getunt.** Aus dem Default übernommen. Eine Sensitivitäts-Analyse über `n_neighbors=10/15/20/30` würde belegen, dass die Cluster-Struktur stabil ist (oder das Gegenteil zeigen).
- **HDBSCAN sieht nicht alle thematischen Beziehungen.** Cluster 5 (Operative Anleitungen, gemischt) ist heterogen, weil HDBSCAN bei niedriger Dichte zwischen Sub-Themen nicht trennen kann. Eine zweite Iteration mit anderen Embeddings oder mit hierarchischem Refinement wäre eine Verbesserung.
- **Cluster-Labels sind LLM-generiert pro Lauf.** Vorteil: jede Hyperparameter-Variante bekommt sofort sinnvolle Labels. Nachteil: Wortwahl variiert leicht zwischen Läufen. Für stabile Long-Run-Reports kann die generierte JSON manuell gepinnt werden, siehe [ADR-5](decisions.md#adr-5-llm-generierte-cluster-labels-pro-lauf-yaml-als-fallback).
- **Keine Sensitivität gegen das Keyword Set.** Wenn 50 neue Keywords hinzukommen, ändern sich Cluster-Grenzen potentiell. Aktuell gibt es keinen Mechanismus, um die Stabilität zwischen Läufen zu messen. Vorschlag: Cluster-Persistenz-Score über Läufe hinweg tracken.

## 9. Lesetipps

- [Sentence Transformers Documentation](https://www.sbert.net/) für die Embedding Modelle
- [UMAP Original Paper](https://arxiv.org/abs/1802.03426) (McInnes, Healy, Melville 2018)
- [HDBSCAN Original Paper](https://link.springer.com/chapter/10.1007/978-3-642-37456-2_14) (Campello, Moulavi, Sander 2013)
- [hdbscan Python Library Docs](https://hdbscan.readthedocs.io/)
