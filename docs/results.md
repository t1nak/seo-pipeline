# Ergebnisse: Cluster Katalog

13 Cluster, sortiert nach Gesamt-Suchvolumen pro Monat. Pro Cluster eine Empfehlung mit Funnel Stage, Aufwand, und Revenue Hypothese.

Diese Datei ist als Arbeitsdokument für Marketing und Redaktion gedacht. Zahlen kommen direkt aus `output/clustering/cluster_profiles.csv` und sind reproduzierbar via `python -m src.cluster --step profile`.

## Übersicht

| # | Cluster (DE) | Keywords | SV / Monat | Ø KD | % komm. | Funnel Stage |
|---|---|---|---|---|---|---|
| 11 | B2B-SaaS Kategorie-Heads | 52 | 48.945 | 48 | 77 | Bottom |
| 3 | Kommerzielle SaaS-Heads (Zeit/Software) | 46 | 26.062 | 48 | 93 | Bottom |
| 13 | Branche & Betrieb (Sammelbecken) | 82 | 24.589 | 38 | 38 | Mid / Mixed |
| 5 | Marke: zvoove Produktnamen | 32 | 23.432 | 54 | 100 | Bottom |
| 4 | Operative Anleitungen (gemischt) | 31 | 13.831 | 34 | 26 | Mid |
| 9 | Digitalisierung allgemein | 22 | 12.979 | 38 | 45 | Top / Mid |
| 12 | AÜG / Arbeitsrecht-Pillar | 39 | 12.922 | 30 | 3 | Top |
| 2 | Recruiting & KI-Tools | 34 | 12.075 | 37 | 44 | Mid |
| 6 | HR-Mid-Funnel | 20 | 9.265 | 37 | 30 | Mid |
| 8 | Tarif- & Überlassungsrecht | 20 | 8.942 | 34 | 0 | Top |
| 10 | Gebäudereinigung-Vertikale | 25 | 8.166 | 40 | 52 | Bottom |
| 7 | Equal Pay & Cashflow-Risiko | 15 | 6.262 | 37 | 27 | Mid |
| 1 | Factoring-Grundlagen | 15 | 3.516 | 36 | 27 | Top / Mid |

## Cluster 11: B2B-SaaS Kategorie-Heads

> Größter Cluster nach SV. Klassischer Bottom-of-Funnel Hebel mit hoher kommerzieller Dichte.

**Stats:** 52 Keywords, 48.945 SV / Monat, Ø KD 48, 77 Prozent kommerziell, Ø CPC 6,03 EUR

**Top 5 Keywords:** `dokumentenmanagement software`, `bewerbermanagement software`, `mitarbeiterverwaltung software`, `digitalisierung personaldienstleistung`, `hr software kmu`

**Empfehlung**

Pillar Page Set zu Software Kategorien, jeweils mit zvoove Modul als Lösung. Architektur:

- `/wissen/dokumentenmanagement-software-vergleich/` mit zvoove DMS+ als beworbene Lösung
- `/wissen/bewerbermanagement-software/` mit zvoove Recruit
- `/wissen/mitarbeiterverwaltung-personaldienstleister/` mit zvoove One als Plattform-Antwort

Pro Pillar 2500 bis 3500 Wörter, plus 3 bis 5 Cluster Artikel je 1500 Wörter, die intern auf den Pillar verlinken.

**Aufwand:** mittel. Jeder Pillar braucht Vergleichstabelle, Persona, Pricing Sektion.

**Revenue Hypothese:** Bei 5 Prozent CTR auf 49.000 SV sind das 2.450 Klicks. Bei 2 Prozent Conversion zu MQL: 49 MQLs pro Monat. Bei 30 Prozent MQL-zu-SQL und 20 Prozent Close Rate: ungefähr 3 Neukunden pro Monat aus diesem Cluster. Die Conversion Annahmen sind konservativ und verifizierbar über GSC plus CRM Daten.

## Cluster 3: Kommerzielle SaaS-Heads (Zeit/Software)

> Zweitwichtigster Bottom-Funnel Cluster. Spezifisch auf Zeitarbeit-Software fokussiert.

**Stats:** 46 Keywords, 26.062 SV / Monat, Ø KD 48, 93 Prozent kommerziell, Ø CPC 6,57 EUR

**Top 5 Keywords:** `zeiterfassung software`, `mobile zeiterfassung`, `zeitarbeitssoftware`, `roi zeitarbeit software`, `zeitarbeit software`

**Empfehlung**

Direkter Wettbewerber-Cluster zu Landwehr, Prosoft, sclever. zvoove muss hier ranken. Drei Hebel:

1. Eine Pillar Page `/wissen/zeitarbeitssoftware-vergleich/` mit ehrlicher Vergleichsmatrix
2. Pro Wettbewerber eine eigene Vergleichsseite (`zvoove vs landwehr`, `zvoove vs prosoft`)
3. ROI Rechner als interaktives Tool, das nach `roi zeitarbeit software` rankt

**Aufwand:** hoch, weil ROI Rechner Engineering Aufwand bedeutet. Aber der Wettbewerber ranking ist ohne diesen Differentiator schwer zu schlagen.

**Revenue Hypothese:** Niedrigere Volume aber höhere Conversion als Cluster 11, weil 93 Prozent kommerziell. Geschätzt 30 MQLs pro Monat bei 5 Prozent CTR und 2,5 Prozent Conversion.

## Cluster 13: Branche & Betrieb (Sammelbecken)

> Größter Cluster nach Keyword-Anzahl, aber heterogen. Vorsicht.

**Stats:** 82 Keywords, 24.589 SV / Monat, Ø KD 38, 38 Prozent kommerziell

**Top 5 Keywords:** `zeitarbeit programm`, `zeitarbeit branche entwicklung`, `factoring zeitarbeit`, `crm zeitarbeit`, `saas zeitarbeit`

**Empfehlung**

Dieser Cluster ist ein Catch-all aus Begriffen, die HDBSCAN nicht klar in andere Cluster einordnen konnte. Zwei Schritte:

1. **Sub-Clustering.** Zweiten HDBSCAN Lauf nur auf diesen 82 Keywords ausführen, um Sub-Themen zu finden. Erwartung: 3 bis 5 Sub-Cluster (Branchenmonitor, Software, CRM, Trends).
2. **Selektive Bearbeitung.** Bis das Sub-Clustering steht, nur die Top 10 Keywords nach Priority Score bearbeiten, nicht den ganzen Cluster.

**Risiko:** Wenn ohne Sub-Clustering ein einzelner Pillar Artikel für den ganzen Cluster geschrieben wird, wird er thematisch verwässert und bei keinem Keyword wirklich konkurrenzfähig.

**Aufwand:** vor Bearbeitung erst eine Methodik-Iteration. Dann mittel.

## Cluster 5: Marke: zvoove Produktnamen

> 100 Prozent kommerzieller Brand Cluster. Schneller Win durch klare URL Architektur.

**Stats:** 32 Keywords, 23.432 SV / Monat, Ø KD 54, 100 Prozent kommerziell, Ø CPC 6,71 EUR

**Top 5 Keywords:** `zvoove referenzen`, `zvoove dms`, `zvoove cockpit`, `zvoove payroll`, `zvoove cashlink`

**Empfehlung**

Brand Keywords haben ungewöhnlich hohe KD von 54, was darauf hindeutet, dass aktuell entweder Wettbewerber-Vergleichsseiten oder Bewertungsplattformen wie OMR Reviews die SERP belegen. Drei sofortige Maßnahmen:

1. **Audit der bestehenden Produktseiten.** `zvoove cockpit` muss auf einer dedizierten Produktseite ranken, nicht auf einer Übersicht. Gleiches für payroll, cashlink, dms, recruit.
2. **Erfahrungen Hub.** `zvoove erfahrungen` ist hochkommerziell. Eine eigene Seite mit aggregierten Bewertungen, Case Studies, und einem klaren CTA.
3. **Schema Markup.** Product Schema und Review Schema auf jeder Produktseite, damit zvoove eigene Rich Results in der SERP belegt.

**Aufwand:** niedrig bis mittel. Großteils technische SEO Arbeit auf bestehenden Seiten.

**Revenue Hypothese:** Brand Traffic ist am höchsten konvertierender Traffic überhaupt. Ein zusätzlicher Klick auf `zvoove preise` ist mehr wert als 10 Klicks auf `software vergleich`. Annahme: 10 Prozent CTR auf 23.000 SV sind 2.300 Klicks, bei 5 Prozent Conversion zu MQL sind das 115 hochqualifizierte MQLs.

## Cluster 4: Operative Anleitungen (gemischt)

> Heterogener Mid-Funnel Cluster. Drei Sub-Themen vermischt.

**Stats:** 31 Keywords, 13.831 SV / Monat, Ø KD 34, 26 Prozent kommerziell

**Top 5 Keywords:** `aüg`, `bewerber finden`, `lohnabrechnung sage`, `indeed alternative`, `lohnabrechnung erstellen`

**Empfehlung**

Wie Cluster 13 ist auch dieser Cluster heterogen (Compliance, Recruiting, Lohnabrechnung). Praktisch:

- Die Top 3 Keywords nach Priority bearbeiten, einzeln, nicht als Cluster
- Sub-Clustering später, wenn Daten gewachsen sind

