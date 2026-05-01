# Interview-Präsentation: 15 Minuten auf Deutsch

> Sprechskript für die mündliche Vorstellung der SEO-Keyword-zu-ContentBrief-Pipeline.
> Zielzeit: 15 Minuten Vortrag, danach Q&A. Sprich frei, nutze die Notizen als Anker.

---

## Kurzfahrplan (15 Minuten)

| Zeit | Block | Slide / Artefakt |
|---|---|---|
| 0:00 – 1:00 | Einstieg, ein Satz zum Ziel | Titelfolie |
| 1:00 – 2:30 | Aufgabe und Ergebnis in zwei Zahlen | KPI-Folie |
| 2:30 – 4:30 | Architektur, sechs entkoppelte Schritte | `docs/architecture.svg` |
| 4:30 – 8:30 | Herzstück: Cluster-Schritt (Embeddings, UMAP, HDBSCAN) | Cluster-Map |
| 8:30 – 10:00 | Briefs mit Claude API plus Prompt Caching | Beispiel-Brief |
| 10:00 – 11:30 | Reporting und Export, Anbindung an Revenue Stack | Dashboard, Sheets-Link |
| 11:30 – 13:30 | Drei konkrete Empfehlungen für zvoove | Empfehlungs-Folie |
| 13:30 – 14:30 | Limits, Trade-offs, was ich anders machen würde | Decisions-Slide |
| 14:30 – 15:00 | Abschluss, Übergang in die Fragen | Titelfolie zurück |

---

## 0:00 – 1:00 · Einstieg

> Slide: Titelfolie mit Repo-Link und einem Satz zum Ziel.

„Vielen Dank für die Einladung. Ich zeige in den nächsten fünfzehn Minuten eine
Pipeline, die ich für die Aufgabenstellung gebaut habe: aus dem zvoove Blog ein
priorisiertes Keyword-Set entwickeln, thematisch clustern, pro Cluster einen
Content-Brief schreiben und das Ganze in ein filterbares Reporting überführen.

Mein Ziel heute ist nicht, jede Codezeile zu erklären, sondern drei Dinge klar
zu machen: erstens, wie ich die Aufgabe in Schritte zerlegt habe; zweitens, wo
die nicht-trivialen Entscheidungen lagen; und drittens, wie das Ergebnis im
Revenue-Kontext von zvoove landen würde."

---

## 1:00 – 2:30 · Aufgabe und Ergebnis in zwei Zahlen

> Slide: Die KPI-Tabelle aus dem README oder der Case Study. Zwei Zahlen groß
> hervorheben: 500 Keywords, 13 Cluster.

„Die Aufgabe in einem Satz: aus dem Blog ein Keyword-Set von maximal fünfhundert
Keywords entwickeln, clustern, briefen, reporten.

Das Ergebnis lässt sich in zwei Zahlen zusammenfassen. Fünfhundert Keywords sind
in dreizehn thematische Cluster zugeordnet, mit null Outliern. Das Gesamt-
Suchvolumen über alle Cluster liegt bei knapp zweihundertvierzigtausend
Suchanfragen pro Monat.

Drei Cluster stechen heraus. Der größte nach Suchvolumen ist `HR und
Dokumentenverwaltungssoftware` mit fünfundvierzigtausend Suchanfragen im Monat.
Die höchste kommerzielle Dichte hat der Cluster `Zvoove Plattform Features und
Preise` mit siebenundneunzig Prozent kommerzieller Intent. Das ist genau die
Mischung, die für Pillar-Pages und für Bottom-of-Funnel-Inhalte interessant ist.

Methodisch validiert ist das Ganze über einen Silhouette-Score von 0,647 auf
den Kern-Keywords und einen ARI von 0,811 gegen ein zweites, unabhängig
gerechnetes Verfahren, Ward Hierarchical Clustering. Beide Werte sind solide,
darauf komme ich gleich noch einmal kurz zurück."

---

## 2:30 – 4:30 · Architektur

