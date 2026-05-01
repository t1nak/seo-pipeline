# Interview-Präsentation: 15 Minuten auf Deutsch (einfache Version)

> Kurze Sätze, einfache Sprache, leicht zu merken.
> Pro Block ein Gedanke, eine Zahl, ein Beispiel.

---

## Fahrplan

| Zeit | Block |
|---|---|
| 0:00 – 1:00 | Begrüßung |
| 1:00 – 3:00 | Aufgabe und Ergebnis |
| 3:00 – 5:00 | Architektur in sechs Schritten |
| 5:00 – 9:00 | Cluster-Schritt erklären |
| 9:00 – 10:30 | Briefs mit Claude |
| 10:30 – 12:00 | Reporting und Export |
| 12:00 – 13:30 | Drei Empfehlungen für zvoove |
| 13:30 – 14:30 | Was fehlt noch |
| 14:30 – 15:00 | Abschluss |

---

## 0:00 – 1:00 · Begrüßung

„Hallo, danke für die Einladung.

Ich zeige in fünfzehn Minuten meine Pipeline für die Aufgabenstellung.

Ziel der Aufgabe: aus dem zvoove-Blog Keywords gewinnen, gruppieren, Briefs
schreiben, ein Reporting bauen.

Drei Dinge möchte ich zeigen: Wie ich es gebaut habe. Warum ich so entschieden
habe. Welchen Nutzen es für zvoove hat."

---

## 1:00 – 3:00 · Aufgabe und Ergebnis

> Slide: zwei große Zahlen — **500** und **13**.

„Die Aufgabe in einem Satz: Aus dem Blog ein Keyword-Set bauen, clustern,
briefen, reporten.

Das Ergebnis in zwei Zahlen:

- **500 Keywords**
- **13 thematische Cluster**, alle Keywords zugeordnet, null Outlier

Das Gesamt-Suchvolumen liegt bei rund **240.000 Suchen pro Monat**.

Drei Cluster sind besonders interessant:

- Größter Cluster: HR- und Dokumentenverwaltungssoftware, 45.000 Suchen
- Höchste kommerzielle Dichte: zvoove-Produktnamen, 97 Prozent kommerziell
- Größter Awareness-Cluster: Digitalisierung in der Personaldienstleistung

Ist das gut? Ja. Der Silhouette-Score liegt bei 0,65. Werte über 0,5 gelten als
solide.

Ich habe das mit einem zweiten Verfahren gegengeprüft. Beide Verfahren stimmen
zu rund 80 Prozent überein. Das ist die Plausibilitätsprobe."

---

## 3:00 – 5:00 · Architektur

> Slide: `docs/architecture.svg` zeigen.

„Die Pipeline hat sechs Schritte:

1. **Discover** — Keywords sammeln
2. **Enrich** — Suchvolumen, Difficulty, CPC dazu
3. **Cluster** — Keywords nach Bedeutung gruppieren
4. **Brief** — pro Cluster einen Content-Brief schreiben
5. **Report** — alles in ein Dashboard packen
6. **Export** — JSON für Airtable, Notion, Sheets

Jeder Schritt ist eigenständig. Ich kann jeden einzeln laufen lassen.

Warum ist das wichtig? Die Schritte kosten unterschiedlich viel Zeit und Geld.
Embeddings rechne ich einmal. Briefs kosten Geld pro Lauf. Das will ich nicht
versehentlich neu erzeugen.

Eine ehrliche Sache: Discover ist noch nicht fertig. Ich lese aktuell ein
fertiges Keyword-Set aus einer CSV. Live-Scraping vom Blog kommt als Nächstes.

Warum so? Lieber vier Schritte richtig fertig, als sechs Schritte halb fertig."

---

## 5:00 – 9:00 · Cluster-Schritt

> Slide: Cluster-Karte live zeigen.

„Der Cluster-Schritt ist das Herzstück. Drei Entscheidungen sind wichtig.

**Erste Entscheidung: Embeddings.**

Ein Embedding ist eine Zahlenfolge, die die Bedeutung eines Texts beschreibt.

Beispiel: `Lohnabrechnung Software` und `Payroll Tool`. Andere Wörter, gleiche
Bedeutung, ähnliche Zahlen.

Das brauche ich, um Keywords nach Thema zu gruppieren — nicht nach exakter
Wortübereinstimmung.

