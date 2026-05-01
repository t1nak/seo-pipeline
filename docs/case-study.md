# Case Study: SEO Keyword → ContentBrief Pipeline für zvoove

> Eine Pipeline, die aus dem zvoove Blog ein priorisiertes Keyword Set ableitet, thematisch clustert, pro Cluster einen Content Brief erzeugt und ein konsolidiertes Reporting liefert.

Diese Schreibarbeit erklärt, was gebaut wurde, warum so, wo die Grenzen liegen und wie das in einen Revenue Stack passt. Sie ist die längere Version des [README](index.md).

## 1. Aufgabe

Die Aufgabe in der ausgeschriebenen Form:

> Develop a keyword set from existing blog topics, cluster the keywords, generate content briefs, and transfer everything into a structured reporting system. Baue einen funktionierenden Workflow, der aus vorhandenen Blogartikeln, Themenfeldern oder Content-Schwerpunkten zunächst ein relevantes Keywordset von max. 500 Keywords entwickelt, diese anschließend thematisch clustert, pro Cluster einen Content-Brief generiert und die Ergebnisse in ein strukturiertes Reporting überführt. Die Basis ist unser Blog: https://zvoove.de/wissen/blog

Ich habe die Aufgabe als vier verbundene Probleme gelesen:

1. Welche Themen sind überhaupt relevant für die Zielgruppe und für zvoove als Anbieter?
2. Welche dieser Themen lohnen sich nach Suchnachfrage und Wettbewerb?
3. Welche Themen gehören semantisch zusammen und sollten als ein Pillar plus Cluster Strategie behandelt werden statt als isolierte Artikel?
4. Wie wird das Ergebnis so verpackt, dass eine Redaktion damit ohne weitere Vorarbeit produzieren kann?

Punkt 3 ist der eigentliche Gewinn. Punkt 4 ist das, was den Unterschied zwischen einer Keyword Liste und einem nutzbaren Asset ausmacht.

## Das Problem in einem Satz

Das Ziel ist es, im Bereich Zeitarbeit und Personaldienstleistung organischen Traffic zu gewinnen, der echte Kaufinteressenten bringt. Dafür braucht es eine klare Antwort auf die Frage: Welche Themen lohnen sich wirklich, und in welcher Reihenfolge?

## 2. Ergebnis in zwei Minuten

Aus 500 Keywords (Cap aus 504 manuellem Baseline-Set) wurden 10 thematische Cluster plus rund 40 Ausreißer (~8 Prozent). Die wichtigsten Zahlen:

| Metrik | Wert |
|---|---|
| Keywords gesamt | 500 |
| Cluster (HDBSCAN, `mcs=10, ms=5, eom` + Soft-Assignment) | **13 Cluster, 0 Outlier** |
| HDBSCAN-Kern-Keywords | 428 (direkt geclustert) |
| Soft-Assigned-Keywords | 72 (Nearest-Centroid in 5D UMAP) |
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

