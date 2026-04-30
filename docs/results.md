# Ergebnisse: Cluster Katalog

10 Cluster aus 500 Keywords, sortiert nach Gesamt-Suchvolumen pro Monat. Pro Cluster eine Empfehlung mit Funnel Stage, Aufwand, und Revenue Hypothese.

Diese Datei ist als Arbeitsdokument für Marketing und Redaktion gedacht. Zahlen kommen direkt aus `output/clustering/cluster_profiles.csv` und sind reproduzierbar via `python -m src.cluster --step profile`.

## Übersicht

| # | Cluster (DE) | Keywords | SV / Monat | Ø KD | % komm. | Funnel Stage |
|---|---|---|---|---|---|---|
| 2 | Branche & Arbeitsrecht (Sammelbecken) | 189 | 64.264 | 34 | 22 | Mid / Mixed |
| 10 | B2B-SaaS Kategorie-Heads | 44 | 47.989 | 49 | 82 | Bottom |
| 3 | Kommerzielle Zeit/Software-Heads | 47 | 26.159 | 43 | 94 | Bottom |
| 5 | Marke: zvoove Produktnamen | 34 | 23.604 | 51 | 97 | Bottom |
| 6 | Operative Anleitungen (gemischt) | 30 | 13.755 | 33 | 23 | Mid |
| 4 | Recruiting & KI-Tools | 34 | 12.075 | 38 | 44 | Mid |
| 7 | HR-Mid-Funnel | 29 | 10.524 | 35 | 24 | Mid |
| 8 | Gebäudereinigung-Vertikale | 24 | 8.135 | 38 | 50 | Bottom |
| 1 | Factoring-Grundlagen | 15 | 3.516 | 39 | 27 | Top / Mid |
| 9 | Digitalisierung praktisch | 16 | 3.281 | 29 | 44 | Top / Mid |

Plus rund 40 Keywords als Rauschen (~8 Prozent, je nach Plattform leicht variabel). Diese werden nicht bearbeitet, weil sie semantisch isoliert sind und kein klares Pillar Thema bilden.

## Cluster 2: Branche & Arbeitsrecht (Sammelbecken)

> Mit 189 Keywords der mit Abstand größte Cluster. Heterogen, deshalb VORSICHT vor Bearbeitung.

**Stats:** 189 Keywords, 64.264 SV / Monat, Ø KD 34, 22 Prozent kommerziell, Ø CPC 2,79 EUR

**Top 5 Keywords:** `debitorenmanagement`, `arbeitnehmerüberlassung`, `zeitarbeit programm`, `höchstüberlassungsdauer`, `equal pay zeitarbeit`

**Empfehlung**

Dieser Cluster ist ein Catch-all aus Begriffen, die HDBSCAN nicht klar in andere Cluster einordnen konnte. Mischt AÜG Wissen, Software Begriffe, Equal Pay, Liquidität, CRM und Branchen-Trends. Zwei zwingende Schritte vor Bearbeitung:

1. **Sub-Clustering.** Zweiten HDBSCAN Lauf nur auf diesen 189 Keywords ausführen, um Sub-Themen zu finden. Erwartung: 4 bis 6 Sub-Cluster (AÜG Wissen, Equal Pay, Software-Recherche, Cashflow / Factoring, Branchen-Monitor, Lohn-Themen).
2. **Selektive Bearbeitung.** Bis das Sub-Clustering steht, nur die Top 10 Keywords nach Priority Score bearbeiten, nicht den ganzen Cluster.

**Risiko:** Wenn ohne Sub-Clustering ein einzelner Pillar Artikel für den ganzen Cluster geschrieben wird, wird er thematisch verwässert und bei keinem Keyword wirklich konkurrenzfähig.

**Aufwand:** vor Bearbeitung erst eine Methodik-Iteration. Dann hoch (mehrere Pillar plus Cluster Artikel).

**Revenue Hypothese:** Der Cluster ist wertvoll wegen seiner Größe (64.000 SV). Wenn das Sub-Clustering sauber gemacht wird, kann jeder Sub-Pillar 5.000 bis 15.000 SV bedienen. Über alle Sub-Cluster hinweg potential für 30.000 plus Klicks pro Monat bei seriöser Bearbeitung.

