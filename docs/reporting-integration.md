# Reporting-Anbindung

Der `export`-Schritt der Pipeline schreibt fünf Dateien nach `output/reporting/`:

| Datei | Inhalt | Empfohlenes Tool |
|---|---|---|
| `clusters.json` | Cluster-Reporting mit Brief-Feldern | Airtable, Notion (per API) |
| `keywords.json` | Filterbare Keyword-Tabelle | Airtable, Notion (per API) |
| `report.json` | Konsolidiertes Bundle plus Run-Metadaten | Looker Studio, Custom Tools |
| `clusters.csv` | Wie `clusters.json`, mit aufgelösten Brief-Feldern (Prefix `brief_`) und Pipe-separierten Listen | Google Sheets, Excel |
| `keywords.csv` | Wie `keywords.json`, mit Pipe-separierten Listen | Google Sheets, Excel |

Diese Seite zeigt zwei konkrete Anbindungen, die in fünf Minuten lauffähig sind.

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

## Airtable

Die Pipeline bringt einen Sync-Befehl mit, der `clusters.json` und `keywords.json` direkt in eine Airtable-Base hochlädt.

### Setup

1. **Token anlegen.** Auf [airtable.com/create/tokens](https://airtable.com/create/tokens) einen Personal Access Token erzeugen. Scopes: `data.records:read` und `data.records:write`. Access auf eine konkrete Base beschränken.

2. **Base erstellen.** Im Airtable-UI eine leere Base anlegen. Zwei Tabellen erstellen, Standardnamen sind `Clusters` und `Keywords`. (Alternativ andere Namen wählen und über `AIRTABLE_CLUSTERS_TABLE` und `AIRTABLE_KEYWORDS_TABLE` setzen.)

3. **Felder anlegen.** Airtable verlangt, dass alle Felder vorab im UI existieren. Die Pipeline verrät, welche das sind:

   ```bash
   python -m src.sync_airtable --print-schema
   ```

   Das druckt die rund 33 Cluster-Felder und 15 Keyword-Felder mit empfohlenem Typ. Im Airtable-UI für jedes Feld den passenden Typ wählen (`Number`, `Checkbox`, oder `Long text`). Tipp: Checkbox-Felder wie `is_noise` müssen in Airtable explizit als `Checkbox` angelegt sein, damit `true`/`false` korrekt landet.

4. **Base-ID herauslesen.** Auf [airtable.com/api](https://airtable.com/api) die eigene Base anklicken. In der URL-Leiste steht jetzt etwas wie `airtable.com/appXXXXXXXXX/...`. Der Teil mit dem `app`-Prefix ist die Base-ID.

5. **Umgebungsvariablen setzen** (oder als CLI-Flags übergeben):

   ```bash
   export AIRTABLE_TOKEN=patXXXXXXXXX
   export AIRTABLE_BASE_ID=appXXXXXXXXX
   ```

### Sync ausführen

```bash
# Vorschau ohne Upload
python -m src.sync_airtable --dry-run

# Voller Sync
python -m src.sync_airtable

# Nur eine Tabelle
python -m src.sync_airtable --tables clusters
```

**Sync-Strategie:** Die Tabelle wird vor jedem Lauf vollständig geleert und mit den aktuellen Records neu befüllt. Das ist absichtlich einfach, weil jeder Pipeline-Lauf einen vollständigen Snapshot erzeugt. Inkrementelle Updates wären für die übliche Lauffrequenz (täglich oder seltener) unnötiger Komplexitäts-Aufwand.

**Linked Records (optional):** Standardmäßig steht in beiden Tabellen die `cluster_id` als Number-Feld. Wer in Airtable explizite Verknüpfungen will, konvertiert das `cluster_id`-Feld in der `Keywords`-Tabelle nachträglich auf den Typ `Link to another record` mit Ziel `Clusters`. Airtable zeigt dann pro Cluster automatisch alle zugehörigen Keywords.

### Views, die sich für die zvoove-Daten lohnen

In Airtable in der `Clusters`-Tabelle:

- `Pillar-Kandidaten`: Filter `intent_dominant = commercial` und `total_search_volume > 10000`, sortiert nach `mean_priority`.
- `Quick Wins`: Filter `mean_kd < 30` sortiert nach `total_search_volume`.
- `Redaktions-Backlog`: Gruppiert nach `intent_dominant`, sortiert nach `rank_by_sv`.

In der `Keywords`-Tabelle:

- `Top Priority`: Sortiert nach `priority_score`, gefiltert auf `is_noise = false`.
- `Pro Cluster`: Gruppiert nach `cluster_label_de`.

## Notion

Notion hat eine ähnliche API, aber bewusst kein dediziertes Sync-Modul in dieser Pipeline. Gründe:

- Die Notion-API erlaubt nur einen Page-Insert pro Call, kein Bulk. Bei 500 Keywords sind das 500 Calls (langsam, Rate-Limit-anfällig).
- Schema-Mapping ist fummeliger: Notion-Properties haben mehr Typen (relation, select-with-color, formula), die per UI gepflegt werden wollen.

Wenn Notion das Zielsystem ist, der pragmatischste Weg: `clusters.csv` per `Importieren → CSV` in eine Notion-Database laden. Notion erkennt Spaltentypen automatisch und legt Properties an. Nachteil: ein neuer Lauf erzeugt eine neue Database-Page statt die alte zu überschreiben. Für reine Stakeholder-Sicht (kein bidirektionales Editieren) reicht das.

## Looker Studio / Metabase

Beide Tools arbeiten gut mit `report.json` (custom JSON connector) oder mit den CSV-Dateien (CSV-Connector). Empfehlung: CSV verwenden, weil der JSON-Connector in Looker Studio ein Community-Plugin ist und deshalb Wartungs-Overhead bringt.
