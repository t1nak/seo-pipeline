# Ergebnisse: Cluster Katalog

13 Cluster aus 500 Keywords (`mcs=10, ms=5, eom`), sortiert nach Gesamt-Suchvolumen pro Monat. Alle 500 Keywords sind einem Cluster zugeordnet — 428 direkt von HDBSCAN, die verbleibenden 72 Rand-Keywords per Soft-Assignment zum nächsten Cluster-Centroid im 5D-UMAP-Raum (siehe [ADR-15](decisions.md#adr-15-soft-assignment-fur-noise-keywords)). Pro Cluster eine Empfehlung mit Funnel-Stage, Aufwand und Revenue-Hypothese. Labels werden pro Lauf von Anthropic Haiku aus den Top-Keywords erzeugt ([ADR-5](decisions.md#adr-5-llm-generierte-cluster-labels-pro-lauf-yaml-als-fallback)).

Die Datei ist als Arbeitsdokument für Marketing und Redaktion gedacht. Zahlen kommen direkt aus `output/clustering/cluster_profiles.csv` und sind reproduzierbar via `python pipeline.py --step cluster && python -m src.labels_llm`.

## Übersicht

| # | Cluster (DE) | Keywords | SV / Monat | Ø KD | % komm. | Funnel Stage |
|---|---|---|---|---|---|---|
| 10 | HR Software Dokumenten- und Mitarbeiterverwaltung | 45 | 45.567 | 52 | 89 | Bottom |
| 12 | Sammelthemen Zeitarbeit Software und Finanzierung | 97 | 28.301 | 36 | 34 | Mid |
| 1 | Zeiterfassung und Zeitarbeitssoftware | 47 | 26.159 | 48 | 94 | Bottom |
| 7 | Digitalisierung Personaldienstleistung und KI | 37 | 23.984 | 36 | 35 | Mid |
| 3 | Zvoove Produkte und Features | 34 | 23.604 | 52 | 97 | Bottom (Brand) |
| 8 | Liquidität Equal Pay und Tariflandschaft | 34 | 15.571 | 33 | 18 | Mid |
| 4 | Sammelthemen Lohnabrechnung und Recruiting | 32 | 14.455 | 34 | 22 | Mid |
| 11 | Arbeitnehmerüberlassung Recht und Sozialversicherung | 44 | 14.429 | 31 | 2 | Top / Mid |
| 6 | Personalverwaltung und Einsatzplanung | 34 | 12.386 | 37 | 32 | Mid |
| 2 | KI-gestützte Recruiting Automatisierung | 34 | 12.075 | 37 | 44 | Mid |
| 5 | Zeitarbeit Markt und Regulierung Deutschland | 20 | 11.462 | 33 | 5 | Top |
| 9 | Gebäudereinigung Disposition und Kalkulation | 27 | 8.467 | 40 | 52 | Bottom (Vertikale) |
| 0 | Factoring Buchhaltung und Genehmigung | 15 | 3.516 | 36 | 27 | Top / Mid |

Die 72 Soft-assigned Keywords (Spalte `noise_assigned=True` in `keywords_labeled.csv`) sind in den oben gezeigten Cluster-Größen bereits enthalten. Im Reporting können sie als „Rand-Keywords" gesondert ausgewertet werden, bekommen aber denselben Brief wie der Cluster-Kern.

## Cluster 10: HR Software Dokumenten- und Mitarbeiterverwaltung

> Größter Cluster nach SV. Klassischer Bottom-of-Funnel-Hebel mit hoher kommerzieller Dichte und klaren Software-Vergleichs-Suchen.

**Stats:** 45 Keywords, 45.567 SV / Monat, Ø KD 52, 89 Prozent kommerziell, Ø CPC 6,47 EUR

**Top 5 Keywords:** `dokumentenmanagement software`, `bewerbermanagement software`, `mitarbeiterverwaltung software`, `hr software kmu`, `gehaltsabrechnung software`

**Empfehlung**

Pillar-Page-Set zu Software-Kategorien, jedes mit dem passenden zvoove-Modul als Lösung:

- `/wissen/dokumentenmanagement-software-vergleich/` mit zvoove DMS+
- `/wissen/bewerbermanagement-software/` mit zvoove Recruit
- `/wissen/mitarbeiterverwaltung-personaldienstleister/` mit zvoove One als Plattform-Antwort

Pro Pillar 2.500 bis 3.500 Wörter, plus 3 bis 5 Cluster-Artikel je 1.500 Wörter, die intern auf den Pillar verlinken.

**Aufwand:** mittel. Jeder Pillar braucht Vergleichstabelle, Persona, Pricing-Sektion.

**Revenue-Hypothese:** Bei 5 Prozent CTR auf 45.000 SV sind das 2.250 Klicks. Bei 2 Prozent Conversion zu MQL: 45 MQLs pro Monat. Bei 30 Prozent MQL-zu-SQL und 20 Prozent Close-Rate: ungefähr 3 Neukunden pro Monat aus diesem Cluster.

## Cluster 12: Sammelthemen Zeitarbeit Software und Finanzierung

> Größter Cluster nach Anzahl. Vom LLM transparent als „Sammelthemen" markiert, weil er heterogene Zeitarbeit-Kombinationen bündelt.

**Stats:** 97 Keywords, 28.301 SV / Monat, Ø KD 36, 34 Prozent kommerziell, Ø CPC 3,45 EUR

**Top 5 Keywords:** `zeitarbeit programm`, `zeitarbeit branche entwicklung`, `factoring zeitarbeit`, `crm zeitarbeit`, `lohnabrechnung zeitarbeit`

**Empfehlung**

Dieser Cluster bündelt „Zeitarbeit + X" Kombinationen aus mehreren operativen Bereichen (Software, Factoring, CRM, Lohn, Branchen-Trends, DSGVO). Das ist redaktionell nicht als ein Brief bearbeitbar. Zwei Schritte vor Bearbeitung:

1. **Sub-Clustering.** Zweiten HDBSCAN-Lauf nur auf diesen 97 Keywords ausführen (`src.subcluster`), um Sub-Themen zu finden. Erwartung: 4 bis 6 Sub-Cluster (Branchen-Software, Factoring-Zeitarbeit, CRM-Zeitarbeit, Lohn-Zeitarbeit, Trend-Berichte).
2. **Selektive Bearbeitung.** Bis zum Sub-Clustering nur die Top 10 Keywords nach Priority Score einzeln bearbeiten, nicht den ganzen Cluster.

**Aufwand:** vor Bearbeitung Methodik-Iteration, dann hoch (mehrere Pillar plus Cluster-Artikel).

**Revenue-Hypothese:** Bei sauberer Sub-Cluster-Bearbeitung können 5.000 bis 8.000 SV pro Sub-Pillar bedient werden. Über alle Sub-Cluster hinweg Potenzial für 12.000 bis 18.000 monatliche Klicks bei seriöser Bearbeitung.

## Cluster 1: Zeiterfassung und Zeitarbeitssoftware

> Direkter Wettbewerber-Cluster. 94 Prozent kommerziell, höchste Conversion-Wahrscheinlichkeit im Set.

**Stats:** 47 Keywords, 26.159 SV / Monat, Ø KD 48, 94 Prozent kommerziell, Ø CPC 6,47 EUR

**Top 5 Keywords:** `zeiterfassung software`, `mobile zeiterfassung`, `zeitarbeitssoftware`, `roi zeitarbeit software`, `zeitarbeit software`

**Empfehlung**

Direkter Wettbewerber-Cluster zu Landwehr, Prosoft, sclever. zvoove muss hier ranken. Drei Hebel:

1. Pillar-Page `/wissen/zeitarbeitssoftware-vergleich/` mit ehrlicher Vergleichsmatrix
2. Pro Wettbewerber eine eigene Vergleichsseite (`zvoove vs landwehr`, `zvoove vs prosoft`)
3. ROI-Rechner als interaktives Tool, das nach `roi zeitarbeit software` rankt

**Aufwand:** hoch (ROI-Rechner ist Engineering). Ohne diesen Differentiator ist Wettbewerber-Ranking schwer.

**Revenue-Hypothese:** Niedrigeres Volumen als Cluster 10, aber höhere Conversion-Rate. Geschätzt 30 MQLs pro Monat bei 5 Prozent CTR und 2,5 Prozent Conversion.

## Cluster 7: Digitalisierung Personaldienstleistung und KI

> Mid-Funnel-Awareness mit hoher Priority und niedriger KD. Brückenkopf in den Funnel.

**Stats:** 37 Keywords, 23.984 SV / Monat, Ø KD 36, 35 Prozent kommerziell, Ø CPC 3,37 EUR

**Top 5 Keywords:** `digitalisierung zeitarbeit`, `digitalisierung personaldienstleistung`, `künstliche intelligenz personaldienstleistung`, `digitale zeiterfassung`, `elektronische lohnabrechnung`

**Empfehlung**

Hohe Priority (16,8), weil das Verhältnis aus SV und KD attraktiv ist und die Themen perfekt auf zvoove-Botschaften einzahlen. Pillar `/wissen/digitalisierung-personaldienstleistung/` als Hub, der Awareness-Traffic gezielt in Cluster 1 (Zeiterfassungssoftware) und Cluster 10 (HR-Software) überführt. Plus drei Cluster-Artikel zu `digitale zeiterfassung`, `elektronische lohnabrechnung`, `künstliche intelligenz personaldienstleistung`.

**Aufwand:** mittel.

**Revenue-Hypothese:** Pipeline-Influence statt direkte Conversion. Bei 6 bis 12 Monaten Reifezeit erwartbar: signifikante Brand-Lift-Wirkung und gestützte Brand-Suchen in Cluster 3.

## Cluster 3: Zvoove Produkte und Features

> 97 Prozent kommerzieller Brand-Cluster. Schneller Win durch URL-Architektur und Schema Markup.

**Stats:** 34 Keywords, 23.604 SV / Monat, Ø KD 52, 97 Prozent kommerziell, Ø CPC 6,44 EUR

**Top 5 Keywords:** `zvoove referenzen`, `zvoove dms`, `zvoove cockpit`, `zvoove payroll`, `zvoove cashlink`

**Empfehlung**

Brand-Keywords mit ungewöhnlich hoher KD von 52. Hinweis darauf, dass Wettbewerber-Vergleichsseiten oder Bewertungsplattformen wie OMR Reviews die SERP belegen. Drei sofortige Maßnahmen:

1. **Audit der bestehenden Produktseiten.** `zvoove cockpit`, `zvoove payroll`, `zvoove dms`, `zvoove cashlink`, `zvoove recruit` müssen jeweils auf einer dedizierten Produktseite ranken, nicht auf einer Übersicht.
2. **Erfahrungen-Hub.** `zvoove referenzen` und `zvoove erfahrungen` sind hochkommerziell. Eigene Seite mit aggregierten Bewertungen, Case Studies, klarem CTA.
3. **Schema Markup.** Product- und Review-Schema auf jeder Produktseite, damit zvoove eigene Rich Results in der SERP belegt.

**Aufwand:** niedrig bis mittel. Großteils technische SEO-Arbeit auf bestehenden Seiten.

**Revenue-Hypothese:** Brand-Traffic ist der höchstkonvertierende Traffic überhaupt. Annahme: 10 Prozent CTR auf 23.000 SV sind 2.300 Klicks, bei 5 Prozent Conversion zu MQL sind das 115 hochqualifizierte MQLs.

## Cluster 8: Liquidität Equal Pay und Tariflandschaft

> Compliance- und Liquiditäts-Cluster mit hoher Priority. Brücke zwischen regulatorischem Wissen und CashLink-Funnel.

**Stats:** 34 Keywords, 15.571 SV / Monat, Ø KD 33, 18 Prozent kommerziell, Ø CPC 2,49 EUR

**Top 5 Keywords:** `debitorenmanagement`, `equal pay zeitarbeit`, `zahlungsausfall absichern`, `liquidität zeitarbeit`, `tariflandschaft zeitarbeit`

**Empfehlung**

Verbindet Compliance-Wissen (`equal pay`, `tariflandschaft`, `igz tarifvertrag`) mit Liquiditäts-Themen (`debitorenmanagement`, `zahlungsausfall`, `liquidität zeitarbeit`). Zwei Pillars:

1. `/wissen/equal-pay-zeitarbeit/` als regulatorischer Hub mit Tariflandschaft-Übersicht
2. `/wissen/debitorenmanagement-personaldienstleister/` mit zvoove CashLink als Lösungs-Anker

**Aufwand:** niedrig bis mittel.

**Revenue-Hypothese:** Pipeline-Influence über die Equal-Pay-Pflicht und Liquiditäts-Sorgen, klassischer Pain Trigger im Personaldienstleistungs-Markt.

## Cluster 4: Sammelthemen Lohnabrechnung und Recruiting

> Vom LLM als „Sammelthemen" markiert. Mischt Lohn-, Recruiting- und SaaS-Begriffe.

**Stats:** 32 Keywords, 14.455 SV / Monat, Ø KD 34, 22 Prozent kommerziell, Ø CPC 2,58 EUR

**Top 5 Keywords:** `aüg`, `bewerber finden`, `lohnabrechnung sage`, `indeed alternative`, `offboarding prozess`

**Empfehlung**

Cluster ist heterogen (Lohnabrechnung, Sourcing, AÜG, SaaS-Lizenz). Pragmatisch:

- Top-3-Keywords nach Priority einzeln bearbeiten (`aüg`, `bewerber finden`, `lizenzmodell saas`)
- Sub-Clustering später, sobald das Set wächst
- `indeed alternative` als Anker für eine Sourcing-Tools-Vergleichsseite, die auf zvoove Recruit verlinkt

**Aufwand:** niedrig (3 bis 5 Einzelartikel statt Pillar).

## Cluster 11: Arbeitnehmerüberlassung Recht und Sozialversicherung

> AÜG- und Compliance-Cluster mit Sozialversicherungs-Bezug. Niedrige kommerzielle Dichte (2 Prozent), aber relevant für Top-of-Funnel und Vertrauensaufbau.

**Stats:** 44 Keywords, 14.429 SV / Monat, Ø KD 31, 2 Prozent kommerziell, Ø CPC 1,81 EUR

**Top 5 Keywords:** `arbeitnehmerüberlassung`, `arbeitnehmerüberlassungsgesetz`, `einkommensteuer zeitarbeit`, `arbeitsschutz zeitarbeit`, `arbeitgeberanteile sozialversicherung`

**Empfehlung**

Reines Wissens-Cluster mit hohem Top-of-Funnel-Wert. Pillar `/wissen/arbeitnehmerueberlassung/` mit klarer Struktur (Definition, AÜG-Pflichten, Höchstüberlassungsdauer, Equal Pay, Sozialversicherung). Daraus 4 bis 6 Cluster-Artikel ableiten. Verlinkung in Cluster 1 und 10 als Lösungs-CTA.

**Aufwand:** mittel.

**Revenue-Hypothese:** Indirekt. Vertrauensanker für Suchen, die später kommerzielle Recherche auslösen.

## Cluster 6: Personalverwaltung und Einsatzplanung

> Operative HR-Themen rund um Personalakte und Karriereseite.

**Stats:** 34 Keywords, 12.386 SV / Monat, Ø KD 37, 32 Prozent kommerziell, Ø CPC 2,82 EUR

**Top 5 Keywords:** `personaleinsatzplanung`, `personalakte inhalt`, `gehaltsabrechnung outsourcing`, `azubi verwaltung`, `karriereseite erstellen`

**Empfehlung**

Solider Mid-Funnel-Cluster. Pro Top-Keyword ein eigener How-To-Artikel, vernetzt über interne Verlinkung. Keine Pillar-Architektur nötig. Verlinkung in Cluster 10 (HR-Software) als Lösungs-CTA.

**Aufwand:** niedrig (5 bis 7 How-To-Artikel).

## Cluster 2: KI-gestützte Recruiting Automatisierung

> Mid-Funnel mit Tech-Hype-Komponente. Wettbewerber-Set wächst schnell.

**Stats:** 34 Keywords, 12.075 SV / Monat, Ø KD 37, 44 Prozent kommerziell, Ø CPC 3,28 EUR

**Top 5 Keywords:** `ki recruiting`, `recruiting software`, `recruiting plattform`, `automatisierung recruiting prozess`, `active sourcing tools`

**Empfehlung**

Hoher Such-Trend wegen KI-Hype. Geschwindigkeit ist hier wichtiger als Tiefe.

- Pillar `/wissen/ki-recruiting-zeitarbeit/` mit klarer Position: was macht KI in Recruiting konkret, was sind die Fallstricke
- Cluster-Artikel zu Sub-Themen (Bewerber-Matching, Chatbots, Active-Sourcing-Tools, Candidate-Experience)
- Verbindung zu zvoove Recruit als Lösung

**Aufwand:** mittel.

## Cluster 5: Zeitarbeit Markt und Regulierung Deutschland

> Top-of-Funnel-Marktwissen. Höchste Priority im Set (17,6).

**Stats:** 20 Keywords, 11.462 SV / Monat, Ø KD 33, 5 Prozent kommerziell, Ø CPC 2,02 EUR

**Top 5 Keywords:** `höchstüberlassungsdauer`, `fachkräftemangel deutschland`, `gig economy deutschland`, `gesetzliche abzüge lohn`, `markt zeitarbeit deutschland`

**Empfehlung**

Marktbericht-Anker mit hohem Such-Volumen und niedriger Konkurrenz. Ein jährlich aktualisierter Marktreport (`zeitarbeit markt deutschland 2026`) als Lead-Magnet, plus 3 bis 4 Cluster-Artikel zu Höchstüberlassungsdauer, Fachkräftemangel, Gig Economy.

**Aufwand:** niedrig bis mittel.

**Revenue-Hypothese:** Lead-Magnet für Marktforschung-Suchen, die an Geschäftsführer und Marktleitung gehen.

## Cluster 9: Gebäudereinigung Disposition und Kalkulation

> Eigenständige Branchen-Vertikale. Eigene Sprache, eigene Cluster-Logik.

**Stats:** 27 Keywords, 8.467 SV / Monat, Ø KD 40, 52 Prozent kommerziell, Ø CPC 4,35 EUR

**Top 5 Keywords:** `gebäudereinigung software`, `disposition gebäudereinigung`, `auftragsverwaltung gebäudereinigung`, `reinigungskalkulation software`, `unterhaltsreinigung kalkulation`

**Empfehlung**

zvoove bedient Gebäudereinigung als zweite Kernzielgruppe. Eigene Sprache (Revier, Objektkartei, Glasreinigung), daher dedizierte Content-Strategie. Pillar `/wissen/gebaeudereinigung-software/` parallel zur Zeitarbeit-Achse, kein gemeinsamer Pillar.

**Aufwand:** mittel.

## Cluster 0: Factoring Buchhaltung und Genehmigung

> Top-of-Funnel-Wissens-Cluster, Eingang in den CashLink-Funnel.

**Stats:** 15 Keywords, 3.516 SV / Monat, Ø KD 36, 27 Prozent kommerziell, Ø CPC 3,23 EUR

**Top 5 Keywords:** `factoring buchen`, `factoring erlaubnis`, `offenes factoring`, `echtes factoring`, `factoring kfw`

**Empfehlung**

Wissens-Hub für Factoring-Grundlagen, der dann in den CashLink-Funnel überführt. `/wissen/factoring-grundlagen/`: 2.500 Wörter, was ist Factoring, welche Typen gibt es (echt, offen), wann lohnt sich was, Beispielrechnung. Verlinkt auf zvoove CashLink Produktseite.

**Aufwand:** niedrig.

## Konsolidierte Empfehlung

Wenn morgen mit der Bearbeitung begonnen würde, wäre eine sinnvolle Reihenfolge:

1. **Cluster 3 (Zvoove Brand)**: Audit der Produktseiten plus Schema Markup. Niedriger Aufwand, höchste Conversion-Dichte.
2. **Cluster 10 (HR-Software)**: Pillar-Set zu Software-Kategorien. Größter Cluster nach SV.
3. **Cluster 1 (Zeiterfassungs- und Zeitarbeitssoftware)**: Pillar plus Wettbewerber-Vergleiche. Höchste kommerzielle Dichte.
4. **Cluster 7 (Digitalisierung)**: Awareness-Hub als Brücke in die kommerziellen Cluster. Hohe Priority, niedrige KD.
5. **Cluster 5 (Zeitarbeit Markt Deutschland)**: Marktreport als Lead-Magnet, höchste Priority im Set.

Die beiden Sammel-Cluster (12 und 4) sind bewusst nicht in der Quartal-1-Liste, weil sie Sub-Clustering brauchen, bevor sie redaktionell handhabbar werden.

Damit sind in Quartal 1 ungefähr 130.000 SV pro Monat angegangen, mit einer Mischung aus Bottom-Funnel-Conversion (Cluster 1, 3, 10), Mid-Funnel-Awareness (Cluster 7) und einem fokussierten Marktreport (Cluster 5).

## Hinweis zur Reproduzierbarkeit

Dieser Lauf basiert auf 500 Keywords (Cap aus 504 manuellem Baseline-Set) mit `mcs=10, ms=5, eom`. HDBSCAN findet 13 Cluster mit 72 Noise-Punkten (14 Prozent), die dann per Soft-Assignment ihrem nächsten Cluster zugeordnet werden — Endzustand 13 Cluster, 500 Keywords, 0 Outlier. Die Wahl von `eom` über `leaf` ist bewusst getroffen für niedrigere Rauschrate, die Wahl von `mcs=10` über `mcs=12` für mehr Themen-Differenzierung (sonst Sammelcluster mit knapp 200 Keywords). Begründung in der [Methodik](methodology.md), Soft-Assignment in [ADR-15](decisions.md#adr-15-soft-assignment-fur-noise-keywords). Frühere Läufe mit `mcs=15, leaf` (13 Cluster, 26 Prozent Noise) sind als Snapshots in `output/_archive/` gepinnt.
