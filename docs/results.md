# Ergebnisse: Cluster Katalog

13 Cluster aus 500 Keywords (`mcs=15, ms=5, leaf`), sortiert nach Gesamt-Suchvolumen pro Monat. Pro Cluster eine Empfehlung mit Funnel-Stage, Aufwand und Revenue-Hypothese. Labels werden pro Lauf von Anthropic Haiku aus den Top-Keywords erzeugt (siehe [ADR-5](decisions.md#adr-5-llm-generierte-cluster-labels-pro-lauf-yaml-als-fallback)), bei einem Re-Run können sich Wortwahl und Reihenfolge leicht ändern.

Diese Datei ist als Arbeitsdokument für Marketing und Redaktion gedacht. Zahlen kommen direkt aus `output/clustering/cluster_profiles.csv` und sind reproduzierbar via `python -m src.cluster --step profile && python -m src.labels_llm`.

## Übersicht

| # | Cluster (DE) | Keywords | SV / Monat | Ø KD | % komm. | Funnel Stage |
|---|---|---|---|---|---|---|
| 9 | HR- und Bewerbermanagementsoftware KMU | 36 | 36.450 | 51 | 86 | Bottom |
| 1 | Zeiterfassungs- und Zeitarbeitssoftware | 47 | 26.159 | 48 | 94 | Bottom |
| 6 | Digitalisierung in Personaldienstleistung | 33 | 23.592 | 37 | 39 | Mid |
| 3 | Zvoove Produktfeatures und Preise | 33 | 23.508 | 53 | 100 | Bottom (Brand) |
| 4 | Lohnabrechnung und Candidate Sourcing | 28 | 13.668 | 35 | 25 | Mid |
| 10 | Arbeitnehmerüberlassung Regulierung und Onboarding | 38 | 13.081 | 30 | 3 | Top / Mid |
| 2 | KI-gestützte Recruiting-Automatisierung | 34 | 12.075 | 37 | 44 | Mid |
| 7 | Debitorenmanagement und Equal Pay | 15 | 11.181 | 37 | 20 | Mid |
| 12 | Zeitarbeit Branchentrends und Einsatzplanung | 28 | 9.537 | 37 | 32 | Top / Mid |
| 5 | Personalakte und Einsatzplanung | 20 | 8.614 | 38 | 30 | Mid |
| 8 | Gebäudereinigung Software und Disposition | 26 | 8.325 | 40 | 50 | Bottom (Vertikale) |
| 0 | Factoring Geschäftsmodelle und Genehmigung | 15 | 3.516 | 36 | 27 | Top / Mid |
| 11 | Zeiterfassung Spezialbranche und Compliance | 17 | 2.492 | 38 | 59 | Mid |

Plus 130 Keywords (~26 Prozent) als Rauschen markiert. Diese werden nicht bearbeitet, weil sie semantisch isoliert sind und kein klares Pillar-Thema bilden. Die hohe Rauschrate ist die Konsequenz aus der Wahl `leaf` statt `eom`: feinere Cluster liefern bessere Brief-Themen, lassen aber mehr Randkeywords ohne klare Zuordnung. Methodische Begründung in der [Methodik](methodology.md).

## Cluster 9: HR- und Bewerbermanagementsoftware KMU

> Größter Cluster nach SV. Klassischer Bottom-of-Funnel-Hebel mit hoher kommerzieller Dichte.

**Stats:** 36 Keywords, 36.450 SV / Monat, Ø KD 51, 86 Prozent kommerziell, Ø CPC 6,35 EUR

**Top 5 Keywords:** `bewerbermanagement software`, `mitarbeiterverwaltung software`, `hr software kmu`, `gehaltsabrechnung software`, `ats software`

**Empfehlung**

Pillar-Page-Set zu Software-Kategorien, jeweils mit dem passenden zvoove-Modul als Lösung:

- `/wissen/bewerbermanagement-software/` mit zvoove Recruit
- `/wissen/mitarbeiterverwaltung-personaldienstleister/` mit zvoove One als Plattform-Antwort
- `/wissen/hr-software-kmu/` als KMU-Einstieg, Verlinkung in beide Richtungen

Pro Pillar 2.500 bis 3.500 Wörter, plus 3 bis 5 Cluster-Artikel je 1.500 Wörter, die intern auf den Pillar verlinken.

**Aufwand:** mittel. Jeder Pillar braucht Vergleichstabelle, Persona, Pricing-Sektion.

**Revenue-Hypothese:** Bei 5 Prozent CTR auf 36.000 SV sind das 1.800 Klicks. Bei 2 Prozent Conversion zu MQL: 36 MQLs pro Monat. Bei 30 Prozent MQL-zu-SQL und 20 Prozent Close-Rate: ungefähr 2 Neukunden pro Monat aus diesem Cluster. Annahmen sind konservativ und über GSC plus CRM verifizierbar.

## Cluster 1: Zeiterfassungs- und Zeitarbeitssoftware

> Direkter Wettbewerber-Cluster. 94 Prozent kommerziell, höchste Conversion-Wahrscheinlichkeit im Set.

**Stats:** 47 Keywords, 26.159 SV / Monat, Ø KD 48, 94 Prozent kommerziell, Ø CPC 6,47 EUR

**Top 5 Keywords:** `zeiterfassung software`, `mobile zeiterfassung`, `zeitarbeitssoftware`, `roi zeitarbeit software`, `zeitarbeit software`

**Empfehlung**

Direkter Wettbewerber-Cluster zu Landwehr, Prosoft, sclever. zvoove muss hier ranken. Drei Hebel:

1. Pillar-Page `/wissen/zeitarbeitssoftware-vergleich/` mit ehrlicher Vergleichsmatrix
2. Pro Wettbewerber eine eigene Vergleichsseite (`zvoove vs landwehr`, `zvoove vs prosoft`)
3. ROI-Rechner als interaktives Tool, das nach `roi zeitarbeit software` rankt

**Aufwand:** hoch (ROI-Rechner ist Engineering). Ohne diesen Differentiator ist Wettbewerber-Ranking schwer.

**Revenue-Hypothese:** Niedrigeres Volumen als Cluster 9, aber höhere Conversion-Rate. Geschätzt 30 MQLs pro Monat bei 5 Prozent CTR und 2,5 Prozent Conversion.

## Cluster 6: Digitalisierung in Personaldienstleistung

> Mid-Funnel-Awareness mit hoher Priorität (Ø Priority 18,4) und niedriger KD. Der Brückenkopf in den Funnel.

**Stats:** 33 Keywords, 23.592 SV / Monat, Ø KD 37, 39 Prozent kommerziell, Ø CPC 3,61 EUR

**Top 5 Keywords:** `digitalisierung zeitarbeit`, `digitalisierung personaldienstleistung`, `künstliche intelligenz personaldienstleistung`, `digitale zeiterfassung`, `elektronische lohnabrechnung`

**Empfehlung**

Hohe Priorität, weil das Verhältnis aus SV und KD attraktiv ist und die Themen perfekt auf zvoove-Botschaften einzahlen. Pillar `/wissen/digitalisierung-personaldienstleistung/` als Hub, der Awareness-Traffic gezielt in Cluster 1 (Zeitarbeitssoftware) und Cluster 9 (HR-ATS) überführt. Plus drei Cluster-Artikel zu `digitale zeiterfassung`, `elektronische lohnabrechnung` und `künstliche intelligenz personaldienstleistung`.

**Aufwand:** mittel.

**Revenue-Hypothese:** Pipeline-Influence statt direkte Conversion. Bei 6 bis 12 Monaten Reifezeit erwartbar: signifikante Brand-Lift-Wirkung und gestützte Brand-Suchen in Cluster 3.

## Cluster 3: Zvoove Produktfeatures und Preise

> 100 Prozent kommerziell. Brand-Cluster mit klarem Quick Win durch URL-Architektur und Schema.

**Stats:** 33 Keywords, 23.508 SV / Monat, Ø KD 53, 100 Prozent kommerziell, Ø CPC 6,61 EUR

**Top 5 Keywords:** `zvoove referenzen`, `zvoove dms`, `zvoove cockpit`, `zvoove payroll`, `zvoove cashlink`

**Empfehlung**

Brand-Keywords mit ungewöhnlich hoher KD von 53. Hinweis darauf, dass Wettbewerber-Vergleichsseiten oder Bewertungsplattformen wie OMR Reviews die SERP belegen. Drei sofortige Maßnahmen:

1. **Audit der bestehenden Produktseiten.** `zvoove cockpit`, `zvoove payroll`, `zvoove dms`, `zvoove cashlink`, `zvoove recruit` müssen jeweils auf einer dedizierten Produktseite ranken, nicht auf einer Übersicht.
2. **Erfahrungen-Hub.** `zvoove referenzen` und `zvoove erfahrungen` sind hochkommerziell. Eigene Seite mit aggregierten Bewertungen, Case Studies, klarem CTA.
3. **Schema Markup.** Product- und Review-Schema auf jeder Produktseite, damit zvoove eigene Rich Results in der SERP belegt.

**Aufwand:** niedrig bis mittel. Großteils technische SEO-Arbeit auf bestehenden Seiten.

**Revenue-Hypothese:** Brand-Traffic ist der höchstkonvertierende Traffic überhaupt. Annahme: 10 Prozent CTR auf 23.000 SV sind 2.300 Klicks, bei 5 Prozent Conversion zu MQL sind das 115 hochqualifizierte MQLs.

## Cluster 4: Lohnabrechnung und Candidate Sourcing

> Heterogener Mid-Funnel. Operative Lohn-Themen plus Recruiting-Hilfen, beides für Personaldienstleister relevant.

**Stats:** 28 Keywords, 13.668 SV / Monat, Ø KD 35, 25 Prozent kommerziell, Ø CPC 2,72 EUR

**Top 5 Keywords:** `aüg`, `bewerber finden`, `lohnabrechnung sage`, `indeed alternative`, `lohnabrechnung erstellen`

**Empfehlung**

Cluster ist heterogen (Lohnabrechnung, Sourcing, AÜG-Begriffe). Pragmatisch:

- Top-3-Keywords nach Priority einzeln bearbeiten (`aüg`, `bewerber finden`, `lizenzmodell saas`)
- Sub-Clustering später, sobald das Set wächst
- `indeed alternative` als Anker für eine Sourcing-Tools-Vergleichsseite, die auf zvoove Recruit verlinkt

**Aufwand:** niedrig (3 bis 5 Einzelartikel statt Pillar).

## Cluster 10: Arbeitnehmerüberlassung Regulierung und Onboarding

> AÜG- und Compliance-Cluster. Niedrige kommerzielle Dichte (3 Prozent), aber relevant für Vertrauensaufbau und Top-of-Funnel.

**Stats:** 38 Keywords, 13.081 SV / Monat, Ø KD 30, 3 Prozent kommerziell, Ø CPC 1,91 EUR

**Top 5 Keywords:** `arbeitnehmerüberlassung`, `arbeitnehmerüberlassungsgesetz`, `arbeitsschutz zeitarbeit`, `arbeitgeberanteile sozialversicherung`, `disposition zeitarbeitnehmer`

**Empfehlung**

Reines Wissens-Cluster mit hohem Top-of-Funnel-Wert. Pillar `/wissen/arbeitnehmerueberlassung/` mit klarer Struktur (Definition, AÜG-Pflichten, Höchstüberlassungsdauer, Equal Pay, Sozialversicherung). Daraus 4 bis 6 Cluster-Artikel ableiten. Verlinkung in Cluster 1 und 9 als Lösungs-CTA.

**Aufwand:** mittel.

**Revenue-Hypothese:** Indirekt. Vertrauensanker für Suchen, die später kommerzielle Recherche auslösen.

## Cluster 2: KI-gestützte Recruiting-Automatisierung

> Mid-Funnel mit Tech-Hype-Komponente. Wettbewerber-Set wächst schnell.

**Stats:** 34 Keywords, 12.075 SV / Monat, Ø KD 37, 44 Prozent kommerziell, Ø CPC 3,28 EUR

**Top 5 Keywords:** `ki recruiting`, `recruiting software`, `recruiting plattform`, `automatisierung recruiting prozess`, `active sourcing tools`

**Empfehlung**

Hoher Such-Trend wegen KI-Hype. Geschwindigkeit ist hier wichtiger als Tiefe.

- Pillar `/wissen/ki-recruiting-zeitarbeit/` mit klarer Position: was macht KI in Recruiting konkret, was sind die Fallstricke
- Cluster-Artikel zu Sub-Themen (Bewerber-Matching, Chatbots, Active-Sourcing-Tools)
- Verbindung zu zvoove Recruit als Lösung

**Aufwand:** mittel.

## Cluster 7: Debitorenmanagement und Equal Pay

> Höchste Priority im Set (19,3). Kompakter Cluster mit ungewöhnlich konzentriertem Suchvolumen pro Keyword.

**Stats:** 15 Keywords, 11.181 SV / Monat, Ø KD 37, 20 Prozent kommerziell, Ø CPC 2,42 EUR

**Top 5 Keywords:** `debitorenmanagement`, `equal pay zeitarbeit`, `zahlungsausfall absichern`, `zahlungsziele kunden`, `bap tarif aktuell`

**Empfehlung**

Brücke zwischen Compliance-Wissen (`equal pay`, `bap tarif`) und Liquiditäts-Themen (`debitorenmanagement`, `zahlungsausfall`). Zwei Pillars:

1. `/wissen/equal-pay-zeitarbeit/` als regulatorischer Hub
2. `/wissen/debitorenmanagement-personaldienstleister/` mit zvoove CashLink als Lösungs-Anker

**Aufwand:** niedrig bis mittel (15 Keywords, gut bearbeitbar).

## Cluster 12: Zeitarbeit Branchentrends und Einsatzplanung

> Zukunfts- und Trend-Themen. Hoher Awareness-Wert, niedrige bis mittlere Conversion-Rate.

**Stats:** 28 Keywords, 9.537 SV / Monat, Ø KD 37, 32 Prozent kommerziell, Ø CPC 3,23 EUR

**Top 5 Keywords:** `zeitarbeit branche entwicklung`, `saas zeitarbeit`, `einsatzplanung zeitarbeit`, `zukunft zeitarbeit`, `ausbildung zeitarbeit`

**Empfehlung**

Solider Mid-Funnel-Cluster, gut für Thought-Leadership-Inhalte. Ein jährlich aktualisierter Trend-Report (`zeitarbeit branche entwicklung 2026`) als Lead-Magnet, plus 3 bis 4 Cluster-Artikel zu `einsatzplanung`, `saas zeitarbeit`, `zukunft zeitarbeit`.

**Aufwand:** niedrig bis mittel.

## Cluster 5: Personalakte und Einsatzplanung

> Operative HR-Themen. Niedriges SV pro Keyword aber hohe Kohäsion.

**Stats:** 20 Keywords, 8.614 SV / Monat, Ø KD 38, 30 Prozent kommerziell, Ø CPC 2,80 EUR

**Top 5 Keywords:** `personaleinsatzplanung`, `personalakte inhalt`, `saas personaldienstleister`, `kennzahlen personaldienstleister`, `factoring personaldienstleister`

**Empfehlung**

Solider Mid-Funnel-Cluster. Pro Top-Keyword ein eigener How-To-Artikel, vernetzt über interne Verlinkung. Keine Pillar-Architektur nötig.

**Aufwand:** niedrig (5 bis 7 How-To-Artikel).

## Cluster 8: Gebäudereinigung Software und Disposition

> Eigenständige Branchen-Vertikale. Eigene Sprache, eigene Cluster-Logik.

**Stats:** 26 Keywords, 8.325 SV / Monat, Ø KD 40, 50 Prozent kommerziell, Ø CPC 4,26 EUR

**Top 5 Keywords:** `gebäudereinigung software`, `disposition gebäudereinigung`, `auftragsverwaltung gebäudereinigung`, `reinigungskalkulation software`, `unterhaltsreinigung kalkulation`

**Empfehlung**

zvoove bedient Gebäudereinigung als zweite Kernzielgruppe. Eigene Sprache (Revier, Objektkartei, Glasreinigung), daher dedizierte Content-Strategie. Pillar `/wissen/gebaeudereinigung-software/` parallel zur Zeitarbeit-Achse, kein gemeinsamer Pillar.

**Aufwand:** mittel.

## Cluster 0: Factoring Geschäftsmodelle und Genehmigung

> Top-of-Funnel-Wissens-Cluster, Eingang in den CashLink-Funnel.

**Stats:** 15 Keywords, 3.516 SV / Monat, Ø KD 36, 27 Prozent kommerziell, Ø CPC 3,23 EUR

**Top 5 Keywords:** `factoring buchen`, `factoring erlaubnis`, `offenes factoring`, `echtes factoring`, `factoring kfw`

**Empfehlung**

Wissens-Hub für Factoring-Grundlagen, der dann in den CashLink-Funnel überführt. `/wissen/factoring-grundlagen/`: 2.500 Wörter, was ist Factoring, welche Typen gibt es (echt, offen), wann lohnt sich was, Beispielrechnung. Verlinkt auf zvoove CashLink Produktseite.

**Aufwand:** niedrig.

## Cluster 11: Zeiterfassung Spezialbranche und Compliance

> Vertikalen-Cluster. Niedriges Gesamt-SV, aber 59 Prozent kommerziell und stark fokussiert.

**Stats:** 17 Keywords, 2.492 SV / Monat, Ø KD 38, 59 Prozent kommerziell, Ø CPC 5,20 EUR

**Top 5 Keywords:** `zeiterfassung pflege`, `zeiterfassung handwerk`, `zeiterfassung kostenlos`, `zeiterfassung dsgvo`, `zeitarbeit corona auswirkung`

**Empfehlung**

Vertikalen-Plays: `zeiterfassung pflege` und `zeiterfassung handwerk` als zwei Branchen-Landingpages mit klaren Compliance-Ankern (DSGVO, branchenspezifische Pflichten). Verlinkung in Cluster 1 (Zeiterfassungssoftware) als Software-Lösung.

**Aufwand:** niedrig.

## Konsolidierte Empfehlung

Wenn morgen mit der Bearbeitung begonnen würde, wäre eine sinnvolle Reihenfolge:

1. **Cluster 3 (Zvoove Brand)**: Audit der Produktseiten plus Schema Markup. Niedriger Aufwand, höchste Conversion-Dichte.
2. **Cluster 1 (Zeiterfassungs- und Zeitarbeitssoftware)**: Pillar plus Wettbewerber-Vergleiche. Höchste kommerzielle Dichte mit nennenswertem Volumen.
3. **Cluster 9 (HR- und Bewerbermanagementsoftware KMU)**: Pillar-Set. Größter Cluster nach SV, klare KMU-Adressierung.
4. **Cluster 6 (Digitalisierung)**: Awareness-Hub als Brücke in die kommerziellen Cluster. Hohe Priority, niedrige KD.
5. **Cluster 7 (Debitorenmanagement und Equal Pay)**: Quick Win, weil kompakt und hochpriorisiert.

Damit sind in Quartal 1 ungefähr 121.000 SV pro Monat angegangen, mit einer Mischung aus Bottom-Funnel-Conversion (Cluster 1, 3, 9), Mid-Funnel-Awareness (Cluster 6) und einem fokussierten Quick Win (Cluster 7).

## Hinweis zur Reproduzierbarkeit

Dieser Lauf basiert auf 500 Keywords (Cap aus 504 manuellem Baseline-Set) mit `mcs=15, ms=5, leaf` und 13 Clustern. Frühere Läufe mit anderen Hyperparametern (z.B. `mcs=12, eom` mit 10 Clustern, oder 504 Keywords ohne Cap) sind als Snapshots in `output/_archive/` gepinnt. Die unterschiedliche Cluster-Anzahl ist ein Beispiel dafür, wie HDBSCAN auf Hyperparameter und Datenset-Variationen reagiert. Die Wahl von `leaf` über `eom` ist bewusst für Brief-Granularität getroffen, mit dem Trade-off einer höheren Rauschrate; Begründung in der [Methodik](methodology.md).