**Aufwand:** niedrig (3 Einzelartikel statt Pillar)

## Cluster 9: Digitalisierung allgemein

> Top-of-Funnel Awareness Cluster, Brückenfunktion zu kommerziellen Themen.

**Stats:** 22 Keywords, 12.979 SV / Monat, Ø KD 38, 45 Prozent kommerziell

**Top 5 Keywords:** `digitalisierung zeitarbeit`, `digitale zeiterfassung`, `elektronische lohnabrechnung`, `gebäudereiniger digital`, `digitale lohnabrechnung`

**Empfehlung**

Strategischer Awareness-Cluster. Fängt Geschäftsführer ab, die noch keine konkrete Software suchen, sondern Trends recherchieren. Zwei Pillar:

1. `/wissen/digitalisierung-zeitarbeit-leitfaden/`: 3000 Wörter, Stand der Branche, ROI Beispiele, Software Kategorien
2. `/wissen/digitale-lohnabrechnung-grundlagen/`: 2000 Wörter, gesetzliche Rahmen, technische Optionen, Tools Vergleich

Beide Pillar sollen intern auf Cluster 11 (B2B-SaaS Heads) und Cluster 3 (Zeitarbeit Software) verlinken, damit Awareness Traffic in den Funnel überführt wird.

**Aufwand:** mittel.

**Revenue Hypothese:** Pipeline-Influence statt direkte Conversion. Awareness Touchpoint, der über 6 bis 12 Monate zu Brand-Suchen führt.

## Cluster 12: AÜG / Arbeitsrecht-Pillar

> Top-of-Funnel Wissens-Hub. Höchste Compliance-Relevanz.

**Stats:** 39 Keywords, 12.922 SV / Monat, Ø KD 30, 3 Prozent kommerziell

**Top 5 Keywords:** `arbeitnehmerüberlassung`, `arbeitnehmerüberlassungsgesetz`, `arbeitsschutz zeitarbeit`, `arbeitgeberanteile sozialversicherung`, `disposition zeitarbeitnehmer`

**Empfehlung**

AÜG-Compliance ist existenziell für jeden Personaldienstleister. Verstöße kosten die Erlaubnis. Hohe Anziehungskraft für Geschäftsführer und Compliance-Verantwortliche.

Konkret:

1. AÜG Pillar Page `/wissen/aueg-grundlagen/`: 4000 Wörter, vollständige Gesetzeserklärung, FAQ, Checklisten
2. 5 bis 7 Cluster Artikel zu Sub-Themen (Höchstüberlassungsdauer, Equal Pay Pflicht, Erlaubnis Antrag, Bußgeld Katalog)
3. PDF Download (AÜG Compliance Checkliste) als Lead Magnet

**Aufwand:** hoch wegen rechtlicher Sorgfaltspflicht. Erfordert juristisches Lektorat oder Quellenangabe an einen Fachanwalt.

**Revenue Hypothese:** Niedrige Conversion Rate (3 Prozent kommerziell), aber starker Pipeline Influence. Compliance Themen werden gegoogelt, wenn ein Audit ansteht oder eine Klage droht. Genau dann wird auch Software gesucht.

## Cluster 2: Recruiting & KI-Tools

> Mid-Funnel mit Tech-Hype Komponente. Konkurrenz wächst schnell.

**Stats:** 34 Keywords, 12.075 SV / Monat, Ø KD 37, 44 Prozent kommerziell

**Top 5 Keywords:** `ki recruiting`, `recruiting software`, `recruiting plattform`, `automatisierung recruiting prozess`, `active sourcing tools`

**Empfehlung**

Aktuell hoher Such-Trend wegen KI Hype. Empfehlung: schnell sein, bevor das Wettbewerber-Set saturiert.

- Pillar `/wissen/ki-recruiting-zeitarbeit/` mit klarer Position: was macht KI in Recruiting konkret, was sind die Fallstricke
- Cluster Artikel zu Sub-Themen (Bewerber Matching, Chatbots, Active Sourcing Tools)
- Verbindung zu zvoove Recruit als Lösung

**Aufwand:** mittel, aber Geschwindigkeit ist hier wichtiger als Tiefe.

## Cluster 6: HR-Mid-Funnel

> Operative HR Themen. Niedriges SV pro Keyword aber hohe Kohäsion.

**Stats:** 20 Keywords, 9.265 SV / Monat, Ø KD 37, 30 Prozent kommerziell

**Top 5 Keywords:** `personaleinsatzplanung`, `personalakte inhalt`, `karriereseite erstellen`, `saas personaldienstleister`, `kennzahlen personaldienstleister`

**Empfehlung**

