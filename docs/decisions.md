# Architecture Decisions (ADRs)

Knappe Architecture Decision Records für die wichtigsten Entscheidungen in dieser Pipeline. Jede ADR folgt dem gleichen Muster: Kontext, Entscheidung, Alternativen, Konsequenzen.

## ADR-1: HDBSCAN statt k-means für das Clustering

**Kontext.** 500 deutsche SEO Keywords sollen thematisch gruppiert werden. Die Anzahl der Cluster ist nicht vorab bekannt. Manche Keywords passen zu keinem Thema klar.

**Entscheidung.** HDBSCAN.

**Alternativen geprüft.**

- k-means: braucht vorgegebenes k, keine Rauschen-Klasse
- DBSCAN: globaler `eps`, kann variable Cluster-Dichte nicht handhaben
- Agglomerative (Ward): braucht vorgegebenes k, keine Rauschen-Klasse

**Konsequenzen.**

- Pro: 10 Cluster aus den Daten heraus. 38 (lokal) bis 40 (CI) echte Ausreißer als Rauschen markiert. Die kleine Abweichung zwischen Plattformen liegt an unterschiedlichen BLAS-Implementierungen, nicht an einem Fehler. Begründung in [`methodology.md`](methodology.md).
- Pro: Variable Cluster-Dichte wird verarbeitet (zvoove Marken-Cluster ist eng, Branche-Sammelcluster ist breit).
- Contra: Hyperparameter `min_cluster_size` und `min_samples` müssen gesweept werden.

Sweep Ergebnis dokumentiert in [`methodology.md`](methodology.md).

## ADR-2: UMAP statt PCA oder t-SNE

**Kontext.** 384-dimensionale Embeddings müssen für Density-based Clustering reduziert werden. Density-based Clustering funktioniert in hohen Dimensionen schlecht, weil alle Abstände ähnlich groß werden.

**Entscheidung.** UMAP, mit zwei separaten Reduktionen: 5D fürs Clustering, 2D für die Karte.

**Alternativen geprüft.**

- PCA: schnell, deterministisch, aber verliert lokale Struktur (optimiert globale Varianz)
- t-SNE: gut für Visualisierung, aber Abstände sind nicht interpretierbar; der Algorithmus ist nicht-deterministisch ohne aufwendige Initialisierung

**Konsequenzen.**

- Pro: erhält lokale plus globale Struktur, deterministisch mit `random_state`, Abstände sind lokal interpretierbar.
- Pro: zwei Reduktionen erlauben jeweils optimale Parameter (`min_dist` unterschiedlich für Clustering vs. Karte).
- Contra: etwas langsamer als PCA, mehr Hyperparameter.

## ADR-3: Multilingual MiniLM L12 statt L6 oder größere Modelle

**Kontext.** Embedding-Modell für deutsche Keywords.

**Entscheidung.** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (120 MB, 384 Dimensionen).

**Alternativen geprüft.**

- `all-MiniLM-L6-v2`: nur Englisch, deutsche Komposita schwach
- `intfloat/multilingual-e5-large`: 2,3 GB, vermutlich höhere Qualität

**Konsequenzen.**

- Pro: läuft auf jedem Laptop ohne GPU in Sekunden.
- Pro: ausreichend für Cluster-Bildung, validiert über Silhouette und Spot Checks.
- Contra: nicht state of the art. Bei Skalierung auf 5000 Keywords oder mehrsprachigem Kontext lohnt sich ein Upgrade.

Backlog: Vergleichslauf mit `multilingual-e5-large` zur Quantifizierung des Qualitätsunterschieds.

## ADR-4: Heuristische SV/KD/CPC Schätzung als Default, DataForSEO optional

**Kontext.** Pro Keyword werden Suchvolumen, Keyword Difficulty, CPC gebraucht. DataForSEO kostet Geld, eine Heuristik ist kostenfrei.

**Entscheidung.** Deterministische Heuristik als Default (SHA256 Hash als Seed). DataForSEO als optionaler `--provider dataforseo` Modus.

**Alternativen geprüft.**

- DataForSEO als Default: zu teuer für die Iteration; jeder Lauf kostet ungefähr 0,75 USD
- Reine LLM-Schätzung: nicht reproduzierbar, schwierig zu validieren