## Cluster 10: B2B-SaaS Kategorie-Heads

> Zweitwichtigster Cluster nach SV. Klassischer Bottom-of-Funnel Hebel mit hoher kommerzieller Dichte.

**Stats:** 44 Keywords, 47.989 SV / Monat, Ø KD 49, 82 Prozent kommerziell, Ø CPC 6,11 EUR

**Top 5 Keywords:** `dokumentenmanagement software`, `bewerbermanagement software`, `mitarbeiterverwaltung software`, `digitalisierung personaldienstleistung`, `hr software kmu`

**Empfehlung**

Pillar Page Set zu Software Kategorien, jeweils mit zvoove Modul als Lösung. Architektur:

- `/wissen/dokumentenmanagement-software-vergleich/` mit zvoove DMS+ als beworbene Lösung
- `/wissen/bewerbermanagement-software/` mit zvoove Recruit
- `/wissen/mitarbeiterverwaltung-personaldienstleister/` mit zvoove One als Plattform-Antwort

Pro Pillar 2500 bis 3500 Wörter, plus 3 bis 5 Cluster Artikel je 1500 Wörter, die intern auf den Pillar verlinken.

**Aufwand:** mittel. Jeder Pillar braucht Vergleichstabelle, Persona, Pricing Sektion.

**Revenue Hypothese:** Bei 5 Prozent CTR auf 48.000 SV sind das 2.400 Klicks. Bei 2 Prozent Conversion zu MQL: 48 MQLs pro Monat. Bei 30 Prozent MQL-zu-SQL und 20 Prozent Close Rate: ungefähr 3 Neukunden pro Monat aus diesem Cluster. Die Conversion Annahmen sind konservativ und verifizierbar über GSC plus CRM Daten.

## Cluster 3: Kommerzielle Zeit/Software-Heads

> Zeitarbeit-Software Spezial-Cluster mit höchster kommerzieller Dichte.

**Stats:** 47 Keywords, 26.159 SV / Monat, Ø KD 43, 94 Prozent kommerziell, Ø CPC 6,47 EUR

**Top 5 Keywords:** `zeiterfassung software`, `mobile zeiterfassung`, `zeitarbeitssoftware`, `roi zeitarbeit software`, `zeitarbeit software`

**Empfehlung**

Direkter Wettbewerber-Cluster zu Landwehr, Prosoft, sclever. zvoove muss hier ranken. Drei Hebel:

1. Eine Pillar Page `/wissen/zeitarbeitssoftware-vergleich/` mit ehrlicher Vergleichsmatrix
2. Pro Wettbewerber eine eigene Vergleichsseite (`zvoove vs landwehr`, `zvoove vs prosoft`)
3. ROI Rechner als interaktives Tool, das nach `roi zeitarbeit software` rankt

**Aufwand:** hoch, weil ROI Rechner Engineering Aufwand bedeutet. Aber der Wettbewerber ranking ist ohne diesen Differentiator schwer zu schlagen.

**Revenue Hypothese:** Niedrigere Volume aber höhere Conversion als Cluster 10, weil 94 Prozent kommerziell. Geschätzt 30 MQLs pro Monat bei 5 Prozent CTR und 2,5 Prozent Conversion.

## Cluster 5: Marke: zvoove Produktnamen

> 97 Prozent kommerzieller Brand Cluster. Schneller Win durch klare URL Architektur.

**Stats:** 34 Keywords, 23.604 SV / Monat, Ø KD 51, 97 Prozent kommerziell, Ø CPC 6,44 EUR

**Top 5 Keywords:** `zvoove referenzen`, `zvoove dms`, `zvoove cockpit`, `zvoove payroll`, `zvoove cashlink`

**Empfehlung**

Brand Keywords haben ungewöhnlich hohe KD von 51, was darauf hindeutet, dass aktuell entweder Wettbewerber-Vergleichsseiten oder Bewertungsplattformen wie OMR Reviews die SERP belegen. Drei sofortige Maßnahmen:

