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

- Pro: 10 Cluster aus den Daten heraus, 38 echte Ausreißer als Rauschen markiert.
- Pro: Variable Cluster-Dichte handhaben (zvoove Marken-Cluster ist eng, Branche-Sammelcluster ist breit).
- Contra: Hyperparameter `min_cluster_size` und `min_samples` müssen gesweept werden.

Sweep Ergebnis dokumentiert in [`methodology.md`](methodology.md).

## ADR-2: UMAP statt PCA oder t-SNE

**Kontext.** 384-dimensionale Embeddings müssen für density-based Clustering reduziert werden.

**Entscheidung.** UMAP, mit zwei separaten Reduktionen (5D fürs Clustering, 2D für die Karte).

**Alternativen geprüft.**

- PCA: schnell, deterministisch, aber verliert lokale Struktur (optimiert globale Varianz)
- t-SNE: gut für Visualisierung, aber Distanzen sind nicht interpretierbar, und nicht-deterministisch ohne aufwendige Initialisierung

**Konsequenzen.**

- Pro: erhält lokale plus globale Struktur, deterministisch mit `random_state`, distanzen interpretierbar.
- Pro: zwei Reduktionen erlauben jeweils optimale Parameter (`min_dist` unterschiedlich).
- Contra: etwas langsamer als PCA, mehr Hyperparameter.

## ADR-3: Multilingual MiniLM L12 statt L6 oder größere Modelle

**Kontext.** Embedding Modell für deutsche Keywords.

**Entscheidung.** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (120 MB, 384 Dimensionen).

**Alternativen geprüft.**

- `all-MiniLM-L6-v2`: nur Englisch, deutsche Komposita schwach
- `intfloat/multilingual-e5-large`: 2,3 GB, vermutlich höhere Qualität

**Konsequenzen.**

- Pro: läuft auf jedem Laptop ohne GPU in Sekunden.
- Pro: ausreichend für Cluster-Bildung, validiert über Silhouette und Spot Checks.
- Contra: nicht state of the art. Bei Skalierung auf 5000 Keywords oder mehrsprachigem Kontext (Englisch plus Deutsch) lohnt sich Upgrade.

Backlog: Vergleichslauf mit `multilingual-e5-large` zur Quantifizierung des Qualitätsunterschieds.

## ADR-4: Heuristische SV/KD/CPC Schätzung als Default, DataForSEO optional

**Kontext.** Pro Keyword werden Suchvolumen, Keyword Difficulty, CPC gebraucht. DataForSEO kostet Geld, eine Heuristik ist kostenfrei.

**Entscheidung.** Deterministische Heuristik als Default (SHA256 Hash als Seed). DataForSEO als optionaler `--provider dataforseo` Modus.

**Alternativen geprüft.**

- DataForSEO als Default: zu teuer für die Iteration, weil jeder Lauf ungefähr 0,75 USD kostet
- Reine LLM Schätzung: nicht reproduzierbar, schwierig zu validieren

**Konsequenzen.**

- Pro: kostenfreie, reproduzierbare Pipeline. Spalte `data_source` markiert klar, was geschätzt ist.
- Pro: Live Daten optional verfügbar für die finale Lieferung.
- Contra: Heuristik-Werte sind nicht real, was bei der Priorisierung zu Verzerrung führen kann.

In Produktion würde `data_source` ein Filter sein: wenn alle Daten DataForSEO sind, ist die Priorisierung verlässlicher.

## ADR-5: Manuelle Cluster Labels statt LLM-generiert

**Kontext.** Pro Cluster braucht es ein menschenlesbares Label.

**Entscheidung.** Manuelle Labels, abgelegt als Dictionary in `src/cluster.py`. EN und DE.

**Alternativen geprüft.**

- LLM-generiert pro Lauf: skaliert, aber Labels variieren zwischen Läufen, was die Reproduzierbarkeit von Reports erschwert
- Top-Term basiert (häufigste Wörter): schwach, weil die Top Terms oft stoppwörter-ähnlich sind

**Konsequenzen.**

- Pro: stabil zwischen Läufen, kuratiert auf zvoove Geschäfts-Logik, qualitativ deutlich besser als Auto-Labeling.
- Contra: skaliert nicht über 50 Cluster.

Backlog: bei Skalierung Hybrid-Ansatz mit LLM-Vorschlag und manueller Korrektur in einem `cluster_labels.yaml`.

## ADR-6: Discover Schritt als Stub, nicht als Live Scraper

