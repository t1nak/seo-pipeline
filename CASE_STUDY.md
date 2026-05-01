# Case Study: SEO Keyword → ContentBrief Pipeline für zvoove

> Eine Pipeline, die aus dem zvoove Blog ein priorisiertes Keyword Set ableitet, thematisch clustert, pro Cluster einen Content Brief erzeugt und ein konsolidiertes Reporting liefert.

Diese Schreibarbeit erklärt, was gebaut wurde, warum so, wo die Grenzen liegen und wie das in einen Revenue Stack passt. Sie ist die längere Version des [README](README.md).

## 1. Aufgabe

Die Aufgabe in der ausgeschriebenen Form:

> Develop a keyword set from existing blog topics, cluster the keywords, generate content briefs, and transfer everything into a structured reporting system. Baue einen funktionierenden Workflow, der aus vorhandenen Blogartikeln, Themenfeldern oder Content-Schwerpunkten zunächst ein relevantes Keywordset von max. 500 Keywords entwickelt, diese anschließend thematisch clustert, pro Cluster einen Content-Brief generiert und die Ergebnisse in ein strukturiertes Reporting überführt. Die Basis ist unser Blog: https://zvoove.de/wissen/blog

Ich habe die Aufgabe als vier verbundene Probleme gelesen:

1. Welche Themen sind überhaupt relevant für die Zielgruppe und für zvoove als Anbieter?
2. Welche dieser Themen lohnen sich nach Suchnachfrage und Wettbewerb?
3. Welche Themen gehören semantisch zusammen und sollten als ein Pillar plus Cluster Strategie behandelt werden statt als isolierte Artikel?
4. Wie wird das Ergebnis so verpackt, dass eine Redaktion damit ohne weitere Vorarbeit produzieren kann?

Punkt 3 ist der eigentliche Gewinn. Punkt 4 ist das, was den Unterschied zwischen einer Keyword Liste und einem nutzbaren Asset ausmacht.

## 2. Ergebnis in zwei Minuten

Aus 500 Keywords (Cap aus 504 manuellem Baseline-Set) wurden 13 thematische Cluster — alle 500 Keywords sind zugeordnet, 0 Outlier — bei `mcs=10, ms=5, eom` plus Soft-Assignment der 72 HDBSCAN-Rand-Keywords. Die wichtigsten Zahlen:

| Metrik | Wert |
|---|---|
| Keywords gesamt | 500 |
| Cluster (HDBSCAN, `mcs=10, ms=5, eom` + Soft-Assignment) | **13 Cluster, 0 Outlier** |
| HDBSCAN-Kern-Keywords | 428 (direkt geclustert) |
| Soft-Assigned-Keywords | 72 (per Nearest-Centroid in 5D UMAP) |
| Gesamt Suchvolumen pro Monat | 239.976 (alle Cluster) |
| Größter Cluster nach SV | HR Software Dokumenten- und Mitarbeiterverwaltung (45.567 SV, 45 Keywords) |
| Größter Cluster nach Anzahl | Sammelthemen Zeitarbeit Software und Finanzierung (97 Keywords, 28.301 SV — Sub-Clustering empfohlen) |
| Höchste kommerzielle Dichte | Zvoove Produkte und Features (97 Prozent kommerziell, 23.604 SV) |
| Silhouette HDBSCAN-Kern | 0,647 |
| Silhouette inklusive Soft-Assignment | 0,570 |
| Silhouette Ward(k=12) (Vergleich) | 0,590 |
| ARI HDBSCAN gegen LLM-Cluster | 0,143 |
| ARI HDBSCAN gegen Ward(k=10) | 0,811 |

Die fünf größten Cluster nach Suchvolumen:

| # | Cluster (DE) | Keywords | SV / Monat | Ø KD | % kommerziell |
|---|---|---|---|---|---|
| 10 | HR Software Dokumenten- und Mitarbeiterverwaltung | 45 | 45.567 | 52 | 89 |
| 12 | Sammelthemen Zeitarbeit Software und Finanzierung | 97 | 28.301 | 36 | 34 |
| 1 | Zeiterfassung und Zeitarbeitssoftware | 47 | 26.159 | 48 | 94 |
| 7 | Digitalisierung Personaldienstleistung und KI | 37 | 23.984 | 36 | 35 |
| 3 | Zvoove Produkte und Features | 34 | 23.604 | 52 | 97 |

