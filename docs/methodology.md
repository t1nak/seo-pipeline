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
              priority      (incl. soft- (DE/EN)                  + index.html
                            assignment)
```

Der **Entry Point** ist über die Konfiguration austauschbar. Im Demo-Lauf liest `discover` eine LLM-erzeugte Liste aus `keywords.manual.csv`. Produktiv kann derselbe Schritt einen Semrush- oder Ahrefs-Export laden, eine DataForSEO-Abfrage absetzen oder den zvoove-Blog scrapen. Die nachfolgenden Schritte sind quellunabhängig.

Sechs Schritte, jeder einzeln re-runnbar via `python pipeline.py --step <name>` bzw. `python -m src.labels_llm` für den Label-Schritt. Der `cluster`-Schritt enthält die internen Teilschritte clean → embed → reduce → cluster → assign_noise → label → profile. `assign_noise` ordnet jedes HDBSCAN-Noise-Keyword seinem nächsten Cluster-Centroid im 5D-UMAP-Raum zu (siehe [ADR-15](decisions.md#adr-15-soft-assignment-fur-noise-keywords)) und markiert die Zuordnung in `noise_assigned: bool`. `labels_llm` ersetzt die generischen Labels durch DE/EN-Labels aus einem Anthropic-Batch-Call ([ADR-5](decisions.md#adr-5-llm-generierte-cluster-labels-pro-lauf-yaml-als-fallback)). Der `report`-Schritt erzeugt Charts, Cluster-Map und Dashboard.

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
- **Echte Ausreißer.** Mit dem aktuellen Default `mcs=10, eom` markiert HDBSCAN 72 Keywords (14 Prozent) als Noise. Das sind Begriffe wie `fachkräftemangel deutschland`, ein Top-Funnel-Begriff ohne klare Nachbarn. k-means würde sie zwanghaft einem Cluster zuordnen und damit dessen Profil verwässern. Operativ wollen wir aber jedes Keyword in einem Pillar haben — das löst der Soft-Assignment-Schritt (Abschnitt 5).

### Parameter Wahl

```python
HDBSCAN(min_cluster_size=10, min_samples=5,
        cluster_selection_method="eom", metric="euclidean")
```

- `min_cluster_size=10`: ein Cluster braucht mindestens 10 Punkte. Niedrigere Werte produzieren mehr Mikro-Cluster, höhere Werte verschmelzen Themen.
- `min_samples=5`: ein Punkt gilt als Kern-Punkt, wenn mindestens 5 Nachbarn in seinem Radius sind. Höhere Werte machen die Dichte-Schätzung konservativer.
- `cluster_selection_method="eom"`: Excess of Mass — wählt die persistenteste Ebene des HDBSCAN-Hierarchiebaums und liefert damit stabile, dichte Cluster. Die Alternative `leaf` schneidet auf Blatt-Ebene und liefert feinere Aufteilungen, hat aber bei dieser Datenbasis eine Rauschrate von 26 Prozent. `eom` mit `mcs=10` produziert bei vergleichbarer Cluster-Anzahl (13 vs. 13) deutlich weniger Noise (14 Prozent statt 26), siehe Abschnitt 5.
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
  10    5    eom     13     72   14.4%   0.647  <-- gewählt
  10    5   leaf     14    120   24.0%   0.663
  12    1    eom     12     78   15.6%   0.620
  12    1   leaf     15    129   25.8%   0.625
  12    5    eom     10     40    8.0%   0.660
  12    5   leaf     13    130   26.0%   0.668
  15    1    eom     12     78   15.6%   0.620
  15    1   leaf     14    115   23.0%   0.625
  15    5    eom      7     12    2.4%   0.593
  15    5   leaf     13    130   26.0%   0.668
  20    1    eom      8     41    8.2%   0.613
  20    1   leaf     10    114   22.8%   0.576
  20    5    eom      6     27    5.4%   0.582
  20    5   leaf     10    112   22.4%   0.649
```

### Wie der zentrale Parameter gewählt wurde