**Konsequenzen.**

- Pro: kostenfreie, reproduzierbare Pipeline. Spalte `data_source` markiert klar, was geschätzt ist.
- Pro: Live-Daten optional verfügbar für die finale Lieferung.
- Contra: Heuristik-Werte sind nicht real, was bei der Priorisierung zu Verzerrung führen kann.

In Produktion würde `data_source` ein Filter sein: wenn alle Daten DataForSEO sind, ist die Priorisierung verlässlicher.

## ADR-5: Manuelle Cluster Labels statt LLM-generiert

**Kontext.** Pro Cluster braucht es ein menschenlesbares Label.

**Entscheidung.** Manuelle Labels, abgelegt als Dictionary in `src/cluster.py`. EN und DE.

**Alternativen geprüft.**

- LLM-generiert pro Lauf: skaliert, aber Labels variieren zwischen Läufen, was die Reproduzierbarkeit von Reports erschwert
- Top-Term basiert (häufigste Wörter): schwach, weil die Top Terms oft stoppwort-ähnlich sind

**Konsequenzen.**

- Pro: stabil zwischen Läufen, kuratiert auf zvoove Geschäfts-Logik, qualitativ deutlich besser als Auto-Labeling.
- Contra: skaliert nicht über 50 Cluster.

Backlog: bei Skalierung Hybrid-Ansatz mit LLM-Vorschlag und manueller Korrektur in einem `cluster_labels.yaml`.

## ADR-6: Discover Schritt als Stub, nicht als Live Scraper

**Kontext.** Der Aufgaben-Brief verlangt Ableitung aus dem zvoove Blog. Ein robuster Live Scraper für `zvoove.de/wissen/blog` ist Engineering-Aufwand mit vielen Fallunterscheidungen (Pagination, Bot Detection, Layout-Änderungen).

**Entscheidung.** Discover als Stub mit `--source manual` und kuratierter `data/keywords.manual.csv`. `--source live` ist explizit nicht implementiert.

**Alternativen geprüft.**

- Schnell-Scraper mit BeautifulSoup, der bei jeder Layout-Änderung bricht: nicht produktionswürdig
- Headless Browser (Playwright): robust, aber Engineering-Aufwand für Demo zu hoch

**Konsequenzen.**

- Pro: Pipeline läuft heute end-to-end auf einem realistischen Datensatz, der nahe an dem ist, was ein Live-Lauf produzieren würde.
- Pro: Transparenz. README und CASE_STUDY benennen den Stub klar.
- Contra: das Hauptthema (Ableitung aus dem Blog) ist nicht live demonstriert. Genau dieser Trade-off ist Teil der Bewerbungs-Geschichte.

Backlog: höchste Priorität für die nächste Iteration.

## ADR-7: Briefs als Markdown statt HTML

**Kontext.** Pro Cluster ein Content Brief, der an die Redaktion geht.

**Entscheidung.** Markdown.

**Alternativen geprüft.**

- HTML wie im ursprünglichen `_build_briefings.py`: zu viel Boilerplate, schlechter editierbar
- Notion / Airtable Direkt-Import: Lock-in an ein Tool

**Konsequenzen.**

- Pro: pure-text, editierbar, in jedem CMS importierbar (Sanity, Contentful, WordPress, Notion).
- Pro: in Slack lesbar, in Pull Requests sinnvoll diff-bar.
- Contra: weniger visuelle Polish als HTML. Für die Redaktion ist Markdown aber Standard.

## ADR-8: Snapshot Mechanismus statt Datenbank für Persistenz

**Kontext.** Pipeline-Läufe produzieren Artefakte (CSVs, HTMLs). Mehrere Läufe sollen dokumentiert sein.

**Entscheidung.** `output/_archive/<run-id>/` mit gepinnten Snapshots. Pro Lauf wird der vorherige Output kopiert, bevor er überschrieben wird.

**Alternativen geprüft.**

- SQLite für Run Log: einfacher, aber bricht das "alles im Dateisystem" Pattern und braucht zusätzliches Tooling
- Postgres mit Alembic: zu schwer für eine Demo

**Konsequenzen.**