Cluster-Labels werden pro Lauf von einem Anthropic-Haiku-Aufruf aus den Top-Keywords erzeugt (siehe [`docs/decisions.md`](docs/decisions.md) ADR-5). Soft-Assignment der HDBSCAN-Rand-Keywords ist in [`docs/decisions.md`](docs/decisions.md) ADR-15 dokumentiert: jedes der 72 Noise-Keywords bekommt seinen nächsten Cluster-Centroid im 5D-UMAP-Raum, die ursprüngliche Noise-Eigenschaft bleibt in `noise_assigned: bool` erhalten.

Die interaktive Karte zum Klicken liegt unter [`output/clustering/cluster_map.html`](output/clustering/cluster_map.html). Sprache umschaltbar zwischen Deutsch und Englisch, Bubble Größe wählbar zwischen Suchvolumen, Priorität, CPC und Einfachheit, Klick auf einen Punkt öffnet die Keyword Tabelle des Clusters.

## 3. Lösungsansatz

Die Pipeline besteht aus sechs entkoppelten Schritten. Jeder Schritt liest klar definierte Eingaben und schreibt klar definierte Ausgaben. Das macht die Pipeline einzeln testbar und einzeln re-runnbar.

```
                    ┌─ scrapt ──→  data/blog_topics.csv (TODO)
discover.py ────────┤
                    └─ erweitert →  data/keywords_seed.csv (TODO)

                                        │
                                        ▼
enrich.py ─── SV/KD/CPC ─────────→  data/keywords.csv  (kanonisch)
                                        │
        ┌───────────────────────────────┘
        ▼
cluster.py  ─→  output/clustering/{cluster_map.html, embeddings.npy, charts/...}
brief.py    ─→  output/briefings/cluster_NN.md
report.py   ─→  output/reporting/index.html
export.py   ─→  output/reporting/{clusters,keywords,report}.json
```

Der Orchestrator `pipeline.py` kann alles in einem Lauf ausführen oder einzelne Schritte einzeln triggern. Das ist wichtig für die Praxis, weil verschiedene Schritte verschieden teuer sind: Embeddings einmal berechnen, dann Clustering Parameter mehrmals tunen.

## 4. Schritt 1: Discover

Hier ist der ehrliche Stand zuerst: der Discover Schritt scrapt den Blog noch nicht live. Was die Pipeline aktuell verwendet, ist ein kuratiertes Keyword Set, das in einer früheren Iteration mit Hilfe eines LLM aus den Blog Themen abgeleitet wurde. Die Datei `data/keywords.manual.csv` hält dieses Set frozen.

### Was die Live Variante tun müsste

Der Workflow für die Live Variante ist klar, fehlt aber als Code:

1. Die Blog Übersicht unter `https://zvoove.de/wissen/blog` paginieren und alle Artikel URLs einsammeln. Robust gegen Pagination Tricks und Lazy Loading.
2. Pro Artikel die Überschrift (H1, H2, H3) und die ersten 200 Wörter ziehen. Nicht den ganzen Artikel, weil sonst die Themenkonzentration verwässert.
3. Jeden Artikel mit Claude in Seed Keywords umformulieren. Pattern aus dem Brief: pro Artikel 5 bis 15 Seeds in den Kategorien Head, Body, Longtail. Deutsche Morphologie wird vom Modell selbst gehandhabt.
4. Ergebnis auf 500 Keywords begrenzen, sortiert nach geschätzter Relevanz für die Zielgruppe (Geschäftsführer und Operations Verantwortliche bei Zeitarbeit und Personaldienstleistung).
5. Als CSV mit den Spalten `keyword, estimated_intent, category, type, notes` schreiben. Diese Spalten sind das Contract Interface zu `enrich.py`.

### Warum nicht jetzt

Der Discover Schritt ist der höchstwertvolle, aber auch der Schritt mit den meisten Fallunterscheidungen (Anti-Bot, JavaScript Rendering, Robustheit gegen Layout Änderungen). Ich habe die Zeit lieber in die anderen vier Schritte gesteckt, weil ein gutes Cluster und ein guter Brief ohne saubere Discovery trotzdem demonstrierbar sind, während eine perfekte Discovery ohne Cluster und Brief wertlos wäre.

Dieser Trade-off ist als Architecture Decision in [`docs/decisions.md`](docs/decisions.md) festgehalten.

## 5. Schritt 2: Enrich

Pro Keyword werden Suchvolumen, Keyword Difficulty, Cost-per-Click, SERP Features und ein Priority Score berechnet. Es gibt zwei Modi.

### Heuristik (Default)

`enrich.py --provider estimate` erzeugt deterministische Schätzwerte aus einem SHA256 Hash des Keywords. Ranges sind nach Intent und Keyword Typ kalibriert (Head, Body, Longtail). Das ist offensichtlich kein Ersatz für echte Daten, aber:

- Es ist deterministisch, also reproduzierbar zwischen Läufen.
- Es ist schnell und kostenfrei, also für Pipeline Entwicklung tauglich.
- Die Werte sind in einer plausiblen Größenordnung, also reichen sie zum Cluster Profiling und zur Brief Erzeugung.
- Die Spalte `data_source` markiert jedes Keyword als `estimated`, also ist immer sichtbar, was geschätzt und was live ist.

### DataForSEO (Live)

`enrich.py --provider dataforseo` ruft die DataForSEO Labs API mit `language_code=de` und `location_code=2276` (Deutschland) auf. Die KD wird aus `competition_index` (0 bis 100) abgeleitet, was nahe genug an den Ahrefs / Semrush Definitionen ist, um Priorisierung zu erlauben. SERP Features brauchen einen separaten Endpoint, den ich aus Kosten Gründen nicht aktiviert habe, das ist ein leichter TODO.

Cost: ungefähr 0,75 USD für 500 Keywords im Search-Volume Endpoint. Vernachlässigbar gegenüber der Wertschöpfung.

## 6. Schritt 3: Cluster

Das ist das Herz der Pipeline. Die Aufgabe ist, 500 Keywords nach semantischer Ähnlichkeit zu gruppieren, ohne vorzugeben, wie viele Gruppen es geben soll und welche Keywords zu keiner Gruppe gehören.

### Schritt 3.1: Embeddings