Solider Mid-Funnel Cluster. Pro Top-Keyword ein eigener How-To Artikel, vernetzt über interne Verlinkung. Keine Pillar Architektur nötig.

**Aufwand:** niedrig (5 bis 7 How-To Artikel).

## Cluster 8: Tarif- & Überlassungsrecht (info)

> Reiner Wissens-Cluster, 0 Prozent kommerziell.

**Stats:** 20 Keywords, 8.942 SV / Monat, Ø KD 34, 0 Prozent kommerziell

**Top 5 Keywords:** `höchstüberlassungsdauer`, `tariflandschaft zeitarbeit`, `igz tarifvertrag aktuell`, `lohnsteuer zeitarbeit`, `einkommensteuer zeitarbeit`

**Empfehlung**

Mit Cluster 12 (AÜG) zusammen behandeln. Beide sind Wissens-Hubs für Compliance, die Sub-Themen ergänzen sich.

**Aufwand:** niedrig (Integration in den AÜG Pillar).

## Cluster 10: Gebäudereinigung-Vertikale

> Eigenständige Branchen-Vertikale. Eigene Sprache, eigene Cluster Logik.

**Stats:** 25 Keywords, 8.166 SV / Monat, Ø KD 40, 52 Prozent kommerziell

**Top 5 Keywords:** `gebäudereinigung software`, `disposition gebäudereinigung`, `auftragsverwaltung gebäudereinigung`, `reinigungskalkulation software`, `unterhaltsreinigung kalkulation`

**Empfehlung**

zvoove bedient Gebäudereinigung als zweite Kernzielgruppe. Eigene Sprache (Revier, Objektkartei, Glasreinigung), daher dedizierte Content Strategie. Pillar `/wissen/gebaeudereinigung-software/`, parallel zu Zeitarbeit Pillar geführt, kein gemeinsamer Pillar.

**Aufwand:** mittel.

## Cluster 7: Equal Pay & Cashflow-Risiko

> Schmaler aber wichtiger Cluster, verbindet Recht und Liquidität.

**Stats:** 15 Keywords, 6.262 SV / Monat, Ø KD 37, 27 Prozent kommerziell

**Top 5 Keywords:** `equal pay zeitarbeit`, `zahlungsausfall absichern`, `zahlungsziele kunden`, `bap tarif aktuell`, `factoring gebühren`

**Empfehlung**

Differenzierender Cluster für zvoove CashLink. Zeitarbeit hat strukturelles Cashflow-Problem (wöchentliche Löhne vs. 30 bis 60 Tage Zahlungsziel). Mix aus Wissens- und Anbieter-Queries.

Ein dedizierter Artikel zum Cashflow-Problem in Zeitarbeit, mit zvoove CashLink als Lösung am Ende. 1500 Wörter, klare Persona (Geschäftsführer KMU mit 50 bis 300 ZAN).

**Aufwand:** niedrig (1 Artikel, hoher Hebel).

## Cluster 1: Factoring-Grundlagen

> Top-of-Funnel Wissens-Cluster, Eingang in den CashLink Funnel.

**Stats:** 15 Keywords, 3.516 SV / Monat, Ø KD 36, 27 Prozent kommerziell

**Top 5 Keywords:** `factoring buchen`, `factoring erlaubnis`, `offenes factoring`, `echtes factoring`, `factoring kfw`

**Empfehlung**

Der Awareness-Pendant zu Cluster 7 (Equal Pay & Cashflow). Wissens-Hub für Factoring Grundlagen, der dann in den CashLink Funnel überführt.

`/wissen/factoring-grundlagen/`: 2500 Wörter, was ist Factoring, welche Typen gibt es (echt, offen), wann lohnt sich was, Beispielrechnung. Verlinkt auf Cluster 7.

**Aufwand:** niedrig.

## Konsolidierte Empfehlung

Wenn Sie morgen anfangen müssten, in dieser Reihenfolge:

1. **Cluster 5 (Marke zvoove)**: Audit der Produktseiten plus Schema Markup. Niedriger Aufwand, hohe Conversion.
2. **Cluster 3 (Kommerzielle SaaS-Heads)**: Pillar plus Wettbewerber-Vergleiche. Höchste kommerzielle Dichte.
3. **Cluster 12 (AÜG Pillar)**: Wissens-Hub als Pipeline-Trigger. Niedrige KD, hoher Pipeline-Wert.
4. **Cluster 11 (B2B-SaaS Heads)**: Pillar Set. Größter Cluster nach SV.

Damit sind in Quartal 1 ungefähr 100.000 SV pro Monat angegangen, mit einer realistischen Mischung aus Bottom-Funnel Conversion und Top-Funnel Pipeline Influence.