> Slide: `docs/architecture.svg`. Linke Seite externe Systeme, Mitte die sechs
> Schritte, rechts die Datenartefakte.

„Die Pipeline besteht aus sechs entkoppelten Schritten: Discover, Enrich,
Cluster, Brief, Report und Export. Jeder Schritt hat klar definierte Eingaben
und klar definierte Ausgaben. Das ist keine kosmetische Entscheidung, sondern
eine bewusste Architektur, weil die Schritte unterschiedlich teuer sind.

Embeddings rechne ich genau einmal. Das Cluster-Tuning, also Hyperparameter
ausprobieren, läuft danach in Sekunden, weil ich nicht jedes Mal das Modell neu
laden muss. Briefs kosten pro Lauf rund zwanzig Cent über die Claude API, also
will ich sie nicht versehentlich bei jedem Test-Run neu generieren. Genau dafür
ist die Entkopplung da: jeder Schritt einzeln triggerbar, jeder Schritt einzeln
testbar.

Ein Wort zur ehrlichen Einordnung: der Discover-Schritt ist aktuell ein Stub.
Ich lese ein kuratiertes Keyword-Set aus einer CSV, statt den Blog live zu
scrapen. Das ist eine bewusste Trade-off-Entscheidung, transparent in den
Architecture Decision Records dokumentiert. Die Begründung: ein perfektes
Discover ohne Cluster und Brief wäre wertlos, ein gutes Cluster und ein guter
Brief ohne Live-Discover ist trotzdem demonstrierbar. Wenn ich noch eine Woche
hätte, wäre Discover der nächste Schritt, den ich nachziehe.

Tech-Stack auf einen Blick: Sentence-Transformers für Embeddings, UMAP für
Dimensionsreduktion, HDBSCAN fürs Clustering, Anthropic Haiku für die
Cluster-Labels und Claude Sonnet für die Briefs. Optional DataForSEO für echte
Suchvolumen. Alles, was lokal laufen kann, läuft lokal und kostenfrei."

---

## 4:30 – 8:30 · Herzstück: der Cluster-Schritt

> Slide: Live die Cluster-Karte zeigen, oder ein Screenshot der zweidimensionalen
> Darstellung. Sprache umschalten als kleiner Demo-Effekt.

„Das Herzstück ist der Cluster-Schritt. Die Aufgabe klingt einfach: gruppiere
fünfhundert Keywords nach Bedeutung. Die Umsetzung hat drei nicht-triviale
Entscheidungen, über die ich kurz spreche.

**Erste Entscheidung: das Embedding-Modell.** Ich nutze
`paraphrase-multilingual-MiniLM-L12-v2`. Mehrsprachig, weil zvoove Keywords
deutsche Komposita haben, die ein englisch-fokussiertes Modell schlechter
handhabt. Klein, weil hundertzwanzig Megabyte auf jedem Laptop ohne GPU laufen.
Etabliert, weil Sentence-Transformers das Standardwerkzeug sind und in einer
Bewertung nicht erklärungsbedürftig.

Wichtig zum Verständnis für alle, die nicht täglich mit Embeddings arbeiten:
Ein Embedding ist eine Zahlenfolge, die die Bedeutung eines Texts beschreibt.
`Lohnabrechnung Software` und `Payroll Tool` haben ähnliche Zahlen, obwohl kein
Wort identisch ist. Genau das brauche ich, um Keywords nach Thema zu gruppieren
statt nach exakter Wortübereinstimmung.

**Zweite Entscheidung: HDBSCAN statt k-means.** k-means braucht eine
vorgegebene Clusteranzahl. Bei fünfhundert deutschen Keywords aus einer
spezifischen Branche kann ich nicht seriös sagen, ob es fünf oder zehn oder
fünfzehn sinnvolle Themen gibt. HDBSCAN entscheidet das selbst aus den Daten.

