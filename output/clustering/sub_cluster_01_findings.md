# Sub-Clustering von Cluster 2 (Branche & Arbeitsrecht)

Reproduzierbar mit:

```bash
python -m src.subcluster --cluster 1 --mcs 8 --ms 3
```

## Ausgangslage

Cluster 2 (display ID, intern hdb=1) ist der Sammelbecken-Cluster aus dem Hauptlauf. 189 Keywords, 64.264 SV / Monat, thematisch heterogen. Der Hauptlauf empfiehlt in [`docs/results.md`](../../docs/results.md) ein zweites HDBSCAN auf nur diesen 189 Keywords vor Vollausarbeitung.

## Methodik

UMAP-Reduktion auf 5D mit `n_neighbors=10` (kleiner als Hauptlauf 15, weil das Sample kleiner ist). HDBSCAN mit `min_cluster_size=8`, `min_samples=3`, `cluster_selection_method=eom`. Random state 42 zur Reproduzierbarkeit.

## Ergebnis

4 Sub-Cluster plus 4 Ausreißer (2,1 Prozent Rauschen). Silhouette 0,506.

| Sub-Cluster | Keywords | SV / Mo | Ø KD | % komm. | Top Keywords |
|---|---|---|---|---|---|
| Sub 0 | 47 | 14.023 | (mid) | 4 | arbeitnehmerüberlassung, arbeitnehmerüberlassungsgesetz, arbeitsschutz zeitarbeit, arbeitgeberanteile sozialversicherung, arbeitsmarkt 2026 |
| Sub 1 | 24 | 9.783 | (mid) | 4 | höchstüberlassungsdauer, liquidität zeitarbeit, tariflandschaft zeitarbeit, igz tarifvertrag aktuell, lohnsteuer zeitarbeit |
| Sub 2 | 19 | 11.706 | (mid) | 21 | debitorenmanagement, equal pay zeitarbeit, zahlungsausfall absichern, zahlungsziele kunden, bap tarif aktuell |
| Sub 3 | 95 | 27.995 | (mid) | 35 | zeitarbeit programm, zeitarbeit branche entwicklung, factoring zeitarbeit, crm zeitarbeit, lohnabrechnung zeitarbeit |

## Interpretation

**Sub 0: AÜG Wissens-Hub.** Pure top-of-funnel Information über Arbeitnehmerüberlassung. 4 Prozent kommerziell. Hauptkeyword `arbeitnehmerüberlassung` (4.131 SV). Klares Pillar-Thema mit FAQ-Format, Compliance-Trigger.

**Sub 1: Tarif- und Überlassungsrecht.** Höchstüberlassungsdauer, IGZ-Tarif, Lohnsteuer, Tariflandschaft. Gehört thematisch sehr nah zu Sub 0, könnte zusammen behandelt werden als ein größerer AÜG/Tarif Wissens-Pillar.

**Sub 2: Cashflow und Equal Pay.** Liquidität, Equal Pay, Zahlungsausfall, BAP-Tarif. Spezialisiertes Sub-Thema mit Verbindung zu zvoove CashLink. 21 Prozent kommerziell, also Mid-Funnel-Hebel.

**Sub 3: Branche und Software (immer noch breit).** 95 Keywords, höchstes Volumen, höchster kommerzieller Anteil. Aber thematisch mischt es weiterhin Software (`zeitarbeit programm`, `crm zeitarbeit`), Factoring (`factoring zeitarbeit`), Lohn und Branchen-Trends. Kandidat für eine dritte Sub-Cluster-Iteration oder manuelle Aufteilung in 3 Sub-Sub-Cluster.

## Empfehlung

Pillar-Architektur basierend auf der Sub-Cluster-Analyse:

1. **Pillar AÜG plus Tarif-Recht** (Sub 0 + Sub 1, kombiniert 71 Keywords, 23.806 SV): autoritativer Wissens-Hub mit FAQ, Verbindung zur Compliance-Software-Empfehlung am Ende.

2. **Pillar Cashflow und Equal Pay** (Sub 2, 19 Keywords, 11.706 SV): Schmaler aber wertvoller Hub mit Verbindung zu zvoove CashLink. 1.500 Wörter genügen.

3. **Sub-Sub-Clustering von Sub 3** vor Bearbeitung. Erwartung: Sub-Software (zeitarbeit programm, crm), Sub-Factoring (factoring zeitarbeit), Sub-Lohn (lohnabrechnung zeitarbeit). Jedes wird ein eigener Pillar oder verschmilzt mit anderen Cluster (z.B. Cluster 3 Kommerzielle Zeit/Software-Heads).

Anders gesagt: das Sub-Clustering hat 2 klare Pillar-Kandidaten (Sub 0+1, Sub 2) und einen weiterhin heterogenen Block (Sub 3), der eine dritte Iteration braucht.

## Artefakte

- `sub_cluster_01.csv` enthält alle 189 Keywords mit ihrer `sub_cluster` Zuordnung sowie die UMAP 2D Koordinaten (`sub_x`, `sub_y`) für eine eventuelle Visualisierung.
- `sub_cluster_01_profiles.csv` enthält die aggregierten Sub-Cluster-Stats.
