# Methodology

Diese Datei erklärt die methodischen Entscheidungen in der Cluster Pipeline mit der Tiefe, die ein technischer Reviewer erwartet. Die [Übersicht](index.md) gibt den Einstieg, die [Case Study](case-study.md) verbindet die Methodik mit dem Geschäftsproblem, hier geht es um das technische Warum.

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
data/keywords.csv  ──▶  clean      ──▶  embed   ──▶  reduce   ──▶  cluster
                                                            │            │
                                                            ▼            ▼
                                                       umap_2d.npy   keywords_labeled.csv
                                                            │
                                                            ▼
                                          label  ──▶  profile  ──▶  charts  ──▶  viz
```

Acht Schritte, jeder einzeln re-runnbar. Die zentralen Hyperparameter sind als Konstanten oben in `src/cluster.py` festgehalten, damit Code und Doku übereinstimmen.

## 2. Embeddings: warum `paraphrase-multilingual-MiniLM-L12-v2`

Ein Embedding bildet einen Text auf einen Punkt in einem hochdimensionalen Raum ab, in dem semantisch ähnliche Texte nahe beieinander liegen. Beispiel: `lohnabrechnung software` und `payroll tool` haben fast identische Embedding-Vektoren, obwohl sie kein Wort teilen.

### Anforderungen

- **Mehrsprachig.** Das Keyword Set ist durchgehend Deutsch. Englische Modelle wie `all-MiniLM-L6-v2` handhaben deutsche Komposita schlechter (zum Beispiel werden `arbeitnehmerüberlassungsgesetz` und `aüg` ungleich gut zugeordnet).
- **Klein und schnell.** Das Modell muss auf einem normalen Laptop ohne GPU laufen, weil ein Bewerbungs-Reviewer die Pipeline nachvollziehen können soll.
- **Etabliert.** Sentence Transformers sind das Standardwerkzeug für semantische Ähnlichkeit. Kein experimentelles Setup, das in der Bewertung erklärungsbedürftig ist.

### Auswahl

| Modell | Größe | Mehrsprachig | Note |
|---|---|---|---|
| `all-MiniLM-L6-v2` | 80 MB | Englisch only | Verworfen, deutsche Morphologie schwach |
| `paraphrase-multilingual-MiniLM-L12-v2` | 120 MB | 50 Sprachen | **Gewählt.** Guter Kompromiss aus Qualität, Größe, Geschwindigkeit |
| `intfloat/multilingual-e5-large` | 2,3 GB | 100+ Sprachen | Wahrscheinlich höhere Qualität, in Backlog für Produktion |

Embedding Dimension: 384. Bei 504 Keywords also eine 504 × 384 Matrix, ungefähr 770 KB als float32.

Alle Embeddings werden mit `normalize_embeddings=True` erzeugt, damit Cosine Similarity gleichwertig zur Euclidean Distance auf der Einheitssphäre ist. Das vereinfacht die Wahl der Distanz-Metrik im Clustering.

## 3. Dimensionsreduktion: warum UMAP

384 Dimensionen sind für Density-based Clustering zu viel (Curse of Dimensionality, alle Distanzen werden ähnlich). Eine Reduktion auf 5 bis 10 Dimensionen ist Standard.

### UMAP, PCA, t-SNE im Vergleich

| Methode | Stärke | Schwäche | Eignung hier |
|---|---|---|---|
| PCA | Lineare Projektion auf maximale Varianz, schnell, deterministisch | Verliert lokale Struktur, weil sie nur global optimiert | Nicht ideal, weil Keyword Cluster lokal definiert sind |
| t-SNE | Sehr gute Visualisierung lokaler Cluster | Distanzen sind nicht interpretierbar (zwei nah aussehende Punkte sind nicht zwingend ähnlich), nicht deterministisch ohne aufwendige Initialisierung | Nicht ideal für nachgelagerte Analyse, weil Distanzen unbrauchbar |
| UMAP | Erhält lokale und globale Struktur, deterministisch mit `random_state`, distanzen sind lokal interpretierbar | Etwas langsamer als PCA, mehr Hyperparameter | **Gewählt.** Bestes Werkzeug für nachgelagertes Density-based Clustering |

### Zwei Reduktionen, nicht eine

```python
red5 = umap.UMAP(n_neighbors=15, n_components=5, metric="cosine", min_dist=0.0, random_state=42)
red2 = umap.UMAP(n_neighbors=15, n_components=2, metric="cosine", min_dist=0.1, random_state=42)
```

- **5D für Clustering.** Density-based Verfahren wie HDBSCAN profitieren von etwas mehr Dimensionen, um lokale Struktur zu erhalten. `min_dist=0.0` erlaubt Punkten, sich zu überlagern, was für Clustering wichtiger ist als visuelle Separation.
- **2D für Visualisierung.** Die Karte braucht genau zwei Dimensionen. `min_dist=0.1` zieht Punkte leicht auseinander, damit man sie unterscheiden kann.

`random_state=42` macht beide Reduktionen reproduzierbar zwischen Läufen.

## 4. Clustering: warum HDBSCAN

HDBSCAN (Hierarchical Density-Based Spatial Clustering of Applications with Noise) clustert nach Dichte: ein Cluster ist eine Region im Raum, in der Punkte dicht beieinander liegen. Punkte in dünn besiedelten Regionen werden als Rauschen markiert.

### Vergleich mit Alternativen

| Methode | Vorab-K nötig | Variable Dichte | Echte Ausreißer | Reproduzierbar |
|---|---|---|---|---|
| k-means | Ja, muss man raten | Nein, alle Cluster gleich groß | Nein, alles wird einem Cluster zugeordnet | Ja |
| Agglomerative (Ward) | Ja, muss man raten | Eingeschränkt | Nein | Ja |
| DBSCAN | Nein, aber `eps` ist global | Nein, eine Dichte für alle | Ja | Ja |
| **HDBSCAN** | **Nein** | **Ja** | **Ja** | **Ja** mit `random_state` |

HDBSCAN ist hier objektiv die beste Wahl, weil:

- **Keine Vorab-Anzahl.** Bei 504 Keywords zu raten, ob es 8 oder 13 oder 20 Cluster gibt, wäre eine implizite Annahme, die das Ergebnis verzerrt.
- **Variable Dichte.** Manche Themen sind eng (zvoove Marke: 32 Begriffe, alle teilen Wortteile), manche breit (Branche und Betrieb: 82 Begriffe, lose verbunden). Ein globaler `eps` wie bei DBSCAN würde entweder die engen Cluster überfeuern oder die breiten verlieren.
- **Echte Ausreißer.** 71 Keywords (14 Prozent) gehören zu keinem dichten Cluster. Das sind Begriffe wie `fachkräftemangel deutschland`, ein Top-Funnel Begriff ohne klare Nachbarn. K-means würde sie zwanghaft einem Cluster zuordnen und damit dessen Profil verwässern.

### Parameter Wahl

```python
HDBSCAN(min_cluster_size=15, min_samples=5,
        cluster_selection_method="eom", metric="euclidean")