Die Wahl fällt auf **`mcs=10, ms=5, eom`**: 13 Cluster, 72 Noise-Punkte (14 Prozent), Silhouette 0,647. Diese 72 Noise-Keywords werden anschließend per Soft-Assignment ihrem nächsten Cluster zugeordnet (siehe Abschnitt 5.1). Endzustand: 13 Cluster, 500 Keywords, 0 Outlier. Die Begründung folgt aus vier Beobachtungen.

**1. Granularität schlägt Konsolidierung, wenn jeder Cluster ein Content-Brief wird.** Die `eom`-Spalte mit `mcs=12` würde nur 10 Cluster liefern, dabei entsteht aber ein Sammelcluster mit 188 Keywords, der AÜG, Equal Pay, Höchstüberlassungsdauer und Debitorenmanagement vermischt. Ein einziger Brief darüber wäre redaktionell unbearbeitbar. `mcs=10` bricht diese Themen in vier separate Cluster (Cluster 5: Markt und Regulierung, Cluster 8: Liquidität und Equal Pay, Cluster 11: AÜG-Recht, Cluster 12: Sammelthemen Software/Finanzierung), von denen drei klar als Pillar-Themen taugen.

**2. `eom` schlägt `leaf` bei der Rauschrate.** Auf der aktuellen Datenbasis liefern beide Methoden bei `mcs=10` bzw. `mcs=15` jeweils 13 Cluster. Der Unterschied: `eom` mit `mcs=10` produziert 14 Prozent Noise (72 Keywords), `leaf` mit `mcs=15` 26 Prozent (130 Keywords). 58 zusätzliche Keywords als Outlier zu markieren — darunter hochvolumige wie `dokumentenmanagement software` (5.000 SV) — ist operativ nicht tragbar. `eom` ist hier die robustere Wahl.

**3. Soft-Assignment als zweiter Schritt schließt die Lücke ohne Cluster-Distortion.** Anstatt die HDBSCAN-Parameter so weit zu drehen, bis kein Noise mehr entsteht (was die Cluster-Reinheit zerstören würde), wird ein zusätzlicher Schritt nachgelagert: jedes Noise-Keyword wird seinem nächsten Cluster-Centroid zugeordnet. Bei `mcs=10, eom` sind das nur 72 Punkte, die sich gleichmäßig über die Cluster verteilen — keine neuen Sammelcluster entstehen. Bei `mcs=15, leaf` mit 130 Noise hätte ein einzelner Cluster 43 Keywords absorbiert, was operativ nicht akzeptabel war.

**4. Validierung über Silhouette und Ward-Vergleich.** HDBSCAN mit `mcs=10, eom` erreicht eine Silhouette von 0,647 auf den 428 HDBSCAN-Kern-Keywords (vor Soft-Assignment). Ward Hierarchical bei k=12 erreicht 0,590. Der ARI zwischen beiden Methoden ist 0,811 — sehr hohe Übereinstimmung. Beide unabhängige Verfahren finden ähnliche Strukturen, das stärkt das Vertrauen in die Cluster-Grenzen.

Die Wahl ist über `cluster_hdbscan_mcs` (Default 10), `cluster_hdbscan_method` (Default eom) bzw. die Environment-Variablen `PIPELINE_CLUSTER_HDBSCAN_MCS` / `PIPELINE_CLUSTER_HDBSCAN_METHOD` veränderbar, ohne Code-Änderung.

### Was nicht ausgewählt wurde und warum