**Kontext.** Aufgaben-Brief verlangt Ableitung aus dem zvoove Blog. Ein robuster Live Scraper für `zvoove.de/wissen/blog` ist Engineering Aufwand mit vielen Fallunterscheidungen (Pagination, Bot Detection, Layout Änderungen).

**Entscheidung.** Discover als Stub mit `--source manual` und kuratierter `data/keywords.manual.csv`. `--source live` ist explizit nicht implementiert.

**Alternativen geprüft.**

- Schnell-Scraper mit BeautifulSoup, der bei jeder Layout-Änderung bricht: nicht produktionswürdig
- Headless Browser (Playwright): robust aber Engineering Aufwand für Demo zu hoch

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

**Kontext.** Pipeline Läufe produzieren Artefakte (CSVs, HTMLs). Mehrere Läufe sollen dokumentiert sein.

**Entscheidung.** `output/_archive/<run-id>/` mit gepinnten Snapshots. Pro Lauf wird der vorherige Output kopiert, bevor er überschrieben wird.

**Alternativen geprüft.**

- SQLite für Run Log: einfacher, aber bricht das "alles im Dateisystem" Pattern und braucht zusätzliche Tooling
- Postgres mit Alembic: zu schwer für eine Demo

**Konsequenzen.**

- Pro: keine zusätzliche Abhängigkeit, alles git-bar, alles in einem Browser durchklickbar.
- Pro: Snapshot-Historie ist Teil des Repos und damit Teil der Bewerbungs-Geschichte (rekonstruierter manueller Lauf von 2026-04-27 ist gepinnt).
- Contra: skaliert nicht über 20 oder 30 Läufe (Repo wird zu groß).

In Produktion würde nur der aktuelle Stand im Git landen, Snapshots würden in einen S3 Bucket umziehen.

## ADR-9: Prompt Caching für Brief Generation

**Kontext.** Pro Lauf werden 10 Briefs generiert, jeweils mit einem ungefähr 800-Token System Prompt, der das Brief Format beschreibt. Das ist 10x derselbe System Prompt.

**Entscheidung.** Anthropic Prompt Caching auf dem System Block (`cache_control: ephemeral`).

**Alternativen geprüft.**

- Kein Caching: jeder Aufruf zahlt vollen System Prompt
- Eigener Cache (Datei oder Redis): unnötig, Anthropic bietet das nativ

**Konsequenzen.**

- Pro: 90 Prozent Token Ersparnis auf den gecachten Anteil. Bei 10 Cluster ungefähr 6000 gecachte Tokens.
- Pro: schnellere Responses auf Folge-Aufrufe.
- Contra: minimale Komplexität (ein zusätzliches Feld im Request).

## ADR-11: Pluggable LLM Provider mit drei Implementierungen

**Kontext.** Die Brief-Generierung braucht einen Sprachmodell-Aufruf. Es gibt drei realistische Wege:

1. **Anthropic API Key.** Anthropic SDK plus `ANTHROPIC_API_KEY` aus `console.anthropic.com`, separate pay-per-token Abrechnung.
2. **OpenAI API Key.** OpenAI SDK plus `OPENAI_API_KEY` aus `platform.openai.com`, separate pay-per-token Abrechnung.
3. **Claude Subscription.** `claude-agent-sdk` nutzt eine lokale Claude Code Installation als Subprocess, authentifiziert über das Max- oder Pro-Abo des Entwicklers, keine separate Abrechnung.

**Entscheidung.** Pluggable Provider-Abstraktion. `BriefProvider` als Basis-Klasse, drei konkrete Implementierungen (`ApiKeyProvider`, `OpenAIProvider`, `AgentSdkProvider`), Auswahl per CLI-Flag `--provider {api,openai,max}`.

Default: `api` (Anthropic). Begründung: in der DACH B2B SaaS Welt ist Anthropic für Inhalts-Erzeugung etabliert, und Claude generiert insbesondere deutsche Texte mit der gewünschten pragmatischen Tonalität.

**Alternativen geprüft.**

- Nur Anthropic API Key: einfacher, aber Lock-in. Falls zvoove intern OpenAI bereits einsetzt, will man nicht doppelt zahlen. Falls ein neues Modell von OpenAI später besser für deutsche Marketing-Texte ist, muss man die Pipeline erweitern.
- Nur Subscription: nicht in CI nutzbar.
- LangChain als Universal-Wrapper: zu schwer für ein Case Study Projekt, zusätzliche Abhängigkeit, weniger Kontrolle über Prompt-Caching-Spezifika.