```

- `min_cluster_size=15`: ein Cluster braucht mindestens 15 Punkte. Niedrigere Werte produzieren mehr Mikro-Cluster, höhere Werte verschmelzen Themen.
- `min_samples=5`: ein Punkt ist Kern-Punkt, wenn 5 Nachbarn in seinem Radius sind. Steuert, wie konservativ die Dichte-Schätzung ist.
- `cluster_selection_method="eom"`: Excess of Mass, wählt aus dem Cluster Hierarchie-Baum die persistentesten Cluster aus. Alternative `leaf` schneidet immer auf Blatt-Ebene, was tendenziell mehr und kleinere Cluster gibt.
- `metric="euclidean"`: passt zu normalisierten Embeddings nach UMAP.

## 5. Hyperparameter Sweep: die volle Tabelle

Die Wahl der HDBSCAN Parameter habe ich nicht geraten, sondern gemessen. Reproduzierbar mit `python -m src.cluster --step sweep`.

```
 mcs   ms method  n_clu  noise  noise%     sil
   5    1    eom     39     57   11.3%   0.543
   5    1   leaf     50     99   19.6%   0.478
   5    5    eom     23     59   11.7%   0.633
   5    5   leaf     30    160   31.7%   0.634
   8    1    eom     20     90   17.9%   0.589
   8    1   leaf     24    114   22.6%   0.554
   8    5    eom     13     71   14.1%   0.639
   8    5   leaf     17    157   31.2%   0.636
  10    1    eom     18     89   17.7%   0.583
  10    1   leaf     20    104   20.6%   0.563
  10    5    eom     13     71   14.1%   0.639
  10    5   leaf     14     81   16.1%   0.629
  12    1    eom     17     79   15.7%   0.585
  12    1   leaf     18     89   17.7%   0.583
  12    5    eom     13     71   14.1%   0.639
  12    5   leaf     14     81   16.1%   0.629
  15    1    eom     13     39    7.7%   0.586
  15    1   leaf     15     64   12.7%   0.563
  15    5    eom     13     71   14.1%   0.639  <-- gewählt
  15    5   leaf     13     71   14.1%   0.639
  20    1    eom      9     37    7.3%   0.620
  20    1   leaf     12     81   16.1%   0.564
  20    5    eom      8     76   15.1%   0.621
  20    5   leaf     11    101   20.0%   0.649
