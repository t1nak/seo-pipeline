# Reporting-Anbindung

!!! tip "Live-Demo: Reporting in Google Sheets"
    Diese Pipeline pusht nach jedem Lauf in ein echtes Google Sheet, das du direkt anschauen kannst:
    [**docs.google.com/spreadsheets/d/1JExk1b5M8ljtTkhKHwgmEFH9f2fHgOoOmM2pz020JUQ**](https://docs.google.com/spreadsheets/d/1JExk1b5M8ljtTkhKHwgmEFH9f2fHgOoOmM2pz020JUQ/edit) (zwei Tabs: `Clusters`, `Keywords`)

Der `export`-Schritt der Pipeline schreibt fünf Dateien nach `output/reporting/`:

| Datei | Inhalt | Empfohlenes Tool |
|---|---|---|
| `clusters.json` | Cluster-Reporting mit Brief-Feldern | Airtable, Notion (per API) |
| `keywords.json` | Filterbare Keyword-Tabelle | Airtable, Notion (per API) |
| `report.json` | Konsolidiertes Bundle plus Run-Metadaten | Looker Studio, Custom Tools |
| `clusters.csv` | Wie `clusters.json`, mit aufgelösten Brief-Feldern (Prefix `brief_`) und Pipe-separierten Listen | Google Sheets, Excel |
| `keywords.csv` | Wie `keywords.json`, mit Pipe-separierten Listen | Google Sheets, Excel |

Diese Seite zeigt die Google-Sheets-Anbindung im Detail. Push nach Airtable und Notion lässt sich genauso leicht ergänzen, weil die Pipeline beides als JSON exportiert und Skripte für direkten API-Push mitbringt.

## Google Sheets

Zwei Wege, je nach Anforderung.

### Variante A: Einmaliger Import

1. Pipeline laufen lassen: `python pipeline.py --step export`.
2. In Google Sheets: `Datei → Importieren → Hochladen` und die `clusters.csv` oder `keywords.csv` auswählen.
3. Beim Import-Dialog `Tabelle ersetzen` wählen und Trennzeichen auf `Komma` lassen. Die Datei ist UTF-8 mit BOM, damit Sonderzeichen wie `ü` und `ö` direkt richtig erscheinen.
4. Filter aktivieren: `Daten → Filter erstellen`.

Listen sind mit ` | ` separiert (zum Beispiel `top_keywords_by_sv`). Wer einen einzelnen Eintrag herauszieht, nimmt `=SPLIT(A2, " | ")`.

### Variante B: Live-Sync per IMPORTDATA

Wenn die CSVs öffentlich erreichbar sind (zum Beispiel über GitHub Pages, das diese Pipeline ohnehin nutzt), holt Sheets die Daten auf Knopfdruck.

In Zelle `A1`:

```
=IMPORTDATA("https://t1nak.github.io/seo-pipeline/output/reporting/clusters.csv")
```

Sheets aktualisiert nach Cache-Ablauf automatisch (typisch 1 Stunde) oder bei `Datei → Aktualisieren`. Vorteil: keine manuellen Imports. Nachteil: macht das Reporting öffentlich, taugt also eher für Stakeholder-Übersichten ohne sensible Daten.

### Variante C: Direkter Push aus der Pipeline (privat, automatisch)

Für ein privates Sheet, das nach jedem Pipeline-Lauf aktualisiert wird, schreibt `src/sync_sheets.py` direkt in zwei Tabs (`Clusters`, `Keywords`). Der Push hängt an einem Schalter, damit lokale Läufe ohne Setup nicht crashen.

**Einmaliges Setup:**

1. **Google-Cloud-Projekt anlegen** auf [console.cloud.google.com](https://console.cloud.google.com).
2. **Sheets-API aktivieren.** Direkter Link: `https://console.cloud.google.com/apis/library/sheets.googleapis.com?project={PROJECT_ID}` (Projekt-ID einsetzen). „Enable" klicken und ~10 Sekunden warten bis „API enabled" steht. Ohne diesen Schritt scheitert der Sync später mit `403: API has not been used`.
3. **Service Account erstellen** unter `IAM & Admin → Service Accounts → Create`. Name frei wählbar (z.B. `seo-pipeline-sync`), Rollen leer lassen, optionale Permission- und Principal-Steps überspringen.
4. **JSON-Key herunterladen** beim erstellten Service Account unter `Keys → Add Key → Create new key → JSON`. Die Datei enthält ein Feld `client_email`, das sieht aus wie `xyz@projekt.iam.gserviceaccount.com`. Diese E-Mail brauchst du gleich.
5. **Sheet anlegen** in Google Sheets, zwei Tabs benennen: `Clusters`, `Keywords`. Sheet mit der `client_email` aus Schritt 4 teilen, Editor-Rechte. Häkchen „Notify people" entfernen (Service Accounts haben kein Postfach).
6. **Sheet-ID** aus der URL kopieren: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`.

**Lokal ausführen:**

```bash
export PIPELINE_SHEETS_SYNC_ENABLED=true
export PIPELINE_SHEETS_ID=1AbCDeF...  # die Sheet-ID
export GOOGLE_SHEETS_CREDENTIALS_FILE=/Pfad/zu/service-account.json

python -m src.sync_sheets --dry-run    # zeigt Zeilen- und Spaltenzahl, kein API-Call
python -m src.sync_sheets              # tatsächlich pushen
```

**In CI automatisch:**

Im GitHub-Repo unter `Settings → Secrets and variables → Actions` zwei Einträge anlegen:

- Variable `GOOGLE_SHEETS_ID` mit der Sheet-ID
- Secret `GOOGLE_SHEETS_CREDENTIALS_JSON` mit dem kompletten Inhalt der Service-Account-JSON

Beim Auslösen des `Pipeline (full)`-Workflows den Toggle `sheets_sync` auf `true` setzen. Schritt 7 pusht dann nach jedem Lauf in das Sheet.

**Schalter im Detail:**

| Variable | Default | Wirkung |
|---|---|---|
| `PIPELINE_SHEETS_SYNC_ENABLED` | `false` | `false` macht `python -m src.sync_sheets` zum No-op (nur Log, kein Fehler). `true` aktiviert den Push. |
| `PIPELINE_SHEETS_ID` | — | Pflicht, sobald aktiv. Sheet-ID aus der URL. |
| `PIPELINE_SHEETS_CLUSTERS_TAB` | `Clusters` | Tab-Name. Wenn nicht da, wird er automatisch angelegt. |
| `PIPELINE_SHEETS_KEYWORDS_TAB` | `Keywords` | Wie oben. |
| `GOOGLE_SHEETS_CREDENTIALS_FILE` | — | Pfad zur JSON. Lokal benutzen. |
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | — | JSON-Inhalt direkt. Für CI-Secrets. |

`--force` umgeht den `_ENABLED`-Schalter, etwa für einen einmaligen lokalen Test ohne Env-Variable zu setzen.

**Troubleshooting:**

| Fehler | Ursache | Fix |
|---|---|---|
| `APIError: [403]: Google Sheets API has not been used in project ...` | Sheets-API ist im GCP-Projekt nicht aktiviert | Setup-Schritt 2: API auf der Library-Seite aktivieren, ~10 Sekunden warten, neu auslösen. |
| `APIError: [403]: The caller does not have permission` | Sheet ist nicht mit der Service-Account-E-Mail geteilt | Sheet öffnen, „Share", `client_email` aus der JSON eintragen, Editor-Rechte. |
| `APIError: [404]: Requested entity was not found.` | Sheet-ID falsch oder Sheet gelöscht | ID aus der aktuellen Sheet-URL nochmal kopieren, GitHub-Variable `GOOGLE_SHEETS_ID` aktualisieren. |
| `gspread.exceptions.WorksheetNotFound` | Tab-Name stimmt nicht mit `PIPELINE_SHEETS_CLUSTERS_TAB` / `PIPELINE_SHEETS_KEYWORDS_TAB` überein | Tab im Sheet umbenennen oder die Env-Vars anpassen. (Tabs werden bei Bedarf automatisch angelegt, aber nur wenn das Sheet noch keinen anderen Tab mit dem Namen hat.) |
| Step 7 wird mit „Skipped" angezeigt | `sheets_sync` Toggle stand beim Workflow-Start auf `false` | Workflow neu auslösen, Toggle auf `true`. |

## Airtable und Notion

Beide Tools sind über die Pipeline-Outputs leicht anschließbar:

- **Airtable:** `python -m src.sync_airtable --print-schema` zeigt die rund 33 Cluster- und 15 Keyword-Felder, die in der Base anzulegen sind. Mit `AIRTABLE_TOKEN` und `AIRTABLE_BASE_ID` pusht `python -m src.sync_airtable` die JSONs direkt in die Tabellen `Clusters` und `Keywords`.
- **Notion:** `clusters.csv` per `Importieren → CSV` in eine Database laden, Notion erkennt die Spaltentypen automatisch. Für einen direkten API-Push (Bulk-Insert nicht unterstützt, 500 Calls bei 500 Keywords) lässt sich das Sync-Pattern aus `src/sync_airtable.py` übernehmen.

## Looker Studio / Metabase

Beide Tools arbeiten gut mit `report.json` (custom JSON connector) oder mit den CSV-Dateien (CSV-Connector). Empfehlung: CSV verwenden, weil der JSON-Connector in Looker Studio ein Community-Plugin ist und deshalb Wartungs-Overhead bringt.
