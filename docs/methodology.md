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
keywords.manual.csv
        │
        ▼
    discover ──▶ enrich ──▶ cluster ──▶ brief ──▶ report
                   │            │          │          │
                   ▼            ▼          ▼          ▼
              keywords.csv  cluster_map briefings/ reporting/
              SV · KD · CPC charts/     *.md      index.html
              priority       profiles.csv
```

Fünf Schritte, jeder einzeln re-runnbar via `python pipeline.py --step <name>`. Der `cluster`-Schritt enthält acht interne Teilschritte (clean, embed, reduce, cluster, label, profile, charts, viz). Die zentralen Hyperparameter stehen als Konstanten in `src/cluster.py`, damit Code und Doku übereinstimmen.

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
- **Echte Ausreißer.** 38 bis 40 Keywords (ca. 8 Prozent) gehören zu keinem dichten Cluster. Das sind Begriffe wie `fachkräftemangel deutschland`, ein Top-Funnel Begriff ohne klare Nachbarn. k-means würde sie zwanghaft einem Cluster zuordnen und damit dessen Profil verwässern.

### Parameter Wahl

```python
HDBSCAN(min_cluster_size=15, min_samples=5,
        cluster_selection_method="eom", metric="euclidean")
```

- `min_cluster_size=15`: ein Cluster braucht mindestens 15 Punkte. Niedrigere Werte produzieren mehr Mikro-Cluster, höhere Werte verschmelzen Themen.
- `min_samples=5`: ein Punkt gilt als Kern-Punkt, wenn mindestens 5 Nachbarn in seinem Radius sind. Höhere Werte machen die Dichte-Schätzung konservativer.
- `cluster_selection_method="eom"`: Excess of Mass. HDBSCAN baut intern einen Hierarchiebaum aller möglichen Cluster und wählt die Ebene, auf der die Cluster am längsten existieren. Das bevorzugt stabile, persistente Gruppen. Die Alternative `leaf` schneidet immer auf Blatt-Ebene, was tendenziell mehr und kleinere Cluster gibt.
- `metric="euclidean"`: passt zu normalisierten Embeddings nach UMAP.

## 5. Hyperparameter Sweep: die volle Tabelle

Die HDBSCAN Parameter wurden nicht geraten, sondern gemessen. Reproduzierbar mit `python -m src.cluster --step sweep`.

```
 mcs   ms method  n_clu  noise  noise%     sil
   5    1    eom     36     81   16.2%   0.570
   5    1   leaf     41    125   25.0%   0.551
   5    5    eom     16     32    6.4%   0.671
   5    5   leaf     29    181   36.2%   0.648
   8    1    eom     16     30    6.0%   0.660
   8    1   leaf     26    116   23.2%   0.588
   8    5    eom     13     37    7.4%   0.668
   8    5   leaf     20    153   30.6%   0.624
  10    1    eom     10     15    3.0%   0.651
  10    1   leaf     21    106   21.2%   0.568
  10    5    eom     10     38    7.6%   0.672
  10    5   leaf     15    149   29.8%   0.636
  12    1    eom     10     15    3.0%   0.651
  12    1   leaf     18    104   20.8%   0.575
  12    5    eom     10     38    7.6%   0.672  <-- gewählt
  12    5   leaf     13    150   30.0%   0.647
  15    1    eom     10     15    3.0%   0.651
  15    1   leaf     15    103   20.6%   0.595
  15    5    eom     10     38    7.6%   0.672
  15    5   leaf     12    100   20.0%   0.642
  20    1    eom      9     30    6.0%   0.642
  20    1   leaf     11    120   24.0%   0.593
  20    5    eom      8     34    6.8%   0.631
  20    5   leaf      9    115   23.0%   0.604