```

### Wie ich die Wahl getroffen habe

Drei Kriterien, in dieser Reihenfolge:

1. **Silhouette Score am Maximum oder nahe dran.** Die Top-5 Konfigurationen liegen alle bei 0,63 bis 0,65.
2. **Kommunikative Cluster-Anzahl.** 8 Cluster sind zu wenig, um Themen wie Recruiting und HR-Mid-Funnel zu trennen. 30 sind zu viele für eine Stakeholder-Tabelle. Die 13 Cluster bei mcs=15 / ms=5 sind genau im Sweet Spot.
3. **Robustheit.** Konfigurationen, bei denen `eom` und `leaf` das gleiche Ergebnis geben, sind weniger sensitiv für Rand-Entscheidungen. Bei mcs=15 / ms=5 stimmen `eom` und `leaf` exakt überein, was Vertrauen in die Stabilität gibt.

Anders ausgedrückt: mcs=15, ms=5, eom ist nicht das einzige sinnvolle Setup, aber es ist das, das ich am ehesten verteidigen kann. Bei mcs=8 / ms=5 / eom oder mcs=10 / ms=5 / eom hätte ich identische Ergebnisse bekommen, was wieder Robustheit bestätigt.

### Was nicht ausgewählt wurde und warum

- **mcs=20, ms=5, leaf (silhouette 0.649).** Hat den höchsten Silhouette Score, aber nur 11 Cluster. Verschmilzt zwei thematisch unterschiedliche Bereiche (Brand und SaaS Heads), was beim manuellen Spot Check sichtbar wird.
- **mcs=5, ms=1, eom (39 Cluster).** Zu viele Mikro-Cluster, die thematisch nicht mehr klar zusammenhalten. Silhouette ist niedrig (0.543).
- **mcs=5, ms=5, leaf (30 Cluster).** Hoher Noise Anteil (31,7 Prozent), bedeutet ein Drittel aller Keywords werden ausgeschlossen. Das ist methodisch akzeptabel, aber für einen Stakeholder-Bericht zu viel "weiß ich nicht".

## 6. Validierung

Drei Ebenen, die unabhängig voneinander Vertrauen aufbauen.

### 6.1 Silhouette Score

Misst, wie gut Cluster getrennt sind, von -1 bis +1.

| Setup | Silhouette |
|---|---|
| HDBSCAN ohne Rauschen | 0,639 |
| HDBSCAN inklusive Rauschen | 0,462 |

0,639 ist für reale Textdaten sehr gut. Werte über 0,5 gelten als belastbare Cluster.

Der Unterschied zwischen beiden Werten ist informativ: wenn das Rauschen tatsächlich Rauschen ist (also Punkte, die wirklich keinem Cluster zugehören), drückt es den Silhouette stark, weil es als pseudo-Cluster mitgemessen wird. 0,639 vs 0,462 zeigt, dass HDBSCAN die Rauschen-Klassifikation gut trifft.

### 6.2 ARI und NMI gegen die LLM Cluster

Adjusted Rand Index (ARI) und Normalized Mutual Information (NMI) messen, wie ähnlich zwei Cluster-Aufteilungen derselben Daten sind.

| Vergleich | ARI | NMI |
|---|---|---|
| HDBSCAN gegen LLM Cluster (ohne Rauschen) | 0,141 | 0,328 |

ARI ist konservativer als NMI, deshalb ARI < NMI normal.

Diese Werte sind nicht hoch, und das ist methodisch interessant. HDBSCAN findet andere Cluster Grenzen als die LLM Definition. Beide sind gültige Sichten:

- Die LLM Definition gruppiert nach **Geschäfts-Logik** (zvoove Produktbereiche).
- HDBSCAN gruppiert nach **semantischer Ähnlichkeit** im Embedding Raum.

Beispiel: Der LLM Cluster "Recruiting & Bewerbermanagement" wird von HDBSCAN aufgeteilt in "Recruiting & KI-Tools" und "HR-Mid-Funnel", weil die KI Tool Begriffe semantisch näher an "Software" liegen als an "Recruiting".

Das ist eine empirische Erkenntnis, die ohne diese Analyse nicht sichtbar wäre, und sie hat Konsequenzen für die Content Strategie: ein gemeinsamer Pillar für "Recruiting" wäre semantisch falsch zugeschnitten.

### 6.3 Hierarchischer Vergleich (Ward)

Zusätzlich rechne ich Ward Hierarchical Clustering auf den gleichen UMAP Daten, mit `k=8`, `k=10`, `k=12`. Ward minimiert die Varianz innerhalb der Cluster und produziert kompakte, klar getrennte Gruppen.

| k | Silhouette |
|---|---|
| 8 | 0,541 |
| 10 | 0,570 |
| 12 | 0,579 |

Ward erreicht 0,58 bei k=12, HDBSCAN liegt bei 0,639. HDBSCAN ist also etwas besser, aber nicht dramatisch. Der wichtigere Vorteil von HDBSCAN ist die Rauschen-Klasse: Ward muss alle 504 Keywords einem Cluster zuordnen, auch die 71 Ausreißer.

ARI HDBSCAN gegen Ward(k=10) auf den nicht-Rauschen Punkten: 0,754. Die beiden Methoden stimmen auf einem Großteil der Cluster-Zuordnungen überein, was Vertrauen in die Stabilität der gefundenen Struktur gibt. Wenn zwei methodisch unabhängige Verfahren zu ähnlichen Cluster-Grenzen kommen, ist das ein starkes Signal, dass die Struktur in den Daten real ist und nicht ein Algorithmus-Artefakt.

### 6.4 Manuelle Spot Checks

Pro Cluster habe ich die Top 10 Keywords gelesen und gegen das vergebene Label gegengeprüft:

- **11 von 13 Cluster sind eindeutig sauber.** Beispiel Cluster 0 (Factoring-Grundlagen): `factoring buchen`, `factoring erlaubnis`, `offenes factoring`, `echtes factoring`, `factoring kfw`. Klar ein einziges Thema.
- **Cluster 4 (Operative Anleitungen, gemischt) ist heterogen.** Enthält `aüg`, `bewerber finden`, `lohnabrechnung sage`, `indeed alternative`, `lohnabrechnung erstellen`. Drei Sub-Themen in einem Cluster: HR Wissen, Recruiting Tipps, Lohnabrechnung. HDBSCAN hat hier keine ausreichende Dichte gefunden, um sie zu trennen.
- **Cluster 13 (Branche & Betrieb, Sammelbecken) ist mit 82 Keywords der größte Cluster.** Niedrige Kohäsion. Kandidat für ein zweites HDBSCAN nur auf diesem Cluster, um Sub-Cluster zu finden.

Der manuelle Check ist subjektiv, aber notwendig, weil quantitative Maße wie Silhouette nicht alles erfassen. Insbesondere können hohe Silhouette Werte durch breite Cluster mit niedriger interner Kohäsion entstehen.

## 7. Reproduktion und Determinismus

Die Pipeline ist auf Reproduzierbarkeit ausgelegt:

- **`random_state=42`** in beiden UMAP Aufrufen.
- **HDBSCAN ist deterministisch** (kein Random Initialisierung).
- **Embeddings sind deterministisch** (Sentence Transformer in Inference Modus).
- **Heuristische Enrichment** ist deterministisch (SHA256 Hash des Keywords als Seed).

Ein zweiter Lauf mit identischer `data/keywords.csv` produziert byte-identische `embeddings.npy`, `umap_*.npy` und `keywords_labeled.csv`.

Reproduktion auf einem fremden Rechner:

```bash
git clone https://github.com/t1nak/seo-pipeline.git
cd seo-pipeline
pip install -r requirements.txt
python -m src.cluster --step all
```

Erwartetes Ergebnis: 13 Cluster, Silhouette 0,639, ARI 0,141.

## 8. Bekannte Schwächen

- **Embedding Modell ist nicht state of the art.** `paraphrase-multilingual-MiniLM-L12-v2` ist 2 Jahre alt. Aktuelle Modelle wie `intfloat/multilingual-e5-large` würden vermutlich bessere Cluster produzieren, sind aber 20-fach größer. In Backlog für Produktion.
- **UMAP `n_neighbors=15` ist nicht getunt.** Habe ich aus dem Default übernommen. Eine Sensitivitäts-Analyse über `n_neighbors=10/15/20/30` würde belegen, dass die Cluster-Struktur stabil ist (oder das Gegenteil zeigen).
- **HDBSCAN sieht nicht alle thematischen Beziehungen.** Cluster 4 (Operative Anleitungen, gemischt) ist heterogen, weil HDBSCAN bei niedriger Dichte zwischen Sub-Themen nicht trennen kann. Eine zweite Iteration mit anderen Embeddings oder mit hierarchischem Refinement innerhalb dieses Clusters wäre eine Verbesserung.
- **Cluster Labels sind manuell.** Skaliert nicht über 50 Cluster. Backlog Punkt: pro Cluster die Top 10 Keywords an Claude geben und automatisch ein Label generieren lassen.
- **Keine Sensitivität gegen das Keyword Set.** Wenn 50 neue Keywords hinzukommen, ändern sich Cluster Grenzen potentiell. Aktuell habe ich keinen Mechanismus, um die Stabilität zwischen Läufen zu messen. Vorschlag: Cluster Persistenz Score über Läufe hinweg tracken.

## 9. Lesetipps

- [Sentence Transformers Documentation](https://www.sbert.net/) für die Embedding Modelle
- [UMAP Original Paper](https://arxiv.org/abs/1802.03426) (McInnes, Healy, Melville 2018)
- [HDBSCAN Original Paper](https://link.springer.com/chapter/10.1007/978-3-642-37456-2_14) (Campello, Moulavi, Sander 2013)
- [hdbscan Python Library Docs](https://hdbscan.readthedocs.io/)