Zweiter Vorteil: HDBSCAN markiert echte Ausreißer als Rauschen, statt sie
zwanghaft einem Cluster zuzuordnen. Beispiel `fachkräftemangel deutschland` —
ein Top-Funnel-Begriff ohne klare Cluster-Heimat. k-means würde ihn irgendeinem
Cluster zuwerfen und dessen Profil verwässern. HDBSCAN sagt: gehört zu nichts.
Ich behandle ihn dann als Soft-Assignment in den nächsten Cluster, behalte aber
die Information `noise_assigned: true`, dass diese Zuordnung nachträglich war.

**Dritte Entscheidung: Hyperparameter-Sweep statt Bauchgefühl.** Die
Schlüsselparameter `min_cluster_size`, `min_samples` und `cluster_selection_method`
habe ich nicht geraten, sondern in einer Grid Search durchgespielt. Ergebnis:
`mcs=10, ms=5, eom`. Begründung: höchster Silhouette-Score, plausible
Cluster-Anzahl, plausibler Rauschanteil vor Soft-Assignment. Der Sweep ist
reproduzierbar, das gehört für mich zu jedem ML-Projekt dazu.

Ein Detail noch zur Validierung: ich rechne parallel ein zweites,
mathematisch unabhängiges Verfahren — Ward Hierarchical Clustering — und
vergleiche die Übereinstimmung über Adjusted Rand Index. Der ARI von 0,811
zwischen HDBSCAN und Ward sagt mir: zwei Verfahren, die unterschiedlich an die
Sache rangehen, sind sich zu vier Fünfteln einig. Das ist die Plausibilitäts-
Probe, dass ich nicht nur einen Algorithmus zufällig glücklich gewählt habe."

> Optional, falls Zeit bleibt: kurz die Karte live demonstrieren, einen Cluster
> anklicken, die Sprache umschalten. Das wirkt stärker als jeder Screenshot.

---

## 8:30 – 10:00 · Briefs mit Claude API plus Prompt Caching

> Slide: Beispiel-Brief, etwa `output/briefings/cluster_05.md`, sichtbar
> herunterscrollen.

„Pro Cluster wird ein Content-Brief in Markdown erzeugt. Das Format ist
festgelegt: Arbeitstitel, Hauptkeyword, drei bis sieben Nebenkeywords,
Suchintention, empfohlene Wortanzahl, Zielgruppe als Ein-Satz-Persona,
Schmerzpunkt, Outline mit H1 bis H3, drei Benchmark-URLs und ein Call to Action
mit Bezug zu zvoove-Produkten.

Technisch interessant ist Prompt Caching. Der System-Prompt — also die
Beschreibung des Brief-Formats und des Tons — ist rund achthundert Tokens groß.
Bei dreizehn Clustern würde ich den Prompt dreizehnmal mitsenden. Mit Caching
wird er einmal gecached und in den darauffolgenden Aufrufen wiederverwendet.
Tokeneinsparung ungefähr neunzig Prozent auf den gecachten Anteil. Das ist
unter einem Dollar pro vollem Lauf, in absoluten Zahlen klein, aber genau die
Sorte Engineering-Disziplin, die in Produktion über die Wirtschaftlichkeit
einer Pipeline entscheidet.

Zu Robustheit: jeder API-Call ist mit einer Retry-Logik mit exponentiellem
Backoff und Jitter umhüllt. Wenn ein einzelner Brief fehlschlägt, schreibt das
Skript einen Stub und macht weiter. Die Pipeline bricht nicht ab, weil Cluster
fünf einen Rate-Limit getroffen hat. Am Ende gibt es ein Status-Reporting:
zwölf OK, ein Fehler. Das ist die Differenz zwischen Demo-Code und Code, der
in einer wöchentlichen Cron-Pipeline überleben kann.

Für CI und für API-freie Demos gibt es einen Dry-Run-Modus, der Stubs schreibt,
ohne die API zu rufen."

---

## 10:00 – 11:30 · Reporting und Export

> Slide: Screenshot vom Dashboard. Wenn live verfügbar, Tab mit dem Google Sheet
> nebenher offen halten.