- Pro: keine zusätzliche Abhängigkeit, alles git-bar, alles im Browser durchklickbar.
- Pro: Snapshot-Historie ist Teil des Repos und damit Teil der Bewerbungs-Geschichte (rekonstruierter manueller Lauf von 2026-04-27 ist gepinnt).
- Contra: skaliert nicht über 20 bis 30 Läufe (Repo wird zu groß).

In Produktion würde nur der aktuelle Stand im Git landen, Snapshots würden in einen S3 Bucket umziehen.

## ADR-9: Prompt Caching für Brief-Generierung

**Kontext.** Pro Lauf werden 10 Briefs generiert, jeweils mit einem ungefähr 800-Token System Prompt, der das Brief-Format beschreibt. Das ist 10-mal derselbe System Prompt.

**Entscheidung.** Anthropic Prompt Caching auf dem System Block. Das technische Mittel dafür ist ein zusätzliches Feld `cache_control: ephemeral` im API Request. Es signalisiert dem Modell: "Dieser Block soll im Cache gehalten werden." Ab dem zweiten Aufruf wird der System Prompt aus dem Cache gelesen statt neu tokenisiert.

**Alternativen geprüft.**

- Kein Caching: jeder Aufruf zahlt den vollen System Prompt
- Eigener Cache (Datei oder Redis): unnötig, Anthropic bietet das nativ

**Konsequenzen.**

- Pro: ungefähr 90 Prozent Token-Ersparnis auf den gecachten Anteil. Bei 10 Clustern ungefähr 6000 gecachte Tokens.
- Pro: schnellere Antworten auf Folge-Aufrufe.
- Contra: minimale Komplexität (ein zusätzliches Feld im Request).

## ADR-10: Plotly für interaktive Karte, matplotlib für PNG Charts

**Kontext.** Visualisierung muss sowohl interaktiv (für Stakeholder) als auch statisch (für Reports und Slides) verfügbar sein.

**Entscheidung.** Plotly für die interaktive HTML-Karte, matplotlib für die 6 PNG-Diagnosecharts.

**Alternativen geprüft.**

- Nur Plotly: PNGs aus Plotly haben unzuverlässige Schriftgrößen über Plattformen
- Nur matplotlib: keine native Interaktivität ohne Bokeh oder Streamlit

**Konsequenzen.**

- Pro: jedes Tool für seinen Zweck. Plotly liefert die Klick-Karte, matplotlib liefert die saubere statische Visualisierung.
- Pro: keine zusätzliche Server-Komponente nötig (Plotly HTML ist self-contained, matplotlib speichert direkt PNG).
- Contra: zwei Plotting-Bibliotheken in der Pipeline.

## ADR-11: Pluggable LLM Provider mit drei Implementierungen

**Kontext.** Die Brief-Generierung braucht einen Sprachmodell-Aufruf. Es gibt drei realistische Wege:

1. **Anthropic API Key.** Anthropic SDK plus `ANTHROPIC_API_KEY`, separate pay-per-token Abrechnung.
2. **OpenAI API Key.** OpenAI SDK plus `OPENAI_API_KEY`, separate pay-per-token Abrechnung.
3. **Claude Subscription.** Das `claude-agent-sdk` nutzt eine lokale Claude Code Installation als Subprocess, authentifiziert über ein Max- oder Pro-Abo, keine separate Abrechnung.

**Entscheidung.** Pluggable Provider-Abstraktion. `BriefProvider` als Basisklasse, drei konkrete Implementierungen (`ApiKeyProvider`, `OpenAIProvider`, `AgentSdkProvider`), Auswahl per CLI-Flag `--provider {api,openai,max}`.

Default: `api` (Anthropic). In der DACH B2B SaaS Welt ist Anthropic für Inhalts-Erzeugung etabliert, und Claude generiert deutsche Texte mit der gewünschten pragmatischen Tonalität.

**Alternativen geprüft.**

- Nur Anthropic API Key: Lock-in. Falls zvoove intern OpenAI bereits einsetzt, will man nicht doppelt zahlen.
- Nur Subscription: nicht in CI nutzbar.
- LangChain als Universal-Wrapper: zu schwer für ein Case Study Projekt, zusätzliche Abhängigkeit, weniger Kontrolle über Prompt-Caching-Spezifika.

**Konsequenzen.**