- **mcs=12, ms=5, eom (10 Cluster, 8 Prozent Noise, sil 0,660).** Statistisch die sauberste Variante. Verworfen, weil der größte Cluster mit 188 Keywords AÜG, Equal Pay, Debitorenmanagement und Höchstüberlassungsdauer mischt — vier eigenständige Pillar-Themen in einem Bucket, redaktionell unbearbeitbar.
- **mcs=15, ms=5, leaf (13 Cluster, 26 Prozent Noise, sil 0,668).** Höchste Silhouette und gleiche Cluster-Anzahl wie der gewählte Punkt. Verworfen wegen 130 Noise-Keywords — darunter hochvolumige wie `dokumentenmanagement software` (5.000 SV), die in einem Content-Plan nicht ungeparkt sein dürfen.
- **mcs=15, ms=5, eom (7 Cluster, 2,4 Prozent Noise).** Sehr saubere Cluster-Grenzen, aber 7 Cluster sind zu wenig für eine differenzierte Content-Strategie auf 500 Keywords.
- **mcs=5, ms=5, eom (25 Cluster, 12 Prozent Noise, sil 0,623).** Sehr feines Clustering, aber 25 Cluster sind operativ zu viel: zu wenig Differenzierung zwischen benachbarten Sub-Themen, zu hoher Brief-Aufwand pro Lauf.
- **Ward Hierarchical (k=13).** Würde alle 500 Keywords zwanghaft zuordnen ohne separate Noise-Klasse. Verworfen, weil HDBSCANs Silhouette deutlich höher ist (0,647 vs 0,590) und HDBSCAN datengetriebene Cluster-Anzahl liefert statt einer geratenen `k`.

### 5.1 Soft-Assignment der Noise-Keywords

HDBSCAN-Default (`assign_noise=True` im Pipeline-Schritt) ordnet jedes als Noise markierte Keyword nachträglich seinem nächsten Cluster-Centroid im 5D-UMAP-Raum zu. Mathematisch: für jeden Noise-Punkt `p` und Cluster-Centroid `c_i` (gemittelt über alle Kern-Keywords des Clusters) wird `argmin_i ||p - c_i||_2` berechnet und `p` dem Argmin-Cluster zugewiesen. Die ursprüngliche Noise-Eigenschaft bleibt in der Spalte `noise_assigned: bool` erhalten, sodass Reporting und Cluster-Map die Rand-Keywords optional anders darstellen können.

**Verteilung der 72 Soft-Assignments im aktuellen Lauf:**
`c3+1, c4+4, c5+10, c6+14, c7+4, c8+19, c9+1, c10+9, c11+6, c12+4`

Der größte Empfänger (Cluster 8 mit +19 Keywords, +56 Prozent zur ursprünglichen Größe) absorbiert die Equal-Pay/Liquiditäts-Rand-Keywords, was thematisch zur Cluster-Identität passt. Cluster 12 (Sammelthemen) bekommt nur +4 — die Soft-Assignment macht ihn nicht „noch heterogener". Insgesamt verteilen sich die 72 Punkte gleichmäßig genug, um keine neuen Sammelcluster zu erzeugen.

**Auswirkung auf die Silhouette.** Die Silhouette auf den 428 HDBSCAN-Kern-Keywords beträgt 0,647. Inklusive der 72 Soft-Assigned-Keywords sinkt sie auf 0,570 — erwartet, weil Rand-Keywords per Definition näher an einer Cluster-Grenze liegen. Beide Werte sind in der Validierungs-Sektion dokumentiert.

**Methodisch standardkonform.** Soft-Assignment ist die Standardlösung für Density-basierte Algorithmen mit operativer Vollabdeckung. `hdbscan` selbst bietet `approximate_predict()` und `all_points_membership_vectors()` als ähnliche Mechanismen. Hier ist es bewusst als einfache Centroid-Distance implementiert (`src/cluster.py:step_assign_noise`), damit das Verfahren in 30 Zeilen Code transparent nachvollziehbar bleibt.

## 6. Validierung

Die Cluster-Qualität wird auf drei unabhängigen Wegen geprüft.

### 6.1 [Silhouette Score](https://en.wikipedia.org/wiki/Silhouette_(clustering))

Der Silhouette Score misst pro Punkt, wie gut er in seinem eigenen Cluster sitzt verglichen mit dem nächsten anderen Cluster. Werte nahe +1 bedeuten: der Punkt gehört klar dazu. Werte nahe 0 liegen auf einer Cluster-Grenze. Negative Werte deuten auf Fehlzuordnung hin.

| Setup | Silhouette |
|---|---|
| HDBSCAN-Kern (428 Keywords, vor Soft-Assignment) | 0,647 |
| Alle 500 (nach Soft-Assignment) | 0,570 |
| Ward Hierarchical k=12 (Vergleich) | 0,590 |