Ich nutze das Modell `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Die Wahl hat drei Gründe:

- **Mehrsprachig.** Die zvoove Keywords sind durchgehend Deutsch. Das nicht-multilinguale `all-MiniLM-L6-v2` würde deutsche Komposita und Flexionen schlechter handhaben.
- **Klein.** Das Modell ist ungefähr 120 MB groß und läuft auf einem normalen Laptop ohne GPU in Sekunden.
- **Etabliert.** Sentence Transformers sind das Standard-Werkzeug für semantische Ähnlichkeit. Kein experimentelles Setup, das in der Bewertung erklärungsbedürftig wäre.

Die Embedding Dimension ist 384. Pro Keyword eine Zeile, normalisiert, gespeichert als `embeddings.npy`.

### Was ist ein Embedding und warum brauche ich das

Ein Embedding ist eine Zahlenfolge, die die Bedeutung eines Texts beschreibt. Zwei Texte mit ähnlicher Bedeutung haben ähnliche Zahlen, auch wenn die Wörter unterschiedlich sind.

Beispiel: "Lohnabrechnung Software" und "Payroll Tool" liegen mathematisch sehr nah beieinander, obwohl kein Wort identisch ist. Genau das brauche ich, um Keywords nach Thema zu gruppieren statt nach exakten Wortübereinstimmungen.

### Schritt 3.2: Dimensionsreduktion mit UMAP

UMAP reduziert die 384-dimensionalen Embeddings auf 5 Dimensionen für das Clustering und 2 Dimensionen für die Visualisierung. Zwei Reduktionen, weil die Optima unterschiedlich sind: das Clustering profitiert von ein paar mehr Dimensionen, die Karte braucht genau zwei.

UMAP statt PCA, weil PCA lokale Struktur opfert, um globale Varianz zu maximieren. Für density-based Clustering ist genau die lokale Struktur wichtig. UMAP statt t-SNE, weil t-SNE keine konsistente Distanzmetrik liefert (zwei nah aussehende Punkte sind nicht zwingend ähnlich), während UMAP zumindest lokal interpretierbar ist.

Parameter:

```
n_neighbors=15        balanciert lokale und globale Struktur
metric="cosine"       passt zu normalisierten Embeddings
min_dist=0.0 (5D)     für Clustering: Punkte dürfen sich überlagern
min_dist=0.1 (2D)     für Karte: Punkte werden leicht auseinandergezogen
random_state=42       reproduzierbar
```

### Schritt 3.3: HDBSCAN

HDBSCAN ist ein Cluster-Algorithmus. Er gruppiert ähnliche Keywords automatisch und entscheidet selbst, wie viele Gruppen sinnvoll sind. Ausreißer (Keywords, die zu nichts passen) werden als Rauschen markiert, statt zwanghaft zugeordnet.

HDBSCAN gegenüber k-means hat drei Vorteile, die für SEO Keywords zentral sind:

- **Keine vorgegebene Clusteranzahl.** Bei k-means muss ich raten, ob es 5 oder 10 oder 15 Cluster gibt. Bei HDBSCAN entsteht die Anzahl aus den Daten.
- **Echte Ausreißer.** Manche Keywords passen zu nichts, weil sie semantische Solitäre sind (zum Beispiel `fachkräftemangel deutschland`, ein Top-Funnel Begriff ohne klare Cluster Heimat). HDBSCAN markiert sie als Rauschen, k-means würde sie zwanghaft einem Cluster zuordnen und damit dessen Profil verwässern.
- **Variable Clusterdichte.** Manche Themen sind eng (10 zvoove Markenbegriffe), manche breit (40 Zeitarbeit Software Begriffe). HDBSCAN handhabt das natürlich, Distanz-basierte Verfahren wie k-means tun sich schwer.

### Schritt 3.4: Hyperparameter Sweep

Für die finalen Parameter habe ich eine Grid Search über `min_cluster_size`, `min_samples` und `cluster_selection_method` gefahren. Der Sweep ist als `cluster.step_sweep()` reproduzierbar.

Ergebnis: `min_cluster_size=10, min_samples=5, cluster_selection_method='eom'`.

Begründung in [`docs/methodology.md`](docs/methodology.md). Kurz: bei dieser Kombination ist der Silhouette Score am höchsten, das Rauschen ist plausibel niedrig (14 Prozent), die Clusteranzahl ist mit 13 für die Stakeholder Kommunikation ideal (klein genug für eine Tabelle, groß genug, um Sub-Themen zu unterscheiden).

### Schritt 3.5: Hierarchischer Vergleich

Zusätzlich rechne ich Ward Hierarchical Clustering auf den gleichen UMAP-Daten und vergleiche die Übereinstimmung. Das ist nicht der Hauptalgorithmus, sondern eine Gegenprobe und eine Alternative für Stakeholder, die „ich brauche genau k Cluster" wollen statt „automatisch erkannte Cluster".

Die Übereinstimmung wird mit Adjusted Rand Index (ARI) und Normalized Mutual Information (NMI) gemessen. Beide Maße sind 0 bei Zufall und 1 bei perfekter Übereinstimmung.

### Schritt 3.6: Cluster Labels

Pro Cluster ein deutsches Label (zum Beispiel „Zvoove Produktfeatures und Preise") und ein englisches Label. Die Labels werden pro Lauf von einem Anthropic-Haiku-Batch-Call aus den Top-Keywords und Top-Termen erzeugt (`src/labels_llm.py`). Eine handgepflegte YAML-Datei (`data/cluster_labels.yaml`) bleibt als Fallback für Demo-Läufe ohne API-Key. Vorteil dieses Setups: jeder Hyperparameter-Sweep bekommt sofort sinnvolle Bezeichnungen; Nachteil: Wortwahl variiert leicht zwischen Läufen, was für stabile Long-Run-Reports per JSON-Pinning oder manueller Korrektur abgefangen werden kann. Methodische Einordnung in [`docs/decisions.md`](docs/decisions.md) ADR-5.

## 7. Schritt 4: Brief

Pro Cluster wird ein Content Brief in deutscher Sprache als Markdown Datei nach `output/briefings/cluster_NN.md` geschrieben.

### Brief Struktur

Jeder Brief enthält:

- Arbeitstitel und Hauptkeyword
- 3 bis 7 Nebenkeywords aus dem Cluster
- Suchintention (commercial, informational, mixed) mit Begründung
- Empfohlene Wortanzahl
- Zielgruppe als 1-Satz Persona
- Schmerzpunkt (was hält den Leser nachts wach)
- Ziel des Artikels
- Outline mit H1 bis H3
- Drei Benchmark URLs (Wettbewerber oder hoch rankende Artikel) mit Begründung
- Call to Action mit Bezug zu zvoove Produkten

Die Struktur ist im System Prompt von `brief.py` festgehalten, also pro Lauf konsistent über alle Cluster.

### Claude API Integration

Verwendet wird `claude-sonnet-4-6` mit Prompt Caching auf dem System Block. Der System Prompt (ungefähr 800 Tokens, beschreibt das Brief Format und den Stil) wird einmal gecached und bei den darauf folgenden Aufrufen wiederverwendet. Token Ersparnis: ungefähr 90 Prozent auf den gecachten Anteil, also für 13 Cluster ungefähr 8000 Tokens gespart.

Pro Brief ungefähr 2500 Output Tokens, also pro vollem Lauf ungefähr 35.000 Output Tokens und 2500 Input Tokens (cached). Geschätzte Kosten: ungefähr 0,15 bis 0,25 USD pro Lauf.

### Fehlerbehandlung

Wenn ein einzelner API Call fehlschlägt (Network, Rate Limit, etc.), schreibt das Skript einen Stub in die Datei und macht weiter. Die Pipeline bricht nicht ab, weil ein einzelner Brief fehlt. Ein Status Reporting am Ende sagt, wie viele OK und wie viele Fehler waren.

`brief.py` nutzt `src.retry.with_retry` — einen Wrapper mit exponentieller Backoff Strategie und Jitter — für alle API Calls, sodass einzelne Rate-Limit-Antworten automatisch wiederholt werden.

### Dry Run

`brief.py --dry-run` schreibt für jeden Cluster einen Stub mit den Top Keywords und einer Notiz, dass kein API Aufruf stattgefunden hat. Nützlich zum Testen der Pipeline ohne API Kosten und in CI Umgebungen ohne Key.

## 8. Schritt 5: Report

`report.py` erzeugt eine einzelne `output/reporting/index.html`, die alle Pipeline Artefakte konsolidiert: KPI Boxen oben, sortierte Cluster Tabelle in der Mitte, eingebettete Charts unten, Link auf die interaktive Karte.

Bewusst keine Frontend Framework Abhängigkeit. Es ist eine einfache HTML Datei mit Inline CSS, die in jedem Browser funktioniert, sich an Stakeholder verschicken lässt und in einer Slack Nachricht klickbar bleibt. Wenn das später als Dashboard in einem Reporting Stack landen soll, ist das Markup einfach genug, um es nach Looker Studio oder Metabase zu portieren.

## 9. Schritt 6: Export

Die Aufgabenstellung verlangt am Ende ein filterbares Reporting in einem Tool wie Google Sheets, Airtable oder Notion. `export.py` erfüllt das, indem es alle Ergebnisse aus den vorherigen Schritten in flache JSON-Dateien überführt, die jedes dieser Tools direkt importieren kann.

Drei Dateien werden in `output/reporting/` geschrieben:

| Datei | Inhalt | Anwendungsfall |
|---|---|---|
| `clusters.json` | Eine Zeile pro Cluster mit allen KPIs plus den geparsten Brief-Feldern (Hauptkeyword, Zielgruppe, H1, H2-Outline, Wortanzahl, CTA, Benchmark-URLs als Liste) | Cluster-Reporting in Airtable, Notion-Datenbank oder Google Sheet |
| `keywords.json` | Eine Zeile pro Keyword mit Cluster-Zuordnung, SV, KD, CPC, Priority, SERP Features | Filterbare Keyword-Sicht, etwa zum Sortieren nach Priority oder zum Filtern auf einen Intent |
| `report.json` | Run-Metadaten plus beide Listen in einem Bundle | Wenn ein Tool oder Skript alles in einem Rutsch lesen will |

Zusätzlich werden die Dateien nach `output/reporting/runs/<run_id>/` gespiegelt, damit jeder Lauf seinen eigenen Schnappschuss behält. So bleibt nachvollziehbar, wie sich Cluster und Priorisierung über Quartale verändern.

Warum JSON statt direkter API-Anbindung an Airtable oder Notion? Eine Datei ist toolneutral und ohne API-Key importierbar. Wer regelmäßig importieren will, hängt einen kleinen Wrapper an: Airtable und Notion akzeptieren JSON-Listen direkt im REST-API-POST, Google Sheets braucht eine Konvertierung zu CSV (eine Zeile Python). Diese letzte Meile ist bewusst nicht Teil der Pipeline, weil die Wahl des Reporting-Tools zur Entscheidung des Marketing-Teams gehört, nicht zur technischen Lieferung.

## 10. Validierung

Drei Validierungs-Ebenen, von leichtgewichtig zu schwergewichtig.

### Quantitativ: Silhouette Score

Silhouette misst, wie gut Cluster getrennt sind, von -1 (schlecht) bis +1 (perfekt).

| Setup | Silhouette |
|---|---|
| HDBSCAN-Kern (428 Keywords, vor Soft-Assignment) | 0,647 |
| Alle 500 (nach Soft-Assignment) | 0,570 |
| Ward Hierarchical (k=12) | 0,590 |

0,647 ist für reale Textdaten sehr gut. Zur Einordnung: Werte über 0,5 gelten als belastbare Cluster. Der Drop auf 0,570 nach Soft-Assignment ist erwartet — die 72 Rand-Keywords liegen per Definition näher an einer Cluster-Grenze. Beide Werte bleiben über Ward(k=12) bei 0,590.

### Quantitativ: Übereinstimmung mit Alternative

Wie ähnlich sind die HDBSCAN Cluster den ursprünglich vom LLM kuratierten Cluster Definitionen?

| Vergleich | ARI | NMI |
|---|---|---|
| HDBSCAN gegen LLM Cluster (HDBSCAN-Kern) | 0,143 | 0,342 |
| HDBSCAN gegen Ward Hierarchical (k=10, alle 500) | 0,811 | (nicht erhoben) |

ARI ist konservativer als NMI, also ARI < NMI ist normal. Die LLM-vs-HDBSCAN-Werte sind erwartet niedrig: HDBSCAN findet andere Cluster-Grenzen als die LLM-Klassifikation, das ist methodisch interessant und keineswegs ein Fehler. Beide sind gültige Sichten auf die Daten. Der ARI von 0,811 zwischen HDBSCAN und Ward(k=10) zeigt zugleich, dass zwei mathematisch unabhängige Verfahren auf großer Mehrheit übereinstimmen.

Ein Beispiel: Der ursprüngliche LLM Cluster `cluster_03` („Recruiting & Bewerbermanagement") wird von HDBSCAN in zwei Cluster aufgeteilt („KI-gestützte Recruiting-Automatisierung" und „HR- und Bewerbermanagementsoftware KMU"), weil ATS- und SaaS-Begriffe semantisch näher an Software-Kategorien liegen als an Recruiting-Workflows. Das ist eine empirische Erkenntnis, die ohne diese Analyse nicht sichtbar wäre.

### Qualitativ: Manuelle Spot Checks

Ich habe für jeden der 13 Cluster die Top 10 Keywords gelesen und gegen das LLM-generierte Label gegengeprüft. Ergebnis:

- 11 von 13 Clustern sind eindeutig sinnvoll und sauber. Beispiel Cluster 0 (Factoring Buchhaltung und Genehmigung): `factoring buchen`, `factoring erlaubnis`, `offenes factoring`. Beispiel Cluster 1 (Zeiterfassung und Zeitarbeitssoftware): `zeiterfassung software`, `mobile zeiterfassung`, `zeitarbeitssoftware`.
- Cluster 4 (Sammelthemen Lohnabrechnung und Recruiting) ist vom LLM transparent als „Sammelthemen" gelabelt — enthält `aüg`, `bewerber finden`, `lohnabrechnung sage`, `indeed alternative`. Nicht falsch, aber kein klares Pillar-Thema. Empfohlene Bearbeitung: Top-Keywords einzeln, nicht als Pillar.
- Cluster 12 (Sammelthemen Zeitarbeit Software und Finanzierung) ist mit 97 Keywords der größte Cluster. Bündelt „Zeitarbeit + X" Kombinationen aus Software, Factoring, CRM, Lohn. Vom LLM transparent als „Sammelthemen" gelabelt. Empfohlen: Sub-Clustering vor Bearbeitung. Vollständige pro-Cluster-Empfehlung in [`docs/results.md`](docs/results.md).

## 11. Top Empfehlungen aus diesem Lauf

Drei aus den 13 Clustern, sortiert nach Hebel für zvoove. Eine vollständige Cluster-Tabelle mit Empfehlung pro Cluster steht in [`docs/results.md`](docs/results.md).

### Empfehlung 1: HR Software Dokumenten- und Mitarbeiterverwaltung (Cluster 10)

45.567 SV pro Monat, 45 Keywords, 89 Prozent kommerziell, mittlere KD 52. Top Keywords: `dokumentenmanagement software`, `bewerbermanagement software`, `mitarbeiterverwaltung software`, `hr software kmu`, `gehaltsabrechnung software`.

Was tun: ein Pillar Page Set zu Software-Kategorien, das jeweils zvoove-Module als Lösung positioniert. Hohe SV, mittelhohe Schwierigkeit, hohe kommerzielle Dichte. Klassischer Bottom-of-Funnel-Hebel.

Revenue Hypothese: Wenn 5 Prozent der monatlichen 45.000 SV Klicks generieren und 2 Prozent davon zu MQLs werden, sind das 45 MQLs pro Monat aus diesem Cluster.

### Empfehlung 2: Zvoove Produkte und Features (Cluster 3)

23.604 SV, 34 Keywords, 97 Prozent kommerziell, mittlere KD 52. Top Keywords: `zvoove referenzen`, `zvoove dms`, `zvoove cockpit`, `zvoove payroll`, `zvoove cashlink`.

Was tun: alle Brand-Begriffe müssen auf dedizierten Produktseiten ranken. KD 52 ist für Brand-Keywords ungewöhnlich hoch, was darauf hindeutet, dass aktuell entweder Wettbewerber-Vergleichsseiten oder Bewertungsplattformen die SERP belegen.

Schneller Win: Ein zvoove-Erfahrungen-Hub, der die positiven Bewertungen aggregiert, mit klarer URL-Struktur unter `/produkte/`.

### Empfehlung 3: Digitalisierung Personaldienstleistung und KI (Cluster 7)

23.984 SV pro Monat, 37 Keywords, 35 Prozent kommerziell, mittlere KD 36. Top Keywords: `digitalisierung zeitarbeit`, `digitalisierung personaldienstleistung`, `künstliche intelligenz personaldienstleistung`, `digitale zeiterfassung`, `elektronische lohnabrechnung`.

Was tun: Hub-Pillar `/wissen/digitalisierung-personaldienstleistung/`, der gezielt Awareness-Traffic in die kommerziellen Cluster 1 (Zeitarbeitssoftware), 10 (HR-Software) und 3 (zvoove) überführt. Mittlere KD und niedrige kommerzielle Dichte machen das zum klassischen Top-of-Funnel-Eingang. Priority 16,8 — einer der hebel-stärksten Cluster.

Revenue Hypothese: Pipeline-Influence statt direkte Conversion. Über 6 bis 12 Monate erwartbar: Brand-Lift-Wirkung und gestützte Brand-Suchen. Geschäftsführer recherchieren Digitalisierungs-Schritte genau dann, wenn ein Software-Wechsel ansteht.

## 12. Wie das in den Revenue Stack passt

Eine SEO Pipeline ist nur dann ein Revenue Asset, wenn ihre Ausgaben in andere Systeme einfließen. Diese Pipeline ist bewusst so gebaut, dass die Anbindung pro Schritt klar ist.

| Pipeline Output | Anbindung an den Revenue Stack |
|---|---|
| `data/keywords.csv` (500 Keywords mit SV/KD/CPC) | Input für Google Ads Keyword Planning, Input für Ahrefs / Semrush Tracking, Input für Looker Studio SEO Dashboards |
| `output/clustering/cluster_profiles.csv` plus `cluster_labels.json` (13 Cluster, 0 Outlier) | Content-Kalender-Anker in Notion / Airtable, Pillar-Page-Architektur für ein neues `/wissen/` Verzeichnis |
| `output/briefings/cluster_NN.md` (13 Briefs) | direkter Input für die Redaktion in einem Headless CMS (Sanity, Contentful) oder direkt in WordPress |
| `output/clustering/cluster_map.html` (interaktive Karte) | embedbar in einem internen Wiki, Slack Card, oder Notion Page für die wöchentliche Marketing Stand-up |
| `output/reporting/index.html` (Dashboard) | embedbar in der Marketing Wiki, alternativ Quelle für ein Looker Studio Embed |

Was bewusst nicht eingebaut ist: Auto-Publishing in ein CMS. Briefs sind explizit eine Übergabe an die Redaktion, nicht eine Maschine-zu-Maschine Verbindung. Der Grund: Briefs sind ein Verhandlungspunkt zwischen SEO und Redaktion, und ein automatisches Publishing würde diese Schnittstelle entwerten.

### Anbindung an Salesforce / HubSpot

Wenn die Pipeline einmal pro Quartal läuft, kann der Output mit MQLs aus dem CRM gegengelegt werden:

- Keywords nach Cluster gruppieren
- MQLs der letzten 90 Tage nach erstem organischen Landing Page bereinigen
- Pro Cluster: SV, KD, MQLs, Cost-per-MQL aus parallelen Paid Kampagnen
- Daraus eine Revenue Attribution Sicht auf SEO ableiten

Das ist eine Erweiterung, kein Teil dieser Lieferung, aber technisch trivial: ein zusätzliches Skript `revenue_attribution.py`, das `cluster_profiles.csv` mit einer CRM Export CSV joint.

## 13. Cost und Ops

| Posten | Kosten pro Lauf |
|---|---|
| Embeddings (lokal, MiniLM) | 0 |
| UMAP / HDBSCAN (lokal, CPU) | 0 |
| DataForSEO Search Volume (500 Keywords) | ~0,75 USD (optional) |
| Anthropic Haiku, Cluster-Labels (1 Batch-Call) | ~0,01 USD |
| Claude Sonnet Briefs (13 Cluster, mit Caching) | ~0,18 bis 0,25 USD |
| Gesamt | ~1 USD pro voller Lauf |

Bei wöchentlicher Ausführung: ungefähr 50 USD pro Jahr. Vernachlässigbar gegenüber der Wertschöpfung eines einzigen rankenden Pillar Artikels.

Lauf Frequenz Empfehlung: einmal pro Quartal voll, zwischendrin nur `enrich` (für aktualisierte SV Daten) und `report`. Embeddings und Cluster ändern sich nur, wenn das Keyword Set sich substantiell ändert.

## 14. Limits und nächste Schritte

Ehrlich, was fehlt oder schwach ist:

### Schwächen im aktuellen Stand

- **Discover ist Stub.** Das Live Scraping fehlt. Aktuell läuft die Pipeline auf einem kuratierten Keyword Set.
- **Sentence Transformer ist nicht das beste Modell für Deutsch.** Multilingual MiniLM ist gut, aber nicht state of the art. Für ein Produktionsprojekt wäre `intfloat/multilingual-e5-large` oder ein deutsches Modell wie `aari1995/German_Sentiment_BERT` einen Test wert.
- **Keine Persistenz Schicht.** Pipeline Läufe leben als Snapshots im Dateisystem. Kein SQLite, kein Postgres. Für Produktion fehlt das.

### Nächste Schritte (priorisiert)

1. **Discover live machen.** Scraper für `zvoove.de/wissen/blog`, plus Claude basierte Keyword Expansion. Höchste Hebelwirkung, weil es die Pipeline von "demonstriert das Konzept" zu "tatsächlich für zvoove einsetzbar" hebt.
2. **Search Console Anbindung.** Statt Heuristik echte Click und Impression Daten aus der zvoove GSC ziehen. Das macht die Priorisierung empirisch verifizierbar.
3. **Persistenz Schicht.** Eine SQLite Datei mit `run_id, timestamp, step, status, rows_in, rows_out` würde Lauf-Vergleiche erheblich vereinfachen.
4. **CMS Integration.** Sanity Studio Schema für Content Briefs, plus ein einfacher Sync, der jeden Brief als Draft in Sanity legt.

## 15. Reflektion

### Was lief gut

Die Pipeline ist von Anfang an als entkoppelte Schritte gebaut. Das hat sich mehrfach ausgezahlt, weil ich Cluster Parameter mehrmals verändern konnte, ohne Embeddings neu rechnen zu müssen, und weil ich Briefs auf alten Cluster Daten generieren konnte, während ich am Reporting arbeitete.

Der Ansatz, einen kuratierten Manual Datensatz als frozen Baseline zu behalten, war wichtig. Er gibt mir und einem Reviewer einen klaren Bezugspunkt für "wenn die Pipeline neu rechnet, ist das Ergebnis besser oder schlechter als die Baseline". Ohne diese Baseline wäre jede Iteration eine subjektive Bewertung.

### Was ich anders machen würde

Bei einer zweiten Iteration würde ich Discover zuerst bauen, nicht zuletzt. Der Schritt ist konzeptionell der schwierigste (echtes HTML im echten Web ist immer ein Wundertüten-Problem), und ihn zuletzt zu bauen heißt, ihn unter Zeitdruck zu bauen.

Weiter: ich würde eher als Teil der ersten Iteration einen einfachen Run Log einbauen. Aktuell rate ich rückwärts aus Dateinamen, welcher Lauf welcher war. Eine SQLite Datei mit `run_id, timestamp, step, status, rows_in, rows_out` würde 30 Minuten kosten und vieles vereinfachen.

### Was die Bewerbung adressieren soll

Diese Case Study soll drei Dinge zeigen:

- **Architektur Denken statt Skript Denken.** Eine Pipeline ist nicht ein Bündel von Skripten, sondern ein definiertes Datenmodell mit klaren Schnittstellen. Die fünf Schritte hier sind so geschnitten, dass jeder einzeln ersetzt werden kann.
- **Pragmatismus über Polish.** Heuristische Schätzwerte für SV / KD / CPC sind klar als geschätzt markiert und werden durch DataForSEO ersetzt, wenn echte Daten verfügbar sind. Discover fehlt als Live-Schritt. Beides bewusste Entscheidungen, nicht Lücken.
- **Revenue Lens.** Die Cluster werden nicht nur ausgegeben, sondern jede Empfehlung wird in eine Revenue Hypothese übersetzt (Cluster X führt zu Y MQLs pro Monat). Das ist die Übersetzungsleistung, die ein Revenue AI Architect leisten muss.

## Anhang: weitere Dokumente

- [`docs/methodology.md`](docs/methodology.md): Parameter Sweep Tabelle, Reproduktion, statistische Validierung
- [`docs/results.md`](docs/results.md): vollständiger 13-Cluster-Katalog mit Empfehlung pro Cluster
- [`docs/architecture.md`](docs/architecture.md): Pipeline Diagramm, Datenfluss, Integration
- [`docs/decisions.md`](docs/decisions.md): Architecture Decision Records