| | Anthropic API | OpenAI API | Claude Subscription |
|---|---|---|---|
| Abrechnung | pay-per-token | pay-per-token | Bestehendes Max/Pro-Abo |
| CI-tauglich | Ja | Ja | Nein (braucht CLI Session) |
| Serverless-tauglich | Ja | Ja | Nein |
| Prompt Caching | explizit über `cache_control: ephemeral` | automatisch ab 1024 Token Prefix | nicht im SDK exponiert |
| Kosten pro 10-Cluster Lauf | ca. 0,15 USD | ca. 0,12 USD | 0 USD (im Abo) |

**Empfehlung für Produktion.** API Key (Anthropic oder OpenAI je nach internem Stack). Drei Gründe: CI/CD-Reproduzierbarkeit (ein GitHub Actions Runner kann keine CLI Session halten), Kosten-Transparenz (pay-per-token ist linear prognostizierbar) und Provider-Wechsel ohne Code-Änderung (ein CLI-Flag plus neuer API Key reicht).

**Hinweis zur Lieferung.** Die 10 Briefs in `output/briefings/` wurden über die Subscription-Variante erzeugt (Claude Code Session des Autors). Der Inhalt ist identisch mit dem, was ein API-Aufruf produziert hätte, weil derselbe System Prompt verwendet wurde. Im Code bleibt die API-Key-Variante der dokumentierte Default.

Ein neuer Provider (z.B. Mistral) braucht eine Klasse mit drei Methoden (`__init__`, `generate`, `name`) plus eine Zeile in `make_provider()`. Kein anderes Modul ändert sich.

## ADR-12: Konfiguration über Environment Variables (Twelve-Factor)

**Kontext.** Pipeline-Settings (Provider, Modell, Hyperparameter) waren als Modul-Konstanten (`UMAP_N_NEIGHBORS = 15`) plus CLI-Flags verteilt. Jede Hyperparameter-Änderung bedeutete einen Code-Edit.

**Entscheidung.** Zentrale `Settings`-Klasse in `src/config.py` via Pydantic. Werte kommen aus dem Environment mit Prefix `PIPELINE_`. Lokal per `.env` Datei, in CI per GitHub Actions Secrets und Workflow-Inputs, in Produktion über die Plattform-Mechanik (Docker, Kubernetes, Lambda).

Secrets (API Keys) bleiben davon getrennt und werden direkt von den Modulen gelesen, die sie brauchen. Sie landen damit nie in einem versehentlichen Settings-Dump.

**Alternativen geprüft.**

- YAML/TOML Konfigurationsdatei: natürliche Hierarchie, Inline-Kommentare, aber nicht 12-Factor-konform für Cloud-Deployments und unhandlich für Per-Deployment-Overrides.
- CLI-Flags als einzige Schnittstelle: funktioniert lokal, aber unhandlich in CI.

**Konsequenzen.**

| | ENV (gewählt) | YAML/TOML | CLI nur |
|---|---|---|---|
| Cloud-Native | sehr gut | Volume-Mount nötig | nicht praktikabel |
| GitHub Secrets | trivial | umständlich | trivial |
| Per-Deployment-Overrides | trivial | extra Mechanismus | bei jedem Aufruf nötig |
| Inline-Kommentare | nein, in `.env.example` | ja | nicht relevant |

**Präzedenz-Reihenfolge** (höchste zuerst):

```
CLI-Flag  >  Shell-Env  >  .env Datei  >  Code-Default in src/config.py
```

`PIPELINE_BRIEF_PROVIDER=openai` in `.env` gilt, kann von einer Shell-Umgebung übersteuert werden, kann von einem CLI-Flag `--brief-provider api` übersteuert werden.

## ADR-13: Strukturiertes Logging über stdlib `logging` statt `print()`

**Kontext.** In der ersten Iteration verwendeten alle Module `print()` mit `[mod] message` Prefixen. Das ist für lokales Debugging OK, aber in Produktion und in CI-Logs unhandlich: keine Log Levels (WARN von INFO nicht trennbar), keine Timestamps, keine strukturierten Felder, keine Möglichkeit, eine Library zu silencen.