0,647 ist für reale Textdaten sehr gut. Werte über 0,5 gelten als belastbare Cluster-Trennung. Der Drop auf 0,570 nach Soft-Assignment ist erwartet: die 72 Rand-Keywords liegen per Definition näher an einer Cluster-Grenze, ihre Silhouette ist niedriger als die der Kern-Keywords. Cross-Platform (lokal macOS gegen Ubuntu-CI) variiert der Score um wenige Hundertstel wegen unterschiedlicher BLAS-Implementierungen.

### 6.2 ARI und NMI gegen die LLM Cluster

ARI (Adjusted Rand Index) und NMI (Normalized Mutual Information) messen beide, wie ähnlich zwei Cluster-Einteilungen derselben Daten sind. ARI bestraft zufällige Übereinstimmungen stärker als NMI; NMI misst gemeinsame Information ohne diese Strafe. Deshalb ist ARI bei realen Daten typischerweise kleiner als NMI.

| Vergleich | ARI | NMI |
|---|---|---|
| HDBSCAN gegen LLM Cluster (HDBSCAN-Kern, vor Soft-Assignment) | 0,143 | 0,342 |

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

Ward erreicht 0,590 bei k=12, HDBSCAN liegt auf den Kern-Punkten bei 0,647. HDBSCAN ist klar besser. Der wichtigere Vorteil von HDBSCAN: das Verfahren findet datengetrieben 13 Cluster ohne Vorgabe-`k` und markiert Rand-Keywords explizit als Noise, die wir dann kontrolliert per Soft-Assignment integrieren.

ARI HDBSCAN gegen Ward(k=10) auf den HDBSCAN-Kern-Keywords: 0,859. Inklusive Soft-Assignment auf alle 500: 0,811. In beiden Fällen sehr hohe Übereinstimmung — zwei mathematisch unabhängige Verfahren finden im Wesentlichen dieselbe Struktur, das stärkt das Vertrauen in die Cluster-Grenzen.

### 6.4 Manuelle Spot Checks

Pro Cluster wurden die Top 10 Keywords gelesen und gegen das LLM-generierte Label gegengeprüft (Cluster-IDs 0 bis 12).

- **11 von 13 Clustern sind eindeutig sauber.** Beispiel Cluster 0 (Factoring Buchhaltung und Genehmigung): `factoring buchen`, `factoring erlaubnis`, `offenes factoring`, `echtes factoring`, `factoring kfw`. Klar ein einziges Thema. Beispiel Cluster 1 (Zeiterfassung und Zeitarbeitssoftware): `zeiterfassung software`, `mobile zeiterfassung`, `zeitarbeitssoftware`, `roi zeitarbeit software`. Klar Bottom-Funnel-Software-Begriffe.
- **Cluster 4 (Sammelthemen Lohnabrechnung und Recruiting) ist vom LLM transparent als „Sammelthemen" markiert.** Enthält `aüg`, `bewerber finden`, `lohnabrechnung sage`, `indeed alternative`, `offboarding prozess` — drei Sub-Themen (Compliance, Recruiting, Lohn). HDBSCAN hat hier keine ausreichende Dichte gefunden, um sie zu trennen — empfohlene Bearbeitung: Top-Keywords einzeln statt Pillar.
- **Cluster 12 (Sammelthemen Zeitarbeit Software und Finanzierung) ist mit 97 Keywords der größte Cluster.** Bündelt „Zeitarbeit + X" Kombinationen aus Software, Factoring, CRM, Lohn und Branchen-Trends. Vom LLM transparent als „Sammelthemen" gelabelt. Empfohlen: Sub-Clustering vor Bearbeitung (zweiter HDBSCAN-Lauf nur auf diesem Cluster), siehe `src/subcluster.py`.

Beide markierten Sammel-Cluster bleiben sichtbar als solche, statt durch andere Hyperparameter künstlich aufgespalten zu werden — das wäre eine Verschleierung der zugrunde liegenden Datendichte.

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

Erwartetes Ergebnis: 13 Cluster, Silhouette ~0,65 auf den HDBSCAN-Kern-Keywords, 14 Prozent Pre-Assignment-Noise → 0 Prozent Outlier nach Soft-Assignment.

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