„Der Reporting-Schritt erzeugt eine einzelne HTML-Datei, die alle Artefakte
konsolidiert: KPI-Boxen, sortierte Cluster-Tabelle, eingebettete Charts, Link
auf die interaktive Karte. Bewusst keine Frontend-Framework-Abhängigkeit. Es
ist eine HTML-Datei mit Inline-CSS, die in jedem Browser läuft, sich an
Stakeholder verschicken lässt und in Slack klickbar bleibt.

Der Export-Schritt liefert dasselbe in maschinenlesbarer Form: drei JSON-
Dateien — `clusters.json`, `keywords.json`, `report.json`. Das ist die
toolneutrale Übergabe an Airtable, Notion oder Google Sheets. Plus ein
optionaler Sync nach Airtable und ein optionaler Push nach Google Sheets über
einen Service Account, jeweils per Konfigurations-Schalter aktivierbar.

Das ist bewusst aufgeteilt: die Pipeline produziert Daten, die letzte Meile zu
einem konkreten Tool ist eine Marketing-Team-Entscheidung. Wer Notion nutzt,
hängt einen Wrapper an. Wer Airtable nutzt, schaltet den Sync ein. Pipeline und
Reporting-Tool bleiben austauschbar."

---

## 11:30 – 13:30 · Drei Empfehlungen für zvoove

> Slide: Drei Spalten oder drei Karten, je eine pro Empfehlung.

„Aus den dreizehn Clustern hebe ich drei heraus, sortiert nach Hebel.

**Erstens: HR und Dokumentenverwaltungssoftware.** Fünfundvierzigtausend
Suchanfragen pro Monat, neunundachtzig Prozent kommerziell. Top-Keywords sind
`dokumentenmanagement software`, `bewerbermanagement software`,
`mitarbeiterverwaltung software`. Empfehlung: ein Pillar-Page-Set zu
Software-Kategorien, das jeweils ein zvoove-Modul als Lösung positioniert.
Klassischer Bottom-of-Funnel-Hebel. Wenn fünf Prozent der monatlichen Klicks
durchkommen und davon zwei Prozent zu MQLs werden, sind das fünfundvierzig MQLs
pro Monat allein aus diesem Cluster.

**Zweitens: Zvoove Plattform Features und Preise.** Dreiundzwanzigtausend
Suchanfragen, siebenundneunzig Prozent kommerziell. Brand-Keywords wie
`zvoove referenzen`, `zvoove dms`, `zvoove cockpit`. Die Keyword-Difficulty
liegt bei zweiundfünfzig. Das ist für Brand-Begriffe ungewöhnlich hoch und
deutet darauf hin, dass aktuell entweder Wettbewerber-Vergleichsseiten oder
Bewertungsplattformen die Suchergebnisse dominieren. Schneller Win: ein
zvoove-Erfahrungen-Hub unter `/produkte/`, der die positiven Bewertungen
aggregiert. Das ist Defense und Offense in einem.

**Drittens: Digitalisierung Personaldienstleistung.** Knapp vierundzwanzig-
tausend Suchanfragen, niedrigere kommerzielle Dichte, mittlere KD. Das ist der
klassische Top-of-Funnel-Eingang. Geschäftsführer recherchieren
Digitalisierungs-Schritte genau dann, wenn ein Software-Wechsel ansteht.
Empfehlung: ein Hub-Pillar `/wissen/digitalisierung-personaldienstleistung/`,
der Awareness-Traffic gezielt in die kommerziellen Cluster eins, zehn und drei
überführt. Pipeline-Influence statt direkter Conversion, Wirkung über sechs bis
zwölf Monate.

Was ich an dieser Übersetzung wichtig finde: nicht jeder Cluster ist ein
Pillar. Cluster vier zum Beispiel ist heterogen — `aüg`, `bewerber finden`,
`lohnabrechnung sage` in einem Topf. Meine Empfehlung dort lautet: Top-Keywords
einzeln, nicht als Pillar. Cluster zwölf ist mit siebenundneunzig Keywords zu
groß für einen einzigen Brief, da empfehle ich Sub-Clustering vor der
redaktionellen Bearbeitung. Eine Pipeline ist nur dann ein Revenue-Asset, wenn
sie nicht jedes Cluster gleich behandelt."