```

### Wie der zentrale Parameter gewählt wurde

Die Wahl fällt auf **`mcs=12, ms=5, eom`**. Dieser Parameter ist die wichtigste Stellschraube der Cluster-Pipeline. Die Begründung folgt aus drei Beobachtungen.

**1. Plateau statt Punkt-Optimum.** Die Sweep-Tabelle zeigt, dass mcs ∈ {10, 12, 15} mit ms=5 / eom **identische** Aufteilungen liefern: 10 Cluster, 38 Rauschen-Punkte, Silhouette 0,672. Das ist keine einzelne optimale Einstellung, sondern eine Äquivalenzklasse aus drei Konfigurationen.

**2. Innerhalb des Plateaus ist die Mitte stabiler als der Rand.** Wenn sich die Eingabe-Geometrie leicht verschiebt (andere Library-Versionen, andere CPU-Architektur, andere BLAS-Implementierung), kann ein Wert am Rand der Plateau-Klasse aus der Klasse fallen. Ein Wert in der Mitte hat Puffer in beide Richtungen. mcs=12 ist die mittlere Position der Plateau-Klasse.

**3. Empirisch falsifizierbar.** Beim Wechsel von der lokalen Entwicklungsumgebung (macOS) in eine Cloud-CI (Ubuntu) zeigt sich genau dieser Unterschied: mcs=15 fällt cross-platform auf 7 Cluster ab (Plateau-Rand erreicht), mcs=12 reproduziert konsistent 10 Cluster. UMAP ist mit `random_state=42` deterministisch innerhalb derselben Plattform und Library-Version, aber Cross-Platform-Identität ist nicht garantiert. Die Plateau-Mitte ist gegen diese Drift versichert.

**Nicht-Argumente, die verworfen wurden.** "Konservativster Wert auf dem Plateau" (also höchstes mcs) ist ein Tiebreaker ohne empirischen Wert. Innerhalb der Äquivalenzklasse sind alle Werte gleichwertig. Konservativ am Rand hilft erst dann, wenn die Klasse garantiert stabil bleibt. Diese Garantie hatte der ursprüngliche Lauf nicht.

**Zusammenfassung.** mcs=12 liegt methodisch in der vom Sweep identifizierten Äquivalenzklasse und ist operativ die robusteste Position gegenüber kleinen Geometrie-Verschiebungen. Die Wahl ist über den Konfigurations-Setting `cluster_hdbscan_mcs` (Default 12) bzw. die Environment-Variable `PIPELINE_CLUSTER_HDBSCAN_MCS` veränderbar, ohne Code-Änderung.

### Was nicht ausgewählt wurde und warum

- **mcs=5, ms=5, eom (16 Cluster, sil 0,671).** Sehr nahe am Maximum, aber 16 Cluster sind für das Stakeholder-Reporting zu fein. Sub-Themen würden zerfasern.
- **mcs=5, ms=1, eom (36 Cluster).** Viele Mikro-Cluster ohne klaren thematischen Zusammenhalt. Silhouette ist niedriger (0,570).
- **mcs=5, ms=5, leaf (29 Cluster, 36 Prozent Rauschen).** Mehr als ein Drittel aller Keywords werden ausgeschlossen. Methodisch akzeptabel, aber für einen Stakeholder-Bericht zu viel "weiß ich nicht".
- **mcs=10/12/15 ms=1 eom (10 Cluster, 3 Prozent Rauschen, sil 0,651).** Niedrigeres Rauschen klingt verlockend, aber `min_samples=1` ist sehr aggressiv und die Cluster-Grenzen sind weniger robust als mit ms=5.

## 6. Validierung

Die Cluster-Qualität wird auf drei unabhängigen Wegen geprüft.

### 6.1 [Silhouette Score](https://en.wikipedia.org/wiki/Silhouette_(clustering))

Der Silhouette Score misst pro Punkt, wie gut er in seinem eigenen Cluster sitzt verglichen mit dem nächsten anderen Cluster. Werte nahe +1 bedeuten: der Punkt gehört klar dazu. Werte nahe 0 liegen auf einer Cluster-Grenze. Negative Werte deuten auf Fehlzuordnung hin.

| Setup | Silhouette (lokal) | Silhouette (CI Ubuntu) |
|---|---|---|
| HDBSCAN ohne Rauschen | 0,672 | ~0,67 (geringfügig variabel je Plattform) |
| HDBSCAN inklusive Rauschen | 0,592 | ~0,59 |

0,672 ist für reale Textdaten sehr gut. Werte über 0,5 gelten als belastbare Cluster-Trennung.

Der Unterschied zwischen beiden Werten ist informativ: wenn das Rauschen tatsächlich Rauschen ist (Punkte, die wirklich keinem Cluster zugehören), drückt es den Silhouette Score, weil es als Pseudo-Cluster mitgemessen wird. ~0,67 vs ~0,59 zeigt, dass HDBSCAN die Rauschen-Klassifikation gut trifft.

### 6.2 ARI und NMI gegen die LLM Cluster

ARI (Adjusted Rand Index) und NMI (Normalized Mutual Information) messen beide, wie ähnlich zwei Cluster-Einteilungen derselben Daten sind. ARI bestraft zufällige Übereinstimmungen stärker als NMI; NMI misst gemeinsame Information ohne diese Strafe. Deshalb ist ARI bei realen Daten typischerweise kleiner als NMI.

| Vergleich | ARI | NMI |
|---|---|---|
| HDBSCAN gegen LLM Cluster (ohne Rauschen) | 0,113 | 0,321 |

Diese Werte sind nicht hoch, und das ist methodisch interessant. HDBSCAN findet andere Cluster-Grenzen als die LLM-Definition. Beide sind gültige Sichten:

- Die LLM-Definition gruppiert nach **Geschäfts-Logik** (zvoove Produktbereiche).
- HDBSCAN gruppiert nach **semantischer Ähnlichkeit** im Embedding-Raum.

Beispiel: Der ursprüngliche LLM Cluster "Recruiting & Bewerbermanagement" wird von HDBSCAN aufgeteilt in "Recruiting & KI-Tools" und "HR-Mid-Funnel", weil die KI-Tool-Begriffe semantisch näher an "Software" liegen als an "Recruiting".

Das ist eine empirische Erkenntnis, die ohne diese Analyse nicht sichtbar wäre, und sie hat Konsequenzen für die Content-Strategie: ein gemeinsamer Pillar für "Recruiting" wäre semantisch falsch zugeschnitten.

### 6.3 Hierarchischer Vergleich (Ward)

Als zweite unabhängige Methode rechne ich [Ward Hierarchical Clustering](https://en.wikipedia.org/wiki/Ward%27s_method) auf denselben UMAP-Daten mit `k=8`, `k=10`, `k=12`. Ward minimiert die Varianz innerhalb der Cluster und produziert kompakte, klar getrennte Gruppen.

| k | Silhouette |
|---|---|
| 8 | 0,520 |
| 10 | 0,531 |
| 12 | 0,579 |

Ward erreicht 0,579 bei k=12, HDBSCAN liegt bei 0,672. HDBSCAN ist klar besser. Der wichtigere Vorteil von HDBSCAN ist die Rauschen-Klasse: Ward muss alle 500 Keywords einem Cluster zuordnen, auch die 38 bis 40 Ausreißer.

ARI HDBSCAN gegen Ward(k=10) auf den Nicht-Rauschen-Punkten: 0,565. Beide Methoden stimmen auf mehr als der Hälfte der Cluster-Zuordnungen überein. Das liegt am großen Catch-all Cluster (Cluster 1 mit 189 Keywords), den Ward feiner aufteilt als HDBSCAN bei dieser Konfiguration. Die methodische Aussage bleibt: zwei unabhängige Verfahren finden ähnliche Cluster-Grenzen, das stärkt das Vertrauen in die zugrunde liegende Struktur.

### 6.4 Manuelle Spot Checks

Pro Cluster wurden die Top 10 Keywords gelesen und gegen das vergebene Label gegengeprüft. Cluster-IDs sind 0-basiert (Cluster 0 bis Cluster 9).

- **8 von 10 Cluster sind eindeutig sauber.** Beispiel Cluster 0 (Factoring-Grundlagen): `factoring buchen`, `factoring erlaubnis`, `offenes factoring`, `echtes factoring`, `factoring kfw`. Klar ein einziges Thema.
- **Cluster 5 (Operative Anleitungen, gemischt) ist heterogen.** Enthält `aüg`, `bewerber finden`, `lohnabrechnung sage`, `indeed alternative`, `lohnabrechnung erstellen`. Drei Sub-Themen in einem Cluster: HR-Wissen, Recruiting-Tipps, Lohnabrechnung. HDBSCAN hat hier keine ausreichende Dichte gefunden, um sie zu trennen.
- **Cluster 1 (Branche & Arbeitsrecht, Sammelbecken) ist mit 189 Keywords der mit Abstand größte Cluster.** Niedrige Kohäsion, mischt AÜG-Wissen, Software, Equal Pay, CRM, Branchen-Trends. Kandidat für ein zweites HDBSCAN nur auf diesem Cluster, um Sub-Cluster zu finden. Wichtigste methodische Empfehlung dieses Laufs.

Der manuelle Check ist subjektiv, aber notwendig, weil quantitative Maße wie Silhouette nicht alles erfassen. Hohe Silhouette-Werte können durch breite Cluster mit niedriger interner Kohäsion entstehen.

## 7. Reproduktion und Determinismus

Die Pipeline ist auf Reproduzierbarkeit ausgelegt:

- **`random_state=42`** in beiden UMAP Aufrufen.
- **HDBSCAN ist deterministisch** (keine zufällige Initialisierung).
- **Embeddings sind deterministisch** (Sentence Transformer im Inference-Modus).
- **Heuristische Enrichment** ist deterministisch (SHA256 Hash des Keywords als Seed).

Ein zweiter Lauf mit identischer `data/keywords.csv` produziert auf derselben Plattform byte-identische `embeddings.npy`, `umap_*.npy` und `keywords_labeled.csv`. Cross-Platform (z.B. lokale macOS-Entwicklung gegen Ubuntu-CI) sind die Embeddings byte-identisch, die UMAP-Koordinaten weichen wegen unterschiedlicher BLAS/LAPACK-Implementierungen minimal ab. Die Cluster-Anzahl bleibt mit `mcs=12` über Plattformen hinweg stabil.

Reproduktion auf einem fremden Rechner:

```bash
git clone https://github.com/t1nak/seo-pipeline.git
cd seo-pipeline
pip install -r requirements.txt
python -m src.cluster --step all
```

Erwartetes Ergebnis: 10 Cluster, Silhouette ~0,67, ARI 0,113 (vs LLM), ARI 0,565 (vs Ward k=10).

## 8. Bekannte Schwächen

- **Embedding Modell ist nicht state of the art.** `paraphrase-multilingual-MiniLM-L12-v2` ist zwei Jahre alt. Aktuelle Modelle wie `intfloat/multilingual-e5-large` würden vermutlich bessere Cluster produzieren, sind aber 20-fach größer. In Backlog für Produktion.
- **UMAP `n_neighbors=15` ist nicht getunt.** Aus dem Default übernommen. Eine Sensitivitäts-Analyse über `n_neighbors=10/15/20/30` würde belegen, dass die Cluster-Struktur stabil ist (oder das Gegenteil zeigen).
- **HDBSCAN sieht nicht alle thematischen Beziehungen.** Cluster 5 (Operative Anleitungen, gemischt) ist heterogen, weil HDBSCAN bei niedriger Dichte zwischen Sub-Themen nicht trennen kann. Eine zweite Iteration mit anderen Embeddings oder mit hierarchischem Refinement wäre eine Verbesserung.
- **Cluster Labels sind manuell.** Skaliert nicht über 50 Cluster. Backlog: pro Cluster die Top 10 Keywords an Claude geben und automatisch ein Label generieren lassen.
- **Keine Sensitivität gegen das Keyword Set.** Wenn 50 neue Keywords hinzukommen, ändern sich Cluster-Grenzen potentiell. Aktuell gibt es keinen Mechanismus, um die Stabilität zwischen Läufen zu messen. Vorschlag: Cluster-Persistenz-Score über Läufe hinweg tracken.

## 9. Lesetipps

- [Sentence Transformers Documentation](https://www.sbert.net/) für die Embedding Modelle
- [UMAP Original Paper](https://arxiv.org/abs/1802.03426) (McInnes, Healy, Melville 2018)
- [HDBSCAN Original Paper](https://link.springer.com/chapter/10.1007/978-3-642-37456-2_14) (Campello, Moulavi, Sander 2013)
- [hdbscan Python Library Docs](https://hdbscan.readthedocs.io/)