1. **Audit der bestehenden Produktseiten.** `zvoove cockpit`, `zvoove payroll`, `zvoove dms`, `zvoove cashlink`, `zvoove recruit` müssen jeweils auf einer dedizierten Produktseite ranken, nicht auf einer Übersicht.
2. **Erfahrungen Hub.** `zvoove referenzen` ist hochkommerziell. Eine eigene Seite mit aggregierten Bewertungen, Case Studies, und einem klaren CTA.
3. **Schema Markup.** Product Schema und Review Schema auf jeder Produktseite, damit zvoove eigene Rich Results in der SERP belegt.

**Aufwand:** niedrig bis mittel. Großteils technische SEO Arbeit auf bestehenden Seiten.

**Revenue Hypothese:** Brand Traffic ist am höchsten konvertierender Traffic überhaupt. Annahme: 10 Prozent CTR auf 23.000 SV sind 2.300 Klicks, bei 5 Prozent Conversion zu MQL sind das 115 hochqualifizierte MQLs.

## Cluster 6: Operative Anleitungen (gemischt)

> Heterogener Mid-Funnel Cluster. Mehrere Sub-Themen vermischt.

**Stats:** 30 Keywords, 13.755 SV / Monat, Ø KD 33, 23 Prozent kommerziell, Ø CPC 2,64 EUR

**Top 5 Keywords:** `aüg`, `bewerber finden`, `lohnabrechnung sage`, `indeed alternative`, `lohnabrechnung erstellen`

**Empfehlung**

Wie Cluster 2 ist auch dieser Cluster heterogen (Compliance, Recruiting, Lohnabrechnung). Praktisch:

- Die Top 3 Keywords nach Priority bearbeiten, einzeln, nicht als Cluster
- Sub-Clustering später, wenn Daten gewachsen sind

**Aufwand:** niedrig (3 Einzelartikel statt Pillar)

## Cluster 4: Recruiting & KI-Tools

> Mid-Funnel mit Tech-Hype Komponente. Konkurrenz wächst schnell.

**Stats:** 34 Keywords, 12.075 SV / Monat, Ø KD 38, 44 Prozent kommerziell, Ø CPC 3,28 EUR

**Top 5 Keywords:** `ki recruiting`, `recruiting software`, `recruiting plattform`, `automatisierung recruiting prozess`, `active sourcing tools`

**Empfehlung**

Aktuell hoher Such-Trend wegen KI Hype. Empfehlung: schnell sein, bevor das Wettbewerber-Set saturiert.

- Pillar `/wissen/ki-recruiting-zeitarbeit/` mit klarer Position: was macht KI in Recruiting konkret, was sind die Fallstricke
- Cluster Artikel zu Sub-Themen (Bewerber Matching, Chatbots, Active Sourcing Tools)
- Verbindung zu zvoove Recruit als Lösung

**Aufwand:** mittel, aber Geschwindigkeit ist hier wichtiger als Tiefe.

## Cluster 7: HR-Mid-Funnel

> Operative HR Themen. Niedriges SV pro Keyword aber hohe Kohäsion.

**Stats:** 29 Keywords, 10.524 SV / Monat, Ø KD 35, 24 Prozent kommerziell, Ø CPC 2,51 EUR

**Top 5 Keywords:** `personaleinsatzplanung`, `personalakte inhalt`, `karriereseite erstellen`, `saas personaldienstleister`, `ki bewerbermanagement`

**Empfehlung**

Solider Mid-Funnel Cluster. Pro Top-Keyword ein eigener How-To Artikel, vernetzt über interne Verlinkung. Keine Pillar Architektur nötig.

**Aufwand:** niedrig (5 bis 7 How-To Artikel).

## Cluster 8: Gebäudereinigung-Vertikale

> Eigenständige Branchen-Vertikale. Eigene Sprache, eigene Cluster Logik.

**Stats:** 24 Keywords, 8.135 SV / Monat, Ø KD 38, 50 Prozent kommerziell, Ø CPC 4,30 EUR

**Top 5 Keywords:** `gebäudereinigung software`, `disposition gebäudereinigung`, `auftragsverwaltung gebäudereinigung`, `reinigungskalkulation software`, `unterhaltsreinigung kalkulation`

**Empfehlung**