**Konsequenzen.**

| | Anthropic API | OpenAI API | Claude Subscription |
|---|---|---|---|
| Abrechnung | pay-per-token, console.anthropic.com | pay-per-token, platform.openai.com | Bestehendes Max/Pro-Abo |
| CI-tauglich | Ja | Ja | Nein (braucht CLI Session) |
| Serverless-tauglich | Ja | Ja | Nein |
| Prompt Caching | explizit über `cache_control: ephemeral` | automatisch ab 1024 Tokens Prefix | nicht im SDK exponiert |
| Modell-Auswahl | per `--model claude-opus-4-7` etc. | per `--model gpt-5` etc. | Inherits aktive CC Session, nicht setzbar |
| Kosten pro 10-Cluster Lauf | ungefähr 0,15 USD | ungefähr 0,12 USD | 0 USD (im Abo) |
| Sprache Deutsch | sehr gut | sehr gut | sehr gut (gleiche Modell-Familie wie API) |

**Empfehlung für Produktion bei zvoove.** API Key (Anthropic ODER OpenAI je nach internem Stack). Drei Gründe:

1. **CI/CD-Reproduzierbarkeit.** Ein GitHub Actions Runner oder ein zvoove-internes CI-System kann keine Claude Code CLI-Session halten. API Key ist das einzige Pattern, das in Build-Pipelines funktioniert.
2. **Kosten-Transparenz.** Per-Token-Abrechnung skaliert linear mit Nutzung und ist im Provider-Console Tag-genau nachvollziehbar. Eine Subscription mit "Unlimited" Charakter ist schwerer zu prognostizieren oder umzulegen.
3. **Provider-Wechsel ist möglich.** Sollte sich ein Provider verschlechtern oder seine Preise erhöhen, ist der Switch eine Zeile CLI-Flag plus ein neuer API Key. Kein Code-Refactoring.

**Empfehlung für die Wahl Anthropic vs OpenAI.** Hängt vom internen Stack ab. Wenn zvoove bereits OpenAI für andere Use Cases nutzt, dort weitermachen (gemeinsame Abrechnung, gemeinsamer Audit-Trail). Sonst Anthropic, weil deren Modelle in DACH B2B SaaS Content gut etabliert sind und Prompt Caching explizit steuerbar ist.

**Hinweis zur Lieferung dieser Case Study.** Die 10 Briefs in `output/briefings/` sind während der Entwicklung über die Subscription-Variante erzeugt worden (über die Claude Code Session des Autors), nicht über einen API Key. Inhaltlich identisch mit dem, was der API-Aufruf produziert hätte, weil derselbe System Prompt verwendet wurde. Im Code-Pfad bleibt die API-Key-Variante der dokumentierte Default, weil das die Empfehlung für die produktive Nutzung ist.

**Provider hinzufügen.** Falls ein neuer Provider gebraucht wird (zum Beispiel Mistral, Gemini, lokales Llama), reicht eine neue Klasse:

```python
class MistralProvider(BriefProvider):
    name = "mistral"
    def __init__(self, model: str): ...
    def generate(self, system: str, user: str) -> str: ...
```

Plus eine Zeile in `make_provider()` und ein neuer Choice in den CLIs (`brief.py` und `pipeline.py`). Kein Code in den anderen Pipeline-Modulen ändert sich.

## ADR-10: Plotly für interaktive Karte, matplotlib für PNG Charts

**Kontext.** Visualisierung muss sowohl interaktiv (für die Stakeholder) als auch statisch (für Reports und Slides) verfügbar sein.

**Entscheidung.** Plotly für die interaktive HTML Karte, matplotlib für die 6 PNG Diagnose Charts.

**Alternativen geprüft.**

- Nur Plotly: PNGs aus Plotly haben unzuverlässige Schriftgrößen über Plattformen
- Nur matplotlib: keine native Interaktivität ohne Bokeh oder Streamlit

**Konsequenzen.**

- Pro: jedes Tool für seinen Zweck. Plotly liefert die Klick-Karte, matplotlib liefert die saubere statische Visualisierung.
- Pro: keine zusätzliche Server-Komponente nötig (Plotly HTML ist self-contained, matplotlib speichert direkt PNG).
- Contra: zwei Plotting Bibliotheken in der Pipeline. Eine zusätzliche Abhängigkeit.