Ich nutze ein mehrsprachiges Modell. Es versteht deutsche Komposita gut und
läuft auf jedem Laptop ohne GPU.

**Zweite Entscheidung: HDBSCAN statt k-means.**

Bei k-means muss ich vorher wissen, wie viele Cluster es gibt. Bei 500
Keywords aus einer fremden Branche kann ich das nicht raten.

HDBSCAN entscheidet selbst, wie viele Cluster sinnvoll sind.

Zweiter Vorteil: HDBSCAN markiert Ausreißer als Rauschen. k-means würde sie
zwanghaft einem Cluster zuwerfen und das Ergebnis verzerren.

**Dritte Entscheidung: Hyperparameter testen.**

Ich habe verschiedene Einstellungen ausprobiert und die beste mit Zahlen
verglichen. Nichts geraten. Alles reproduzierbar.

**Validierung.**

Ich habe parallel ein zweites Verfahren laufen lassen, Ward Hierarchical
Clustering. Beide Verfahren stimmen zu 81 Prozent überein.

Das heißt: zwei unabhängige Methoden sehen ähnliche Cluster. Das ist die
Plausibilitätsprobe."

> Optional: einen Cluster auf der Karte anklicken, Sprache umschalten.

---

## 9:00 – 10:30 · Briefs mit Claude

> Slide: einen Beispiel-Brief zeigen.

„Pro Cluster schreibt Claude einen Content-Brief.

Jeder Brief enthält:

- Arbeitstitel und Hauptkeyword
- Suchintention und Zielgruppe
- Outline mit Überschriften
- Drei Benchmark-URLs
- Call to Action

Format und Stil stehen im System-Prompt. Pro Lauf konsistent über alle
Cluster.

Ein technisches Detail: Prompt Caching.

Der System-Prompt ist groß. Bei 13 Clustern würde ich ihn 13-mal mitschicken.
Mit Caching wird er einmal gespeichert und wiederverwendet.

Ergebnis: rund 90 Prozent weniger Tokens. Kosten pro Lauf: unter einem Dollar.

Falls ein Brief fehlschlägt — Rate-Limit, Netzwerk —, läuft die Pipeline
weiter. Es gibt eine Retry-Logik mit Backoff. Am Ende ein Status-Bericht: 12 OK,
1 Fehler.

Das ist der Unterschied zwischen Demo-Code und Code, der wöchentlich läuft."

---

## 10:30 – 12:00 · Reporting und Export

> Slide: Dashboard und Google Sheet.

„Der Report-Schritt baut eine HTML-Datei.

Drin: KPI-Boxen, Cluster-Tabelle, Charts, Link auf die Karte.

Bewusst kein Frontend-Framework. Eine HTML-Datei, läuft in jedem Browser, kann
per Mail oder Slack verschickt werden.

Der Export-Schritt produziert drei JSON-Dateien:

- `clusters.json` — eine Zeile pro Cluster
- `keywords.json` — eine Zeile pro Keyword
- `report.json` — alles zusammen

Diese JSON-Dateien sind tool-neutral. Airtable, Notion und Google Sheets
akzeptieren sie alle.

Optional gibt es einen direkten Sync nach Airtable und Google Sheets, per
Schalter aktivierbar.

Warum nicht direkt in ein Tool? Die Wahl des Reporting-Tools gehört dem
Marketing-Team, nicht der Pipeline."

---

## 12:00 – 13:30 · Drei Empfehlungen für zvoove

> Slide: drei Karten, eine pro Empfehlung.

„Aus 13 Clustern hebe ich drei heraus.

**Erstens: HR- und Dokumentenverwaltungssoftware.**

45.000 Suchen pro Monat, 89 Prozent kommerziell.

Was tun: Pillar-Pages zu Software-Kategorien, jeweils mit zvoove als Lösung.

Klassischer Bottom-of-Funnel-Hebel.

**Zweitens: zvoove-Marken-Keywords.**

23.000 Suchen pro Monat, 97 Prozent kommerziell.

Schon der eigene Name. Aber: Difficulty bei 52. Das ist hoch. Wahrscheinlich
ranken Vergleichsseiten und Bewertungsportale weit oben.

Was tun: ein zvoove-Erfahrungen-Hub, der Bewertungen aggregiert. Defense und
Offense in einem.

**Drittens: Digitalisierung Personaldienstleistung.**

24.000 Suchen pro Monat, niedrige kommerzielle Dichte.