Cluster-Labels werden pro Lauf von einem Anthropic-Haiku-Aufruf aus den Top-Keywords erzeugt ([ADR-5](decisions.md#adr-5-llm-generierte-cluster-labels-pro-lauf-yaml-als-fallback)). Soft-Assignment der HDBSCAN-Rand-Keywords ist in [ADR-15](decisions.md#adr-15-soft-assignment-fur-noise-keywords) dokumentiert: jedes der 72 Noise-Keywords bekommt seinen nächsten Cluster-Centroid im 5D-UMAP-Raum, die ursprüngliche Noise-Eigenschaft bleibt in `noise_assigned: bool` erhalten.

Die interaktive Karte zum Klicken liegt unter [`output/clustering/cluster_map.html`](https://t1nak.github.io/seo-pipeline/output/clustering/cluster_map.html). Sprache umschaltbar zwischen Deutsch und Englisch, Bubble Größe wählbar zwischen Suchvolumen, Priorität, CPC und Einfachheit, Klick auf einen Punkt öffnet die Keyword Tabelle des Clusters.

## 3. Lösungsansatz

Die Pipeline besteht aus vier modularen Phasen, in der aktuellen Umsetzung als fünf entkoppelte Skripte implementiert (Discover und Enrich liegen heute getrennt vor, würden bei Providern wie SEMrush oder DataForSEO aber zusammenfallen). Jeder Schritt liest klar definierte Eingaben und schreibt klar definierte Ausgaben. Das macht die Pipeline einzeln testbar und einzeln re-runnbar.

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
```

Der Orchestrator `pipeline.py` kann alles in einem Lauf ausführen oder einzelne Schritte einzeln triggern. Das ist wichtig für die Praxis, weil verschiedene Schritte verschieden teuer sind: Embeddings einmal berechnen, dann Clustering Parameter mehrmals tunen.

## 4. Schritt 1: Discover

Discover beantwortet die Frage „welche Keywords sind überhaupt relevant?". Die Pipeline ist hier bewusst Provider-offen aufgebaut — die Quelle ist austauschbar, das Output-Format `data/keywords.csv` mit den Spalten `keyword, estimated_intent, category, type, notes` ist die Schnittstelle zu Schritt 2.

### Mögliche Discover-Quellen

| Quelle | Beschreibung | Heute aktiv |
|---|---|---|
| **Manual CSV** | Kuratiertes Keyword Set aus früherer Iteration, mit Hilfe eines LLM aus Blog-Themen abgeleitet. Frozen in `data/keywords.manual.csv`. | Ja, Default |
| **zvoove Blog Scrape** | Live-Crawl der Blog-Übersicht (`zvoove.de/wissen/blog`), pro Artikel H1/H2/H3 plus erste 200 Wörter, anschließend LLM-basierte Umformulierung in Seed-Keywords. | TODO |
| **SEMrush API** | Abruf von Keyword-Vorschlägen zu einer Domain oder Seed-Liste über die SEMrush Domain Analytics API. Liefert direkt Suchvolumen mit (Schritt 1 und 2 fallen zusammen). | Optional, einbaubar |
| **DataForSEO Labs API** | Ähnlich wie SEMrush mit alternativem Provider. Ranked Keywords oder Related Keywords Endpoints. | Optional, einbaubar |
| **Ahrefs Keywords Explorer API** | Weiterer Anbieter mit Suchvolumen-Datenbank, gleiches Discover-Pattern. | Optional, einbaubar |

Für die Demo hier wird das Manual CSV verwendet, weil es reproduzierbar ist und keine externe API erfordert. Ein Wechsel auf einen der API-Provider wäre eine reine Provider-Implementierung in `discover.py` ohne Schnittstellen-Änderung zu Schritt 2.

### Beispiel: Discover über SEMrush

In der ausgeschriebenen Aufgabe wurde SEMrush als möglicher Provider gezeigt. Die Anbindung wäre eine zweite `Provider`-Klasse in `discover.py` (analog zum Pattern in `brief.py` mit `ApiKeyProvider` / `OpenAIProvider`):

1. SEMrush API-Key als Secret konfigurieren (`SEMRUSH_API_KEY`).
2. `python pipeline.py --step discover --source semrush --domain zvoove.de` ruft den Domain-Analytics-Endpoint auf.
3. Resultat: bis zu 500 Top-Keywords, jeweils mit Suchvolumen, Difficulty, CPC. Discover und Enrich kollabieren in einen Schritt — der API-Provider liefert die Anreicherung gleich mit.

Das ist genau der Vorteil der modularen Architektur: Zugriffspfad und Datenquelle ändern sich, das Schnittstellen-Schema zur nächsten Phase bleibt.

### Live-Blog-Scrape: was es bräuchte

Der Workflow für die Live-Scrape-Variante ist konzeptionell klar, fehlt aber als Code:

1. Die Blog-Übersicht unter `https://zvoove.de/wissen/blog` paginieren und alle Artikel-URLs einsammeln. Robust gegen Pagination-Tricks und Lazy Loading.
2. Pro Artikel die Überschrift (H1, H2, H3) und die ersten 200 Wörter ziehen. Nicht den ganzen Artikel, weil sonst die Themenkonzentration verwässert.
3. Jeden Artikel mit Claude in Seed-Keywords umformulieren. Pattern: pro Artikel 5 bis 15 Seeds in den Kategorien Head, Body, Longtail. Deutsche Morphologie wird vom Modell selbst gehandhabt.
4. Ergebnis auf 500 Keywords begrenzen, sortiert nach geschätzter Relevanz für die Zielgruppe (Geschäftsführer und Operations-Verantwortliche bei Zeitarbeit und Personaldienstleistung).
5. Als CSV mit den Spalten `keyword, estimated_intent, category, type, notes` schreiben.

### Warum nicht jetzt

Der Discover-Schritt ist der höchstwertvolle, aber auch der mit den meisten Fallunterscheidungen (Anti-Bot, JavaScript-Rendering, Robustheit gegen Layout-Änderungen). Ich habe die Zeit lieber in die anderen vier Phasen gesteckt, weil ein gutes Cluster und ein guter Brief auch auf einem kuratierten Set demonstrierbar sind, während eine perfekte Discovery ohne Cluster und Brief wertlos wäre.

Dieser Trade-off ist als Architecture Decision in [`decisions.md`](decisions.md) festgehalten.

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

Ergebnis: `min_cluster_size=15, min_samples=5, cluster_selection_method='eom'`.

Begründung in [`methodology.md`](methodology.md). Kurz: bei dieser Kombination ist der Silhouette Score am höchsten, das Rauschen ist plausibel niedrig (14 Prozent), die Clusteranzahl ist mit 13 für die Stakeholder Kommunikation ideal (klein genug für eine Tabelle, groß genug, um Sub-Themen zu unterscheiden).

### Schritt 3.5: Hierarchischer Vergleich

Zusätzlich rechne ich Ward Hierarchical Clustering auf den gleichen UMAP-Daten und vergleiche die Übereinstimmung. Das ist nicht der Hauptalgorithmus, sondern eine Gegenprobe und eine Alternative für Stakeholder, die „ich brauche genau k Cluster" wollen statt „automatisch erkannte Cluster".

Die Übereinstimmung wird mit Adjusted Rand Index (ARI) und Normalized Mutual Information (NMI) gemessen. Beide Maße sind 0 bei Zufall und 1 bei perfekter Übereinstimmung.

### Schritt 3.6: Cluster Labels

Pro Cluster ein deutsches Label (zum Beispiel „Zvoove Produktfeatures und Preise") und ein englisches Label. Die Labels werden pro Lauf von einem Anthropic-Haiku-Batch-Call aus den Top-Keywords und Top-Termen erzeugt (`src/labels_llm.py`). Eine handgepflegte YAML-Datei (`data/cluster_labels.yaml`) bleibt als Fallback für Demo-Läufe ohne API-Key. Vorteil dieses Setups: jeder Hyperparameter-Sweep bekommt sofort sinnvolle Bezeichnungen; Nachteil: Wortwahl variiert leicht zwischen Läufen, was für stabile Long-Run-Reports per JSON-Pinning oder manueller Korrektur abgefangen werden kann. Methodische Einordnung in [ADR-5](decisions.md#adr-5-llm-generierte-cluster-labels-pro-lauf-yaml-als-fallback).

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

In Produktion würde ich hier einen Retry Wrapper mit exponentieller Backoff Strategie ergänzen, was im aktuellen Stand fehlt.

### Dry Run

`brief.py --dry-run` schreibt für jeden Cluster einen Stub mit den Top Keywords und einer Notiz, dass kein API Aufruf stattgefunden hat. Nützlich zum Testen der Pipeline ohne API Kosten und in CI Umgebungen ohne Key.

## 8. Schritt 5: Report

`report.py` erzeugt eine einzelne `output/reporting/index.html`, die alle Pipeline Artefakte konsolidiert: KPI Boxen oben, sortierte Cluster Tabelle in der Mitte, eingebettete Charts unten, Link auf die interaktive Karte.

Bewusst keine Frontend Framework Abhängigkeit. Es ist eine einfache HTML Datei mit Inline CSS, die in jedem Browser funktioniert, sich an Stakeholder verschicken lässt und in einer Slack Nachricht klickbar bleibt. Wenn das später als Dashboard in einem Reporting Stack landen soll, ist das Markup einfach genug, um es nach Looker Studio oder Metabase zu portieren.

## 9. Validierung

Drei Validierungs-Ebenen, von leichtgewichtig zu schwergewichtig.

### Quantitativ: Silhouette Score

Silhouette misst, wie gut Cluster getrennt sind, von -1 (schlecht) bis +1 (perfekt).

| Setup | Silhouette |
|---|---|
| HDBSCAN-Kern (428 Keywords, vor Soft-Assignment) | 0,647 |
| Alle 500 (nach Soft-Assignment) | 0,570 |
| Ward Hierarchical (k=12) | 0,590 |

0,647 ist für reale Textdaten sehr gut. Zur Einordnung: Werte über 0,5 gelten als belastbare Cluster. Der Drop auf 0,570 nach Soft-Assignment ist erwartet — die 72 Rand-Keywords liegen per Definition näher an einer Cluster-Grenze. Beide Werte liegen über Ward(k=12) bei 0,590.

### Quantitativ: Übereinstimmung mit Alternative

Wie ähnlich sind die HDBSCAN Cluster den ursprünglich vom LLM kuratierten Cluster Definitionen?

| Vergleich | ARI | NMI |
|---|---|---|
| HDBSCAN gegen LLM Cluster (HDBSCAN-Kern) | 0,143 | 0,342 |
| HDBSCAN gegen Ward Hierarchical (k=10, alle 500) | 0,811 | (nicht erhoben) |

ARI ist konservativer als NMI, also ARI < NMI ist normal. Die LLM-vs-HDBSCAN-Werte sind erwartet niedrig: HDBSCAN findet andere Cluster-Grenzen als die LLM-Klassifikation, das ist methodisch interessant und keineswegs ein Fehler. Beide sind gültige Sichten auf die Daten. Der ARI von 0,786 zwischen HDBSCAN und Ward(k=10) zeigt zugleich, dass zwei mathematisch unabhängige Verfahren auf großer Mehrheit übereinstimmen.

Ein Beispiel: Der ursprüngliche LLM Cluster `cluster_03` („Recruiting & Bewerbermanagement") wird von HDBSCAN in zwei Cluster aufgeteilt („KI-gestützte Recruiting-Automatisierung" und „HR- und Bewerbermanagementsoftware KMU"), weil ATS- und SaaS-Begriffe semantisch näher an Software-Kategorien liegen als an Recruiting-Workflows. Das ist eine empirische Erkenntnis, die ohne diese Analyse nicht sichtbar wäre.

### Qualitativ: Manuelle Spot Checks

Ich habe für jeden der 13 Cluster die Top 10 Keywords gelesen und gegen das LLM-generierte Label gegengeprüft. Ergebnis:

- 11 von 13 Clustern sind eindeutig sinnvoll und sauber. Beispiel Cluster 0 (Factoring Buchhaltung und Genehmigung): `factoring buchen`, `factoring erlaubnis`, `offenes factoring`. Beispiel Cluster 1 (Zeiterfassung und Zeitarbeitssoftware): `zeiterfassung software`, `mobile zeiterfassung`, `zeitarbeitssoftware`.
- Cluster 4 (Sammelthemen Lohnabrechnung und Recruiting) ist vom LLM transparent als „Sammelthemen" gelabelt — enthält `aüg`, `bewerber finden`, `lohnabrechnung sage`, `indeed alternative`, `offboarding prozess`. Empfohlene Bearbeitung: Top-Keywords einzeln, nicht als Pillar.
- Cluster 12 (Sammelthemen Zeitarbeit Software und Finanzierung) ist mit 97 Keywords der größte Cluster. Bündelt „Zeitarbeit + X" Kombinationen aus Software, Factoring, CRM, Lohn. Vom LLM transparent als „Sammelthemen" gelabelt. Empfohlen: Sub-Clustering vor Bearbeitung. Vollständige pro-Cluster-Empfehlung in [`results.md`](results.md).

## 10. Top Empfehlungen aus diesem Lauf

Drei aus den 13 Clustern, sortiert nach Hebel für zvoove. Eine vollständige Cluster-Tabelle mit Empfehlung pro Cluster steht in [`results.md`](results.md).

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

Was tun: Hub-Pillar `/wissen/digitalisierung-personaldienstleistung/`, der gezielt Awareness-Traffic in die kommerziellen Cluster 1 (Zeitarbeitssoftware), 10 (HR-Software) und 3 (zvoove) überführt. Mittlere KD und niedrige kommerzielle Dichte machen das zum klassischen Top-of-Funnel-Eingang. Priority 16,8 — einer der hebelstärksten Cluster.

Revenue Hypothese: Pipeline-Influence statt direkte Conversion. Über 6 bis 12 Monate erwartbar: Brand-Lift-Wirkung und gestützte Brand-Suchen. Geschäftsführer recherchieren Digitalisierungs-Schritte genau dann, wenn ein Software-Wechsel ansteht.

## 11. Wie das in den Revenue Stack passt

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

## 12. Cost und Ops

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

## Anhang: weitere Dokumente

- [`methodology.md`](methodology.md): Parameter Sweep Tabelle, Reproduktion, statistische Validierung
- [`results.md`](results.md): vollständiger 13-Cluster-Katalog mit Empfehlung pro Cluster
- [`architecture.md`](architecture.md): Pipeline Diagramm, Datenfluss, Integration
- [`decisions.md`](decisions.md): Architecture Decision Records