---

## 13:30 – 14:30 · Limits und nächste Schritte

> Slide: Eine knappe Liste, drei Punkte links (Limits), drei Punkte rechts
> (Next Steps).

„Drei Punkte zur Ehrlichkeit.

**Erstens, Limits.** Discover ist ein Stub, das Live-Scraping fehlt.
Sentence-Transformer MiniLM ist gut, aber nicht state of the art für Deutsch
— ein Test mit `multilingual-e5-large` wäre lohnenswert. Es gibt keine
Persistenz-Schicht, Pipeline-Läufe leben als Snapshots im Dateisystem.

**Zweitens, Trade-offs.** Diese Limits sind keine Versäumnisse, sondern
bewusste Priorisierungen. Sie sind in den Architecture Decision Records
dokumentiert, jede mit Begründung und Alternative.

**Drittens, was ich als Nächstes baue.** Erstens Discover live machen. Zweitens
die Search Console anbinden, damit aus der Heuristik echte Click- und
Impression-Daten werden. Drittens eine SQLite-Persistenzschicht, die
Lauf-für-Lauf-Vergleiche ermöglicht. Viertens eine Schema-Anbindung an Sanity
oder Contentful, damit Briefs als Drafts direkt im CMS landen.

Bei einer zweiten Iteration würde ich Discover zuerst bauen, nicht zuletzt.
Das wäre die einzige strukturelle Sache, die ich anders machen würde."

---

## 14:30 – 15:00 · Abschluss

„Zusammengefasst: dreizehn Cluster, null Outlier, validiert mit Silhouette und
ARI. Briefs über Claude mit Caching, Reporting toolneutral als JSON, optional
direkt nach Airtable oder Sheets. Drei konkrete Empfehlungen mit Revenue-
Hypothese. Aufgebaut so, dass jeder Schritt einzeln ersetzt werden kann, wenn
ein Teil der zvoove-Realität anders aussieht als meine Annahme.

Ich freue mich auf eure Fragen."

---

## Q&A — vorbereitete Antworten

Die wahrscheinlichsten Fragen aus der Bewerber-Perspektive plus knappe
Antworten zum Mitnehmen.

### Warum HDBSCAN und nicht ein LLM, das die Cluster direkt vorschlägt?

„Beides hat Berechtigung. HDBSCAN ist deterministisch, reproduzierbar, billig
und mathematisch nachvollziehbar. Ein LLM-basierter Ansatz wäre flexibler, aber
nicht reproduzierbar zwischen Läufen und teurer pro Lauf. Ich habe beide
laufen lassen und vergleiche die Übereinstimmung über ARI. Der Wert von 0,143
zeigt, dass die beiden Verfahren unterschiedliche, aber jeweils sinnvolle
Cluster-Grenzen ziehen. HDBSCAN als Hauptverfahren, LLM als Gegenprobe und für
die Labels."

### Warum nicht einfach k-means mit k=13?

„Drei Gründe. Erstens, k=13 ist eine Antwort, kein Setup — ich wüsste nicht im
Voraus, dass dreizehn die richtige Zahl ist. Zweitens, k-means hat keine
Outlier-Behandlung, würde also `fachkräftemangel deutschland` zwangsweise
einem Cluster zuwerfen. Drittens, k-means setzt sphärische Cluster gleicher
Dichte voraus, und Keyword-Cluster sind in der Praxis sehr unterschiedlich
dicht."

### Wie generalisierbar ist das auf andere Branchen oder Sprachen?

„Sehr gut. Das Embedding-Modell ist multilingual, das Clustering ist
domänenfrei, der Brief-Prompt ist eine Konfiguration. Für eine andere Branche
würde ich den System-Prompt für Briefs anpassen und die Discover-Quelle
austauschen. Pro neuer Sprache eventuell ein Test mit einem
sprach-spezifischen Embedding-Modell."

### Wie würdest du die Pipeline produktiv ausrollen?