zvoove bedient Gebäudereinigung als zweite Kernzielgruppe. Eigene Sprache (Revier, Objektkartei, Glasreinigung), daher dedizierte Content Strategie. Pillar `/wissen/gebaeudereinigung-software/`, parallel zu Zeitarbeit Pillar geführt, kein gemeinsamer Pillar.

**Aufwand:** mittel.

## Cluster 1: Factoring-Grundlagen

> Top-of-Funnel Wissens-Cluster, Eingang in den CashLink Funnel.

**Stats:** 15 Keywords, 3.516 SV / Monat, Ø KD 39, 27 Prozent kommerziell, Ø CPC 3,23 EUR

**Top 5 Keywords:** `factoring buchen`, `factoring erlaubnis`, `offenes factoring`, `echtes factoring`, `factoring kfw`

**Empfehlung**

Wissens-Hub für Factoring Grundlagen, der dann in den CashLink Funnel überführt.

`/wissen/factoring-grundlagen/`: 2500 Wörter, was ist Factoring, welche Typen gibt es (echt, offen), wann lohnt sich was, Beispielrechnung. Verlinkt auf zvoove CashLink Produktseite.

**Aufwand:** niedrig.

## Cluster 9: Digitalisierung praktisch

> Top-of-Funnel Awareness Cluster, Brückenfunktion zu kommerziellen Themen.

**Stats:** 16 Keywords, 3.281 SV / Monat, Ø KD 29, 44 Prozent kommerziell, Ø CPC 3,50 EUR

**Top 5 Keywords:** `elektronische lohnabrechnung`, `gebäudereiniger digital`, `digitale lohnabrechnung`, `business case digitalisierung kmu`, `mahnwesen automatisieren`

**Empfehlung**

Praktischer Awareness-Cluster mit niedriger KD von 29. Fängt Geschäftsführer ab, die konkrete Digitalisierungs-Schritte recherchieren. Zwei How-To Artikel:

1. `/wissen/elektronische-lohnabrechnung-einfuehren/`: 1500 Wörter, schrittweise Einführung
2. `/wissen/mahnwesen-automatisieren/`: 1500 Wörter, Tools Vergleich plus Best Practices

Beide Pillar sollen intern auf Cluster 10 (B2B-SaaS Heads) und Cluster 3 (Zeitarbeit Software) verlinken, damit Awareness Traffic in den Funnel überführt wird.

**Aufwand:** niedrig (2 Artikel).

**Revenue Hypothese:** Pipeline-Influence statt direkte Conversion. Awareness Touchpoint, der über 6 bis 12 Monate zu Brand-Suchen führt.

## Konsolidierte Empfehlung

Wenn Sie morgen anfangen müssten, in dieser Reihenfolge:

1. **Cluster 5 (Marke zvoove)**: Audit der Produktseiten plus Schema Markup. Niedriger Aufwand, hohe Conversion.
2. **Cluster 3 (Kommerzielle Zeit/Software-Heads)**: Pillar plus Wettbewerber-Vergleiche. Höchste kommerzielle Dichte.
3. **Cluster 10 (B2B-SaaS Heads)**: Pillar Set. Zweitgrößter Cluster nach SV.
4. **Cluster 2 (Branche & Arbeitsrecht, Sammelbecken)**: ZUERST Sub-Clustering. DANN Pillar Set. Größter Cluster nach Anzahl, höchstes Volumen.

Damit sind in Quartal 1 ungefähr 130.000 SV pro Monat angegangen, mit einer realistischen Mischung aus Bottom-Funnel Conversion und Top-Funnel Pipeline Influence.

## Hinweis zur Reproduzierbarkeit

Dieser Lauf basiert auf 500 Keywords (Cap aus 504 manuellem Baseline-Set). Ein vorheriger Lauf mit allen 504 Keywords lieferte 13 Cluster und ist als Snapshot gepinnt unter `output/_archive/2026-04-27_manual/`. Die unterschiedliche Cluster-Anzahl (10 vs 13) ist ein Beispiel dafür, wie HDBSCAN auf kleine Datenset-Änderungen reagiert: 4 weniger Keywords haben drei Cluster verschmelzen lassen.