Das ist Top-of-Funnel. Geschäftsführer recherchieren genau dann, wenn ein
Software-Wechsel ansteht.

Was tun: ein Wissens-Hub, der Awareness-Traffic in die kommerziellen Cluster
führt.

Wichtig: Nicht jeder Cluster ist ein Pillar. Cluster vier ist zu gemischt. Da
empfehle ich Top-Keywords einzeln. Cluster zwölf ist zu groß. Da empfehle ich
Sub-Clustering."

---

## 13:30 – 14:30 · Was fehlt noch

„Drei ehrliche Punkte.

**Was fehlt:**

- Discover ist ein Stub. Live-Scraping kommt als Nächstes.
- Keine Datenbank. Läufe leben als Dateien.
- Keine direkte Verbindung zur Search Console.

**Warum so:**

Bewusste Priorisierung. Alles dokumentiert in den Decision Records.

**Was ich als Nächstes baue:**

1. Discover live — der Blog wird gescrapt
2. Search Console anbinden — echte Klick-Daten statt Heuristik
3. SQLite-Persistenz — Läufe vergleichen
4. CMS-Integration — Briefs landen direkt im Redaktions-Tool

Bei einer zweiten Iteration würde ich Discover zuerst bauen, nicht zuletzt."

---

## 14:30 – 15:00 · Abschluss

„Zusammengefasst:

- 13 Cluster, 0 Outlier, validiert mit zwei unabhängigen Methoden
- Briefs mit Claude und Caching, robust gegen Fehler
- Reporting tool-neutral, optional direkt in Airtable oder Sheets
- Drei konkrete Empfehlungen für zvoove

Aufgebaut so, dass jeder Schritt einzeln ersetzt werden kann.

Ich freue mich auf eure Fragen."

---

## Q&A — kurze Antworten

**Warum HDBSCAN, nicht k-means?**

„k-means braucht eine vorgegebene Clusteranzahl. HDBSCAN nicht. HDBSCAN findet
auch Ausreißer, k-means zwingt jedes Keyword in einen Cluster."

**Warum nicht ein LLM, das direkt clustert?**

„Habe ich auch laufen lassen. Ein LLM ist nicht reproduzierbar zwischen
Läufen. HDBSCAN ist deterministisch. LLM nutze ich für die Labels."

**Wie produktiv ausrollen?**

„Wöchentlicher Cron für `enrich` und `report`. Quartalsweiser voller Lauf.
SQLite für die Lauf-Historie. Ein Tag Arbeit."

**Wie misst man Erfolg?**

„Methodisch: Silhouette und Übereinstimmung mit zweitem Verfahren. Geschäftlich:
Rankings, Traffic auf neue Pillar-Pages, MQLs aus den Clustern."

**Was kostet das?**

„Rund einen Dollar pro vollem Lauf. Bei wöchentlichem Lauf 50 Dollar pro Jahr."

**Warum kein Live-Discover?**

„Web-Scraping ist konzeptionell der schwierigste Schritt. Ich habe die Zeit
lieber in Cluster, Brief und Reporting gesteckt. Beim nächsten Durchlauf wäre
Discover Schritt eins."

**Größte Schwäche?**

„Das fehlende Live-Discover. Sonst nichts Großes."

**Funktioniert das auch für andere Branchen?**

„Ja. Das Embedding-Modell ist mehrsprachig, das Clustering ist domänenfrei.
Brief-Prompt anpassen, Quelle austauschen, fertig."

**Welche Rolle soll AI bei zvoove spielen?**

„Drei Hebel: Themen finden, Briefs schreiben, Funnel personalisieren. Diese
Pipeline deckt die ersten zwei ab."

---

## Tipps für die Generalprobe

- Diese Zahlen auswendig: **500, 13, 0 Outlier, 240.000 SV, 1 USD pro Lauf**.
- Cluster-Karte im Browser geöffnet halten. Live-Demo wirkt stärker als ein
  Screenshot.
- Bei Q&A: zwei Sekunden Pause vor der Antwort. Wirkt souverän.
- Wenn du etwas nicht weißt: ruhig sagen. Ehrlichkeit schlägt Improvisation.
- Einmal mit Stoppuhr durchsprechen. Wo bist du nach 8 Minuten? Sollte
  mitten im Cluster-Block sein.
- Tief atmen zwischen den Blöcken. 15 Minuten sind kurz.
