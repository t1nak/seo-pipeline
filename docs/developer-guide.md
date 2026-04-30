# Developer Guide

Diese Seite richtet sich an alle, die den Code lesen, ändern oder erweitern. Sie erklärt, **wie** der Code organisiert ist, **warum** er so geschnitten ist und welche Entscheidungen Wartbarkeit und Erweiterbarkeit absichern.

Die fachliche Begründung der Methodik (HDBSCAN, UMAP, Hyperparameter) liegt in der [Methodik](methodology.md) bzw. den [Entscheidungen](decisions.md). Diese Seite hier ist die Brücke zwischen Architektur-Diagramm und Quellcode.

!!! tip "Wo schaue ich zuerst rein?"
    1. [`pipeline.py`](https://github.com/t1nak/seo-pipeline/blob/main/pipeline.py) — die End-to-End-Orchestrierung.
    2. [`src/config.py`](https://github.com/t1nak/seo-pipeline/blob/main/src/config.py) — wo alle Schalter wohnen.
    3. Die Module unter `src/` haben jeweils eine Modul-Docstring, die ihren Zweck, ihre Inputs/Outputs und ihre Sub-CLI dokumentiert.

## 1. Repository auf einen Blick

```
seo-pipeline/
├── pipeline.py              # End-to-End-Orchestrator (1 CLI für alle 5 Schritte)
├── src/
│   ├── config.py            # Pydantic Settings, env-getrieben
│   ├── logging_config.py    # einmalige Root-Logger-Konfiguration
│   ├── retry.py             # Decorator: exponential backoff für Provider-Calls
│   ├── discover.py          # Schritt 1: Keyword-Quelle (manual | live)
│   ├── enrich.py            # Schritt 2: SV/KD/CPC anreichern (estimate | dataforseo)
│   ├── cluster.py           # Schritt 3: embed → UMAP → HDBSCAN → label → profile → charts → viz
│   ├── cluster_viz.py       # Plotly-Klick-Map (von cluster.py aufgerufen)
│   ├── subcluster.py        # zweiter HDBSCAN-Pass auf einen Cluster
│   ├── brief.py             # Schritt 4: LLM-Briefs (api | openai | max)
│   ├── briefs_html.py       # konsolidiertes Brief-Dashboard
│   └── report.py            # Schritt 5: KPI-Dashboard
├── tests/                   # pytest, ohne Netz, ohne API-Keys
├── data/                    # Eingabe-CSVs (gitignored ausser baseline)
├── output/                  # alle erzeugten Artefakte (CSV, PNG, HTML, MD)
└── docs/                    # diese MkDocs-Site
```

Drei Designprinzipien tragen die Struktur:

| Prinzip | Wo sichtbar | Was es bewirkt |
|---|---|---|
| **Ein Modul pro Pipeline-Schritt** | `src/discover.py`, `enrich.py`, `cluster.py`, `brief.py`, `report.py` | Jedes Modul ist isoliert testbar, hat eine eigene `python -m src.<schritt>` Sub-CLI und kann unabhängig redeployed werden. |
| **Artefakte über das Dateisystem** | `data/keywords.csv`, `output/clustering/*.npy`, `output/clustering/*.csv` | Schritte kommunizieren über CSV/NPY auf der Platte, nicht über In-Memory-Objekte. Erlaubt Re-Run einzelner Schritte und macht den Zustand inspizierbar. |
| **Provider sind austauschbar** | `brief.BriefProvider` Subklassen, `enrich.run(provider=...)`, `discover.discover_manual` vs `discover_live` | Externe Abhängigkeiten (Anthropic, OpenAI, DataForSEO, Claude Max) sind hinter einem Interface gekapselt. Wechsel über CLI-Flag oder Env-Var, kein Codepatch. |

## 2. Datenfluss zwischen den Schritten

Jeder Schritt liest klar definierte Dateien und schreibt klar definierte Dateien. Die Pfad-Konstanten stehen am Anfang jedes Moduls (`F_CLEAN`, `F_EMB`, `F_LABELED` etc. in `cluster.py`), damit Code und Doku eine einzige Quelle teilen.

```mermaid
flowchart LR
    M[data/keywords.manual.csv] --> D[discover.py]
    D --> K[data/keywords.csv]
    K --> E[enrich.py]
    E --> K
    K --> C1[cluster.step_clean]
    C1 --> CC[output/clustering/keywords_clean.csv]
    CC --> C2[cluster.step_embed]
    C2 --> EM[embeddings.npy]
    EM --> C3[cluster.step_reduce]
    C3 --> U5[umap_5d.npy]
    C3 --> U2[umap_2d.npy]
    U5 --> C4[cluster.step_cluster]
    C4 --> KL[keywords_labeled.csv]
    KL --> C5[cluster.step_profile]
    C5 --> P[cluster_profiles.csv]
    P --> B[brief.py]
    KL --> B
    B --> BR[output/briefings/cluster_NN.md]
    BR --> BH[briefs_html.py]
    P --> R[report.py]
    BR --> R
    R --> RH[output/reporting/index.html]
```

Was diese Grenze leistet:

- **Wiederholbarkeit:** Ein Schritt re-runnen heisst, seine Eingabedateien existieren noch. Kein implizites Setup.
- **Diagnose:** Bei Problemen reicht ein `head` auf das Zwischenartefakt, um zu wissen, ob der Fehler vor oder nach diesem Schritt liegt.
- **Parallelisierbarkeit:** In CI laufen `cluster.charts` und `cluster.viz` heute sequenziell, könnten aber auf der gleichen Datenbasis parallel laufen, ohne dass Code geändert werden müsste.

## 3. Konfigurations-Modell

Alle Schalter wohnen in einer Datei: `src/config.py`. Das ist der **Twelve-Factor App** Stil — Konfiguration steht im Environment, nicht im Code.

### Präzedenz, höchste zuerst

1. **CLI-Flag** (`--brief-provider openai` in `pipeline.py`)
2. **Echte Environment-Variable** (`PIPELINE_BRIEF_PROVIDER=openai`)
3. **`.env` Datei** im Repo-Root (lokal, nicht versioniert)
4. **Defaults** in der `Settings` Klasse selbst

### Beispiel: Cluster-Hyperparameter überschreiben

```bash
# Per Lauf, ohne Code-Änderung
export PIPELINE_CLUSTER_HDBSCAN_MCS=10
export PIPELINE_CLUSTER_HDBSCAN_METHOD=leaf
python pipeline.py --step cluster
```

### Was bewusst **nicht** in `Settings` lebt

API-Keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DATAFORSEO_LOGIN`/`_PASSWORD`, `STATICRYPT_PASSWORD`) bleiben rohe Environment-Variablen. Sie tauchen nie in einem typisierten Settings-Dump auf, was versehentliche Logs, Repr-Strings und Fehler-Traces sauber hält.

### Wartbarkeit

| Wenn du ... | dann ... |
|---|---|
| einen neuen Schalter brauchst | Feld in `Settings` ergänzen, Typannotation und Default setzen — Pydantic validiert beim Start. |
| weisst, dass ein Default nur in CI anders sein soll | als Env-Var im Workflow setzen, Default unverändert lassen. Niemand patcht Code dafür. |
| eine Setting umbenennst | grep auf `settings.<altername>` plus Übergang dokumentieren in `decisions.md`. |

## 4. Logging und Beobachtbarkeit

`src/logging_config.py` ist die **einzige** Stelle, an der der Root-Logger angefasst wird. Alle Module folgen dem gleichen Muster:

```python
import logging
logger = logging.getLogger(__name__)
logger.info("doing work")
```

Das hat drei Konsequenzen:

1. **Strukturiertes, kompaktes Format** überall: `2026-04-29 12:34:56 | cluster.embed | INFO | encoding 500 keywords`. Der `_ShortNameFilter` schneidet das `src.` Präfix ab, damit die Spalten ausgerichtet bleiben.
2. **Bibliotheks-Lärm gedämpft**: `urllib3`, `httpx`, `anthropic`, `sentence_transformers` sind hartcodiert auf `WARNING`, sonst würden sie in INFO-Modus den eigenen Pipeline-Output begraben.
3. **Verbosität pro Lauf**: `--log-level DEBUG` in `pipeline.py` oder `PIPELINE_LOG_LEVEL=DEBUG` setzt die Stufe ohne Code-Änderung.

`setup_logging()` ist idempotent (`_CONFIGURED` Flag). Mehrfaches Aufrufen schadet nichts, was Tests und Notebook-Imports unkritisch macht.

## 5. Provider-Abstraktion (Brief-Schritt)

Der LLM-Aufruf ist die Stelle, an der sich Anbieter, Preise, Kontextfenster und Auth-Modelle am häufigsten ändern. Daher ist genau dieser Punkt mit einem schmalen Interface geschützt:

```python
class BriefProvider:
    name: str = "abstract"
    def generate(self, system: str, user: str) -> str: ...
```

Drei konkrete Implementierungen:

| Subklasse | Auth | CI-tauglich | Modellwahl | Caching |
|---|---|---|---|---|
| `ApiKeyProvider` | `ANTHROPIC_API_KEY` | ja | `--model claude-…` | Anthropic ephemeral cache |
| `OpenAIProvider` | `OPENAI_API_KEY` | ja | `--model gpt-…` | automatisch ab 1024 tok prefix |
| `AgentSdkProvider` | lokale Claude-Code-Session | nein, nur lokal | aus Session geerbt | nicht exponiert |

`make_provider(name, model)` ist die einzige Factory-Funktion. Wer einen vierten Provider hinzufügt (z.B. Mistral, lokales Llama), schreibt eine neue Subklasse und einen Eintrag in dieser Factory — sonst ändert sich nichts.

### Robustheit am Provider-Rand

Drei Schutzschichten gegen die Realität externer APIs:

1. **`with_retry` Decorator** auf `generate()` — exponentielles Backoff mit Jitter, honoriert `Retry-After` Header. Definiert in `src/retry.py` (rein Stdlib, ~70 Zeilen, kein externer Kram).
2. **Klassenname-Matching für transiente Fehler** — `retryable_default` matcht auf Substrings wie `"RateLimitError"`, `"OverloadedError"`, `"APITimeoutError"` ohne die SDKs zu importieren. Heisst: das Retry-Modul kennt den Anthropic SDK nicht, kann aber trotzdem dessen Fehlerklassen behandeln.
3. **`_strip_preamble` und `_looks_like_real_brief`** — defensive Helfer, die LLM-Antworten normalisieren (Vorrede entfernen) und beim Dry-Run nie einen echten Brief mit einem Stub überschreiben.

### Wartbarkeit

| Wenn du ... | dann ... |
|---|---|
| einen neuen LLM-Anbieter ergänzt | `BriefProvider` subklassen, in `make_provider` registrieren, optional `@with_retry` benutzen. CLI bleibt unverändert. |
| das System-Prompt änderst | nur `SYSTEM_PROMPT` in `brief.py` editieren. Prompt Caching profitiert davon, dass dieser Block stabil bleibt — Änderungen also bewusst sparsam. |
| die Retry-Policy in CI strenger willst | `PIPELINE_BRIEF_RETRY_MAX_ATTEMPTS=3` im Workflow. Kein Codepatch. |

## 6. Test-Strategie

`tests/` ist klein, aber gezielt. Vier Charakteristiken:

1. **Kein Netz, keine API-Keys.** Alles, was über das offene Internet geht, ist im Test über Fixtures abgeschnitten. CI darf nicht an einem Anthropic-Outage scheitern.
2. **Helfer-zentriert.** `test_brief_helpers.py` testet `_strip_preamble`, `_looks_like_real_brief` etc. — kleine, reine Funktionen, die schnell brechen wenn sich Annahmen über LLM-Output ändern.
3. **Settings-Singleton wird zwischen Tests resettet** (`conftest.py:reset_settings_singleton`). Sonst leaken `PIPELINE_*` Env-Vars zwischen Tests und das Verhalten wird nicht-deterministisch.
4. **Smoke-Test** (`test_smoke.py`) importiert alle Pipeline-Module ohne sie auszuführen. Fängt Import-Zeit-Fehler (fehlende Abhängigkeiten, Syntaxbruch) sofort.

Was bewusst **nicht** getestet wird: das Clustering-Ergebnis selbst. UMAP hat plattformbedingten Drift (gleicher `random_state`, andere CPU = andere Embeddings); ein Snapshot-Test würde in CI dauerhaft rot blinken. Stattdessen prüft die Methodik-Dokumentation die Plausibilität über Silhouette-Score und ARI-Vergleich.

## 7. GitHub Actions Workflows (CI/CD im Detail)

Im Repo liegen drei YAML-Workflows unter `.github/workflows/`. Sie sind so geschnitten, dass jeder einen klaren Zweck, einen klaren Trigger und einen klaren Kostenrahmen hat. Diese Trennung ist absichtlich — sie macht es schwer, versehentlich einen teuren Lauf auszulösen.

| Datei | Zweck | Trigger | Kosten / Lauf | Secrets nötig |
|---|---|---|---|---|
| `pipeline.yml` | 4 Schritte ohne LLM (Demo-Lauf) | `push` auf `main` (gefiltert) + manuell | 0 EUR | optional `DATAFORSEO_*` |
| `pipeline-full.yml` | Volle 5 Schritte mit Brief-Generierung | nur manuell (`workflow_dispatch`) | ~0,50 – 2 EUR | `ANTHROPIC_API_KEY` oder `OPENAI_API_KEY` |
| `docs.yml` | Baut MkDocs, verschlüsselt, deployt nach Pages | `push` auf `main` + manuell | 0 EUR | `STATICRYPT_PASSWORD` |

### 7.1 `pipeline.yml` — der kostenlose Demo-Lauf

Der schmalere der beiden Pipeline-Workflows. Lässt die ersten vier Schritte laufen (Discover → Enrich → Cluster → Report) und überspringt den Brief-Schritt, weil der Geld kostet.

**Trigger** (Zeilen 8–44):

```yaml
on:
  workflow_dispatch:                # manueller Knopf in der Actions-UI
    inputs:
      enrich_provider: ...          # estimate (frei) oder dataforseo (~0,75 USD)
      max_keywords: ...             # 100 / 250 / 500 / 1000
      cluster_mcs: ...              # 8 / 10 / 12 / 15 / 20 (HDBSCAN-Sweep)
  push:
    branches: [main]
    paths:                          # NUR wenn diese Pfade sich ändern
      - "src/**"
      - "pipeline.py"
      - "data/keywords.manual.csv"
      - "requirements.txt"
      - ".github/workflows/pipeline.yml"
```

Was an diesem Trigger-Block wichtig ist:

1. **Path-Filter unter `push`** — der Workflow läuft nicht bei jedem Commit, sondern nur, wenn Code, Pipeline-Skript, Baseline-Daten, Dependencies oder das Workflow-File selbst sich ändern. Spart Minuten und macht die Action-History les bar. Doku-Änderungen (`docs/**`) lösen ihn bewusst nicht aus — die werden vom `docs.yml` Workflow abgehandelt.
2. **`workflow_dispatch.inputs` mit `type: choice`** — die UI zwingt den Bediener auf eine erlaubte Auswahl statt freier Texteingabe. Verhindert Tippfehler in numerischen Feldern und erlaubt UI-Validierung pro Feld.
3. **Kein Cron-Trigger** — bewusst weggelassen. Wenn ein Scheduled-Run gewünscht wäre, hier ein `schedule: - cron: ...` ergänzen, aber dann Kostenstelle bedenken.

**`permissions: contents: read`** (Zeile 46–47) — Least Privilege. Der Workflow darf den Code lesen, sonst nichts. Keine Schreibrechte auf Issues, PRs, Pages oder Packages.

**`concurrency`** (Zeile 49–51):

```yaml
concurrency:
  group: pipeline-demo
  cancel-in-progress: false
```

Sorgt dafür, dass parallele Läufe sich nicht gegenseitig auf den Artefakten zertrampeln. `cancel-in-progress: false` heisst: ein neuer Lauf wartet, bis der alte fertig ist, statt ihn abzubrechen — wichtig, wenn der Lauf bereits API-Kosten produziert hat (gilt mehr für `pipeline-full`, hier defensiv auch gesetzt).

**`timeout-minutes: 25`** (Zeile 56) — harte Obergrenze. Wenn ein Lauf länger braucht (z.B. weil sentence-transformers ein neues Modell ziehen muss), bricht GitHub ab statt Stunden Compute zu verbrennen.

**Secrets-Verfügbarkeit** (Zeile 84–86):

```yaml
env:
  DATAFORSEO_LOGIN: ${{ secrets.DATAFORSEO_LOGIN }}
  DATAFORSEO_PASSWORD: ${{ secrets.DATAFORSEO_PASSWORD }}
```

Wenn das Secret im Repo nicht gesetzt ist, ist die Variable einfach leer. Der Code in `enrich.fetch_dataforseo` prüft das und wirft einen klaren Fehler. Heisst: das Workflow-File ist auch ohne DataForSEO-Account lauffähig, solange `enrich_provider=estimate` gewählt wird.

**Settings-Mapping** (Zeile 86–89):

```yaml
PIPELINE_ENRICH_PROVIDER: ${{ inputs.enrich_provider }}
PIPELINE_DISCOVER_MAX_KEYWORDS: ${{ inputs.max_keywords }}
PIPELINE_CLUSTER_HDBSCAN_MCS: ${{ inputs.cluster_mcs }}
```

Genau das Muster, das in Sektion 3 beschrieben ist: `inputs.<feld>` aus der Workflow-UI fliesst in `PIPELINE_*` Env-Vars, die Pydantic Settings beim Start liest. **Keine Code-Änderung** ist nötig, um einen anderen `mcs` zu testen — UI-Klick reicht.

Wichtiger Detail: Beim `push`-Trigger sind diese Inputs leer (es gab ja keine UI-Auswahl). Pydantic Settings fällt dann auf die Defaults aus `src/config.py` zurück. Das ist bewusst so — der Push-Lauf soll die Baseline reproduzieren.

**Modell-Cache** (Zeile 70–78):

```yaml
- name: Cache sentence-transformers model
  uses: actions/cache@v4
  with:
    path:
      - ~/.cache/huggingface
      - ~/.cache/torch/sentence_transformers
    key: st-${{ runner.os }}-paraphrase-multilingual-MiniLM-L12-v2
```

Spart 1–2 Minuten ab dem zweiten Lauf. Der Cache-Key enthält den Modellnamen — wenn das Embedding-Modell wechselt, wird der Cache automatisch invalidiert (alter Key trifft neue Datei nicht).

**Run-Summary** (Zeile 92–101) — kurze Auszüge der Cluster-Profile, KPIs und der Datei-Liste werden in das Action-Log geschrieben. So sieht man im Browser, was rauskam, ohne das Artefakt herunterzuladen.

**Artefakt-Upload** (Zeile 103–112):

```yaml
- name: Upload pipeline outputs
  uses: actions/upload-artifact@v4
  with:
    name: pipeline-output
    path:
      - data/keywords.csv
      - output/clustering/
      - output/reporting/
    retention-days: 14
    if-no-files-found: error
```

`if-no-files-found: error` ist ein wichtiger Schutz: wenn die Pipeline still gescheitert ist und nichts geschrieben hat, fällt das hier auf statt erst beim manuellen Download.

### 7.2 `pipeline-full.yml` — der bewusste, bezahlte Lauf

Inhaltlich derselbe Pipeline-Lauf wie `pipeline.yml`, aber inklusive des Brief-Schritts (LLM-Aufruf). Wegen der Kosten ist dieser Workflow strikt manuell.

**Kein Push-Trigger**, nur `workflow_dispatch` (Zeile 11–54). Im Header-Kommentar dokumentiert:

```yaml
# Warum kein push-Trigger: Brief-Step kostet Geld, jeder Lauf soll eine
# bewusste Entscheidung sein. Demo-Lauf ohne Brief: pipeline.yml.
```

**`dry_run` Eingabe** (Zeile 14–17):

```yaml
dry_run:
  description: "Test-Modus: kein LLM-Call, Stubs schreiben (kostenlos, gut für Verkabelungs-Test)"
  type: boolean
  default: false
```

Erlaubt einen kostenlosen Smoke-Test der ganzen Verkabelung, inklusive Brief-Schritt — der Code in `brief.run` schreibt dann Stub-Markdown statt echte Briefs. Default ist `false` (echter Lauf), aber der Bedienende kann gefahrlos die Pipeline-Mechanik durchprüfen.

**Provider-Auswahl mit CI-bewusster Filterung** (Zeile 18–24):

```yaml
brief_provider:
  description: "... max (Agent SDK) ist lokal-only und in CI nicht verfügbar."
  type: choice
  options:
    - api
    - openai
  default: api
```

Der dritte Provider (`max`, Claude Code Subscription) **fehlt absichtlich** in dieser Liste. Er braucht eine angemeldete lokale CLI-Session, die GitHub-Runner nicht haben. Statt das im Code zu prüfen und mit Fehler abzubrechen, ist die UI-Auswahl direkt gefiltert — ein „nicht nutzbar" Pfad wird gar nicht erst angeboten. Dokumentiert in der Description.

**Pre-Flight-Check des Provider-Secrets** (Zeile 80–101):

```yaml
- name: Verify provider secret
  if: ${{ !inputs.dry_run }}
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    BRIEF_PROVIDER: ${{ inputs.brief_provider }}
  run: |
    if [ "$BRIEF_PROVIDER" = "api" ]; then
      if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "::error::ANTHROPIC_API_KEY secret missing for --brief-provider api."
        exit 1
      fi
      echo "ANTHROPIC_API_KEY present (length: ${#ANTHROPIC_API_KEY})"
    elif [ "$BRIEF_PROVIDER" = "openai" ]; then
      ...
    fi
```

Vier wichtige Eigenschaften:

1. **`if: ${{ !inputs.dry_run }}`** — der Check wird bei `dry_run=true` übersprungen, weil dann gar kein Secret nötig ist.
2. **Frühes Scheitern** — wenn das Secret fehlt, bricht der Workflow hier ab statt drei Schritte später, mitten in `pip install`. `::error::` ist die GitHub-Annotation, die im UI rot hervorgehoben wird.
3. **Konkrete Handlungsanweisung** — die Fehlermeldung sagt, wo man das Secret eintragen muss („Settings -> Secrets and variables -> Actions").
4. **Keine Logleck** — `echo` druckt nur die **Länge** des Keys (`${#ANTHROPIC_API_KEY}`), niemals den Wert. Ein versehentliches `echo $ANTHROPIC_API_KEY` würde GitHub zwar auto-maskieren (Secret Masking), aber sich auf das Masking zu verlassen wäre fragil.

**Conditional CLI-Flag in Bash** (Zeile 125–126):

```yaml
run: |
  python pipeline.py ${{ inputs.dry_run && '--dry-run' || '' }}
```

Ternary-Ausdruck der GitHub-Expression-Sprache: bei `dry_run=true` wird `--dry-run` ans Kommando angehängt, sonst nichts. So bleibt `pipeline.py` ohne Sonderlogik für den CI-Modus.

### 7.3 `docs.yml` — Build, Encrypt, Deploy

Baut die MkDocs-Site, verschlüsselt sie mit StatiCrypt und deployt sie auf GitHub Pages.

**Trigger** (Zeile 3–6):

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
```

Kein Path-Filter — Doku-Änderungen sind für sich der Auslöser. Auch jeder Code-Push auf main triggert ihn (was harmlos ist, weil das Bauen schnell ist und nur die Doku-Site neu deployt).

**Erweiterte Permissions** (Zeile 8–11):

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

Drei spezifische Rechte:

- `contents: read` — Code lesen (Standard).
- `pages: write` — auf den GitHub-Pages-Endpoint deployen.
- `id-token: write` — OIDC-Token für die `actions/deploy-pages@v4` Action. Diese verwendet kein langlebiges Secret, sondern OpenID Connect, ein temporäres Token pro Lauf. Sicherer als ein PAT zu hinterlegen.

**Concurrency** (Zeile 13–15):

```yaml
concurrency:
  group: pages
  cancel-in-progress: false
```

Verhindert race conditions, wenn zwei Doku-Pushes hintereinander kommen — der zweite wartet, statt einen halb-deployten Stand zu produzieren.

**Build-Schritte** im Überblick:

| Schritt | Was er tut |
|---|---|
| Checkout + Setup Python | Standard, mit Pip-Cache |
| Install MkDocs | aus `requirements-docs.txt` (separate von `requirements.txt`, damit der Doku-Build keine ML-Abhängigkeiten braucht) |
| `mkdocs build --strict` | bricht bei toten Links und MkDocs-Warnings ab |
| Copy live artifacts | kopiert `output/` ins gebaute `site/` (siehe unten) |
| Setup Node + Install StatiCrypt | wegen NPM-Tooling |
| Encrypt site | StatiCrypt-Loop über alle HTML-Dateien |
| Upload artifact + Deploy | Standard Pages-Pipeline |

**Live-Artefakte einbinden** (Zeile 35–43):

```yaml
- name: Copy live artifacts into site
  # Preserve the existing URLs:
  #   /seo-pipeline/output/clustering/cluster_map.html
  #   /seo-pipeline/output/reporting/index.html
  # MkDocs serves docs/ only; copying output/ alongside the built site
  # keeps the live cluster map and report dashboard reachable.
  run: |
    cp -r output site/output
    cp .nojekyll site/.nojekyll
```

Wichtige Maintainability-Eigenschaft: die Pages-URL-Struktur ist explizit dokumentiert im Workflow-Kommentar. Wer in `mkdocs.yml` einen Link auf `/output/...` sieht und sich fragt „wie kommt das in den Build?", findet hier die Antwort.

`.nojekyll` ist nötig, damit GitHub Pages den Inhalt 1:1 ausliefert statt eine Jekyll-Verarbeitung zu triggern (die z.B. Dateien mit `_` Präfix verstecken würde).

**Encryption-Schritt im Detail** (Zeile 53–79):

```yaml
- name: Encrypt site with shared password
  env:
    STATICRYPT_PASSWORD: ${{ secrets.STATICRYPT_PASSWORD }}
  run: |
    # 1. Drop the search index (would leak content as plain JSON)
    rm -rf site/search

    # 2. Encrypt every HTML file in place. Loop because staticrypt's
    #    -r flag nests output under the input dir name, which would
    #    break Pages routing. One file at a time keeps paths flat.
    find site -type f -name '*.html' | while read -r f; do
      staticrypt "$f" \
        --short \
        --template-button "Show case study" \
        --template-instructions "Enter the access password ..." \
        --template-color-primary "#0f172a" \
        --template-color-secondary "#2dd4bf" \
        --directory "$(dirname "$f")"
    done

    # 3. Verify: a sampled file should now contain the StatiCrypt loader
    grep -q "staticrypt" site/index.html && echo "encryption OK"
```

Drei Aspekte, die hier subtil aber wichtig sind:

1. **Suchindex-Leak schliessen** (`rm -rf site/search`) — MkDocs Material legt einen JSON-Suchindex an, der den Volltext aller Seiten enthält. Den HTML-Wrapper kann StatiCrypt verschlüsseln, aber das JSON wäre weiterhin Klartext per HTTP zugänglich. Das Löschen des Suchindex ist die kostengünstigste Lösung — die Such-Funktion auf der Site ist damit weg, dafür ist die Inhalts-Sperre wirklich dicht. Ein expliziter Kommentar im Workflow erklärt das, damit niemand die Such-Funktion „repariert", ohne den Trade-off zu sehen.
2. **Per-File-Loop** statt rekursivem Encrypt — StatiCrypts `-r` Flag würde die Output-Pfade verschachteln und Pages-Routing brechen. Der Loop hält die Pfade flach.
3. **Verify-Schritt** am Ende — `grep` prüft, ob mindestens `index.html` den StatiCrypt-Loader enthält. Wenn der Encrypt-Schritt still gescheitert ist (z.B. wegen leerem Passwort), bricht der grep ab und der Workflow rot wird.

**Zwei-Job-Trennung** (Zeile 86–95):

```yaml
deploy:
  needs: build
  runs-on: ubuntu-latest
  environment:
    name: github-pages
    url: ${{ steps.deployment.outputs.page_url }}
  steps:
    - uses: actions/deploy-pages@v4
```

Der `deploy`-Job hängt vom `build`-Job ab (`needs: build`). Trennung in zwei Jobs hat zwei Vorteile:

- **Separate Permissions** möglich (Build braucht andere Rechte als Deploy, hier sind sie zwar global, könnten aber pro Job spezialisiert werden).
- **GitHub-Pages-Environment** wird sichtbar in der Repo-UI mit dem Deploy-Status und einer Verknüpfung zur veröffentlichten URL.

### 7.4 Wartbarkeits-Checkliste für die Workflows

| Wenn du ... | dann ... |
|---|---|
| ein neues `PIPELINE_*` Setting in `config.py` ergänzt | überlege, ob es als `workflow_dispatch.input` exponiert werden soll. Falls ja: in beiden Pipeline-Workflows ergänzen, gleicher Name, gleicher Typ. |
| ein Embedding-Modell wechselst | den Cache-Key in beiden Pipeline-Workflows aktualisieren (`st-${{ runner.os }}-...`) — sonst läuft mit altem Cache und neuen Code-Erwartungen. |
| einen neuen Secret-Wert brauchst | Secret in den Repo-Settings anlegen, in der `env:` Block des betreffenden Steps mappen, und einen Pre-Flight-Check wie in `pipeline-full.yml` ergänzen, damit das Fehlen früh und klar abbricht. |
| eine Doku-Seite umbenennst und sie war unter `--strict` Pflicht | `mkdocs build --strict` würde brechen — daher heisst Umbenennen: alle Verweise prüfen und ggf. Redirects in `mkdocs.yml` setzen. Der Workflow ist hier dein Sicherheitsnetz. |
| die Cron-Ausführung aktivierst | `pipeline.yml` ist der richtige Ort (kostenfrei). `pipeline-full.yml` bewusst **nicht** automatisieren, sonst setzt sich der Kostenrahmen leise höher. |

### 7.5 Häufige Stolpersteine

- **„Mein Lauf hat falsche Settings genommen"** — der `push`-Trigger hat keine `inputs`, also greifen Pydantic-Defaults. Manuell mit `workflow_dispatch` triggern, wenn andere Werte gewünscht sind.
- **„Der Modell-Cache cached etwas Falsches"** — Cache-Key per Hand bumpen (z.B. `key: st-${{ runner.os }}-...-v2`). GitHub-Caches selber lassen sich aus der Actions-UI löschen, aber Key-Bump ist sicherer.
- **„Pages zeigt leere Seite"** — meist `mkdocs build --strict` durchgewunken, aber StatiCrypt mit leerem Passwort scheiterte. Der Verify-`grep` am Ende von `docs.yml` fängt das.
- **„DataForSEO-Lauf in CI bricht ab"** — Quota erreicht, oder Secret fehlt für `--provider dataforseo`. Wechsel auf `estimate` als sofortige Workaround, dann Quota prüfen.

## 8. Designentscheidungen, die direkt im Code wirken

Eine kompakte Sammlung der Wahlmöglichkeiten, die im Code konkret zu sehen sind. Die Volltext-Begründung steht in den [Architektur-Entscheidungen (ADRs)](decisions.md).

### Stdlib-Retry statt `tenacity`

Rationale: Total ~70 Zeilen, kein extra Dependency, lesbar in einem Code-Review, frei von Klassenzustand. Der einzige Nachteil — fehlende Plugins — ist hier keiner, weil das Featureset (exp. backoff, jitter, Retry-After) trivial ist. Siehe `src/retry.py`.

### CSV statt SQLite oder Parquet als Pipeline-Bus

Rationale: Inspizierbar mit `head`, diff-bar in Git, keine Schema-Migration, von Pandas in einer Zeile gelesen. Bei einer Skalierung über mehrere Millionen Keywords wäre Parquet sinnvoller — dieser Punkt ist in `decisions.md` markiert.

### Multilinguales MiniLM statt englisches L6 oder grosses BGE-M3

Rationale: zvoove-Keywords sind deutsch, deutsche Morphologie wäre in einem englischen Modell schlecht abgebildet. BGE-M3 wäre besser, aber 2 GB statt 120 MB und braucht GPU für brauchbare Geschwindigkeit. MiniLM-L12 läuft auf einem MacBook in 25 Sekunden auf 500 Keywords. Dokumentiert im Docstring von `cluster.step_embed`.

### HDBSCAN-Defaults aus Plateau-Mitte

Rationale: Der Hyperparameter-Sweep zeigt eine Plateau-Region `mcs ∈ {10, 12, 15}` mit 10 Clustern. `mcs=12` ist die Mitte → ein Puffer auf jeder Seite gegen plattformbedingten UMAP-Drift. Konstante in `Settings` (siehe `cluster_hdbscan_mcs`), Begründung als Inline-Kommentar im Code-File und in der Methodik.

### Stable, kuratierte Cluster-Labels

`CLUSTER_LABELS_DE` und `CLUSTER_LABELS_EN` in `cluster.py` sind hand-kuratiert. Sobald `random_state=42` und der Datensatz stabil sind, produziert HDBSCAN reproduzierbare IDs — das macht kuratierte Labels statt Auto-Naming akzeptabel. Wenn ein Lauf abweichende Cluster-Anzahlen liefert (z.B. 13 statt 10), greift die Fallback-Logik in `_label_en` / `_label_de` auf generische `Cluster N` zurück, statt zu crashen. Wartung: Bei Daten-Refresh die Labels prüfen, der entsprechende ADR steht in `decisions.md`.

### Klassennamen-Matching für transiente Fehler

`retry._TRANSIENT_CLASS_PATTERNS` matcht Substrings wie `"RateLimitError"`. Damit hängt das Retry-Modul **nicht** vom Anthropic- oder OpenAI-SDK ab. Konsequenz: Diese SDKs bleiben aus dem Test-Pfad raus, das Retry-Modul ist unabhängig getestet, und man kann jeden zukünftigen Provider hinzufügen ohne Retry-Code anzufassen.

## 9. Lokale Entwicklung

### Schneller Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env       # API-Keys eintragen
pytest -q                  # ~3 s, kein Netz nötig
```

### Iterativ an einem einzelnen Schritt arbeiten

Jeder Schritt hat eine eigene Sub-CLI:

```bash
python -m src.discover --source manual --max-keywords 200
python -m src.enrich --provider estimate
python -m src.cluster --step embed,reduce,cluster,label
python -m src.brief --provider api --cluster 5 --model claude-sonnet-4-6
python -m src.briefs_html
python -m src.report
```

### Brief-Schritt ohne API-Kosten testen

```bash
python -m src.brief --dry-run         # Stubs statt echter Briefs
```

### Cluster-Hyperparameter tunen

```bash
python -m src.cluster --step sweep    # gibt die Sweep-Tabelle aus
PIPELINE_CLUSTER_HDBSCAN_MCS=10 python -m src.cluster --step cluster,label
```

## 10. Erweiterungs-Rezepte

### Neuen Pipeline-Schritt hinzufügen

1. Neue Datei `src/<schritt>.py` mit Modul-Docstring (Zweck, Eingaben, Ausgaben, CLI-Beispiele).
2. Eine Top-Level-`run(...)` Funktion, eine `main()` Funktion, ein `if __name__ == "__main__"` Block.
3. In `pipeline.py` ein `step_<schritt>(args)` plus Eintrag in `RUNNERS` und `ALL_STEPS`.
4. Falls neue Settings gebraucht: in `src/config.py` ergänzen.
5. Smoke-Test aufnehmen (`tests/test_smoke.py`).

### Neuen Provider für einen bestehenden Schritt hinzufügen

Beispiel Brief-Schritt:

1. `class MyProvider(BriefProvider)` in `brief.py` mit `name`, `__init__` (Auth-Check) und `generate`.
2. Eintrag in `make_provider`.
3. Optional `@with_retry()` auf `generate` setzen, wenn der Anbieter transiente Fehler wirft, deren Klassenname die `_TRANSIENT_CLASS_PATTERNS` trifft (sonst eigenes Pattern ergänzen).
4. CLI-Choices in `argparse` aktualisieren und den Settings-Literal-Typ erweitern.

### Cluster-Labels nach einem Daten-Refresh aktualisieren

1. `python -m src.cluster --step all` laufen lassen.
2. `output/clustering/cluster_profiles.csv` ansehen — die `top_5_kw_by_sv` und `top_terms` Spalten sind die schnelle Inspektionsbasis.
3. `CLUSTER_LABELS_DE` und `CLUSTER_LABELS_EN` in `src/cluster.py` editieren.
4. Re-Run von `--step label,profile,charts,viz` reicht (embed/reduce/cluster sind unverändert).

## 11. Was diese Architektur explizit **nicht** löst

Ehrlich, damit niemand falsche Annahmen mitnimmt:

- **Keine Streaming-Pipeline.** Alles ist Batch. Bei häufigen kleinen Updates (z.B. neuer Blogpost stündlich) müsste man auf eine Event-Queue umschwenken.
- **Keine Multi-Tenant-Trennung.** Pfade sind hartcodiert auf `data/`, `output/`. Mehrere Mandanten pro Repo wären eine Refactor-Aufgabe.
- **Kein Schema-Versioning.** CSVs haben keine eingebettete Versionsnummer. Eine inkompatible Spaltenänderung würde alte `output/`-Snapshots brechen. Heute akzeptabel weil Snapshots in Git versioniert sind.
- **Keine echte Authn/Authz für die Pages-Site.** StatiCrypt mit Shared Password schützt vor zufälligem Zugriff, ist aber kein Ersatz für SSO.

Diese Lücken sind bewusst gewählt — sie sind in `decisions.md` mit Trade-off und Schwellenwert dokumentiert, ab dem sie geschlossen werden müssten.

---

[Zurück zur Übersicht :octicons-arrow-right-24:](index.md){ .md-button }
[Architektur-Entscheidungen (ADRs) :octicons-arrow-right-24:](decisions.md){ .md-button }