**Entscheidung.** stdlib `logging` mit zentraler Konfiguration in `src/logging_config.py`. Jedes Modul hat sein eigenes `logger = logging.getLogger(__name__)`. Format: `Zeitstempel | Modul-Name | Level | Nachricht`. Verbosity über `PIPELINE_LOG_LEVEL` env var (default INFO).

**Alternativen geprüft.**

- `loguru`: schöne API, aber zusätzliche Abhängigkeit für minimalen Mehrwert.
- `structlog`: gut für JSON-strukturiertes Logging, aber Overkill für eine Pipeline mit fünf Skripten.
- `print()` weiter: keine Levels, kein Filter, keine zentrale Steuerung.

**Konsequenzen.**

- Pro: Standard-Werkzeug, jeder Engineer kennt es, kein Lock-in.
- Pro: Library-Logger lassen sich gezielt silencen (`urllib3`, `httpx`, `transformers` werden auf `WARNING` gesetzt).
- Pro: `PIPELINE_LOG_LEVEL=DEBUG` erhöht die Verbosity pro Run ohne Code-Änderung.
- Pro: In CI ist das Format reproduzierbar grep-bar.
- Contra: Format ist noch nicht JSON. Bei einem Production-Log-Aggregator (Loki, Datadog) wäre JSON besser. Backlog-Punkt.

**Beispiel.**

```
2026-04-29 12:34:56 | cluster.embed        | INFO  | encoding 500 keywords with MiniLM-L12
2026-04-29 12:34:58 | cluster.embed        | INFO  | wrote output/clustering/embeddings.npy, shape=(500, 384)
2026-04-29 12:35:02 | brief.ApiKeyProvider | WARN  | RateLimitError on attempt 1/5: 429 (retrying in 2.1s)
2026-04-29 12:35:04 | brief                | INFO  | wrote output/briefings/cluster_05.md (3204 chars, via api)
```

## ADR-14: Retry-Wrapper mit exponentieller Backoff für API Calls

**Kontext.** Brief-Generierung macht 10 sequentielle API Calls pro Lauf. Jeder kann mit transienten Fehlern scheitern (Rate Limit 429, 5xx Status, Connection Timeout). Ohne Retry bricht der erste Fehler den ganzen Lauf ab.

**Entscheidung.** Eigener Retry-Decorator `@with_retry()` in `src/retry.py`. Stdlib only, keine externe Abhängigkeit (`tenacity` wäre einfacher, aber 70 Zeilen eigener Code zeigen den Mechanismus klarer).

Standard-Verhalten:
- Max 5 Versuche
- Exponential Backoff: 2s, 4s, 8s, 16s, 32s (plus 25 Prozent Jitter)
- Cap bei 60 Sekunden pro Wartezeit
- Honor `Retry-After` Header wenn vorhanden
- Nicht-transiente Fehler (z.B. `ValueError`, `AuthError`) propagieren sofort

Konfigurierbar über `PIPELINE_BRIEF_RETRY_*` env vars (max_attempts, base_delay, max_delay, multiplier).

**Alternativen geprüft.**

- `tenacity`: ausgereift, mehr Features. Aber zusätzliche Abhängigkeit für ein klar abgegrenztes Problem.
- `urllib3` Retry-Adapter: nur HTTP-Layer, geht nicht durch SDK-Wrapper hindurch.
- Keine Retry: in Produktion zu fragil.

**Konsequenzen.**

- Pro: Briefs sind robust gegen 429/529 ohne Pipeline-Abbruch.
- Pro: Stdlib only, ca. 70 Zeilen, leicht zu reviewen.
- Pro: Per-Deployment-konfigurierbar via Env Vars.
- Contra: Transient-Klassen-Erkennung ist Klassen-Namen-basiert (`RateLimitError`, `APITimeoutError` etc.). Wenn das SDK seine Klassen umbenennt, muss die Liste angepasst werden.

**Verwendung.**

```python
@with_retry()
def generate(self, system: str, user: str) -> str:
    msg = self._client.messages.create(...)
    return msg.content[0].text
```

`tests/test_retry.py` deckt ab: nicht-transiente Fehler propagieren, transiente Fehler werden bis zur erfolgreichen Antwort wiederholt, `max_attempts` wird respektiert, das Default-Predicate erkennt die Anthropic- und OpenAI-Klassennamen.