„Drei Schichten. Erstens, ein wöchentlicher Cron-Job, der `enrich` und `report`
fährt — Embeddings und Cluster ändern sich nur, wenn das Keyword-Set
substantiell wächst. Zweitens, ein quartalsweiser voller Lauf inklusive Cluster
und Briefs. Drittens, eine SQLite- oder Postgres-Persistenz für
Lauf-Metadaten. Plus ein einfacher Slack-Webhook am Ende jedes Laufs mit dem
Status. Insgesamt ein Tag Arbeit auf bestehender Basis."

### Wie misst man den Erfolg dieser Pipeline?

„Zwei Ebenen. Methodisch über Silhouette und ARI plus manuelle Spot Checks
pro Cluster. Geschäftlich über die nachgelagerten KPIs: Rankings für die Top-
Keywords, organischer Traffic auf die neuen Pillar-Pages, MQLs aus den
Clustern, mit dem CRM gegenrelegt. Letzteres ist eine Erweiterung, nicht Teil
dieser Lieferung — technisch trivial, sobald ein CRM-Export verfügbar ist."

### Was kostet das?

„Pro vollem Lauf rund einen Dollar. Bei wöchentlichem Lauf etwa fünfzig Dollar
pro Jahr. Vernachlässigbar gegenüber dem Wert eines einzigen rankenden Pillar-
Artikels."

### Warum hast du Discover nicht live umgesetzt?

„Bewusste Trade-off-Entscheidung. Discover ist konzeptionell der schwierigste
Schritt, weil echtes HTML im echten Web ein Wundertüten-Problem ist —
Anti-Bot-Schutz, JavaScript-Rendering, Pagination, Lazy Loading. Ich habe die
Zeit lieber in Cluster, Brief und Reporting gesteckt, weil eine Pipeline ohne
sauberes Discover trotzdem demonstrierbar ist, eine perfekte Discover ohne
Cluster und Brief aber wertlos. Bei einer zweiten Iteration wäre Discover der
erste Schritt."

### Was ist die größte Schwäche der aktuellen Lösung?

„Ehrlich: das fehlende Live-Discover. Die Pipeline läuft auf einem kuratierten
Keyword-Set, das ich nicht aus dem aktuellen zvoove-Blog-Stand abgeleitet habe.
Das ist die einzige Stelle, wo zwischen Demo und Produktion ein klarer Schritt
liegt. Alles andere ist produktionsreif oder zumindest nahe dran."

### Welche Rolle soll AI in der zvoove-Marketing-Strategie spielen, deiner Meinung nach?

„Drei Hebel. Erstens, Discovery — Themen finden, bevor Wettbewerber sie
besetzen. Zweitens, Briefing-Qualität — Redaktion entlasten, Konsistenz
sichern, Time-to-Publish drücken. Drittens, Personalisierung im Funnel —
Recherche-Ergebnisse für unterschiedliche Personas anders anteasern. Diese
Pipeline adressiert die ersten beiden, der dritte Hebel wäre der nächste
Aufbau."

---

## Generalprobe-Tipps

- Sprich die Schlüsselzahlen laut aus, bis sie automatisch kommen: 500 Keywords,
  13 Cluster, 0 Outlier, Silhouette 0,647, ARI 0,811, ~1 USD pro Lauf.
- Halte die Cluster-Map im Browser bereit, eine Live-Demo wirkt stärker als
  jeder Screenshot.
- Bei Q&A: erst zwei Sekunden nachdenken, dann antworten. Wirkt souveräner als
  reflexartige Antworten.
- Wenn du eine Frage nicht beantworten kannst: ruhig sagen „das habe ich nicht
  gemessen, mein Bauchgefühl ist X, sauber prüfen würde ich es so". Ehrlichkeit
  schlägt Improvisation.
- Vermeide Konjunktiv-Häufungen. „Ich würde tun" wirkt schwächer als „Ich tue".
- Ein bewusster Atemzug zwischen den Blöcken. Fünfzehn Minuten sind kürzer als
  sie sich vorbereiten lassen.
