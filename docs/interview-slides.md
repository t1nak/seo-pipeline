---
marp: true
theme: default
paginate: true
size: 16:9
header: 'SEO-Pipeline für zvoove · Interview'
style: |
  section {
    font-family: 'Inter', 'Helvetica Neue', sans-serif;
    padding: 60px 80px;
  }
  h1 { color: #0d3b66; font-size: 1.8em; }
  h2 { color: #0d3b66; }
  strong { color: #0d3b66; }
  .big { font-size: 3em; font-weight: 700; color: #0d3b66; line-height: 1.1; }
  .sub { color: #5b6b7c; }
  table { font-size: 0.85em; }
  code { background: #f0f4f8; padding: 2px 6px; border-radius: 3px; }
  footer { color: #8a99a8; }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# SEO-Keyword → ContentBrief Pipeline
## für zvoove

<br>

**500 Keywords · 13 Cluster · 0 Outlier**

<br>

<span class="sub">Bewerbung als Revenue AI Architect</span>

---

# Was ist die Aufgabe?

Aus dem **zvoove-Blog** ein Keyword-Set entwickeln und daraus konkrete Content-Empfehlungen ableiten.

<br>

**Vier Schritte:**

1. Keywords gewinnen
2. Thematisch clustern
3. Pro Cluster einen Content-Brief schreiben
4. Alles in ein filterbares Reporting

<br>

<span class="sub">Maximal 500 Keywords. Quelle: <code>zvoove.de/wissen/blog</code></span>

---

# Ergebnis in zwei Zahlen

<div style="display: flex; justify-content: space-around; margin-top: 60px;">

<div style="text-align: center;">
<div class="big">500</div>
<div class="sub">Keywords</div>
</div>

<div style="text-align: center;">
<div class="big">13</div>
<div class="sub">Cluster, 0 Outlier</div>
</div>

<div style="text-align: center;">
<div class="big">240k</div>
<div class="sub">Suchen / Monat</div>
</div>

</div>

<br><br>

**Validiert** mit Silhouette 0,65 und ARI 0,81 gegen ein zweites Verfahren.

---

# Drei interessante Cluster

| Cluster | SV/Monat | Kommerziell | Hebel |
|---|---|---|---|
| HR- & Dokumentenverwaltungssoftware | 45.000 | 89 % | Bottom-of-Funnel |
| Zvoove Plattform & Preise | 23.000 | 97 % | Brand Defense |
| Digitalisierung Personaldienstleistung | 24.000 | 35 % | Top-of-Funnel |

<br>

<span class="sub">Vollständige Tabelle aller 13 Cluster im Dashboard.</span>

---

# Architektur: 6 entkoppelte Schritte

```
Discover  →  Enrich  →  Cluster  →  Brief  →  Report  →  Export
   ↓           ↓          ↓          ↓         ↓          ↓
Keywords    SV/KD/CPC   13 Cluster  Markdown  HTML       JSON
                        + Labels    pro       Dashboard  Airtable
                                    Cluster              Notion
                                                         Sheets
```

<br>

**Warum entkoppelt?**

- Embeddings einmal rechnen
- Cluster-Tuning ohne Neukosten
- Briefs nicht versehentlich neu erzeugen
- Jeder Schritt einzeln ersetzbar

---

# Discover: ehrlicher Stand

**Aktuell:** Stub. Liest ein kuratiertes Keyword-Set aus CSV.

**Geplant:** Live-Scraping vom Blog plus Claude-basierte Keyword-Expansion.

<br>

**Warum nicht jetzt?**

Web-Scraping ist konzeptionell der schwierigste Schritt: Anti-Bot, JavaScript-Rendering, Pagination. Lieber **vier Schritte richtig fertig** als sechs halb fertig.

<br>

<span class="sub">Trade-off transparent in den Architecture Decision Records dokumentiert.</span>

---

# Cluster-Schritt: was ist ein Embedding?

Ein **Embedding** ist eine Zahlenfolge, die die Bedeutung eines Texts beschreibt.

<br>

**Beispiel:**

`Lohnabrechnung Software` ≈ `Payroll Tool`

Andere Wörter, gleiche Bedeutung, **ähnliche Zahlen**.

<br>

<span class="sub">Modell: <code>paraphrase-multilingual-MiniLM-L12-v2</code> · mehrsprachig · 120 MB · läuft ohne GPU</span>

---

# Cluster-Schritt: warum HDBSCAN?

<div style="display: flex; gap: 60px;">

<div style="flex: 1;">

### k-means

- Clusteranzahl muss vorgegeben werden
- Kein Outlier-Konzept
- Setzt sphärische Cluster voraus

</div>

<div style="flex: 1;">

### HDBSCAN ✓

- Findet die Anzahl selbst
- Markiert Ausreißer als Rauschen
- Variable Cluster-Dichte

</div>

</div>

<br>

**Beispiel:** `fachkräftemangel deutschland` — gehört semantisch zu nichts. HDBSCAN sagt das. k-means würde es zwanghaft zuordnen.

---

# Cluster-Schritt: Validierung

<br>

| Metrik | Wert | Bedeutung |
|---|---|---|
| Silhouette | **0,65** | Werte > 0,5 gelten als solide |
| ARI gegen Ward(k=10) | **0,81** | Zwei unabhängige Verfahren stimmen zu 4/5 überein |
| Hyperparameter | Grid Search | Reproduzierbar, nichts geraten |

<br>

**Plausibilitätsprobe bestanden:** zwei mathematisch unabhängige Methoden sehen ähnliche Cluster.

---

# Briefs mit Claude + Prompt Caching

**Pro Cluster ein Markdown-Brief mit:**
Hauptkeyword, Suchintention, Zielgruppe, Outline (H1–H3), 3 Benchmark-URLs, CTA.

<br>

**Prompt Caching:** System-Prompt wird einmal gecached, 13× wiederverwendet
→ rund **90 % Token-Ersparnis**, < 1 USD pro Lauf.

<br>

**Robust:** Retry mit Backoff. Wenn ein Brief fehlschlägt, läuft die Pipeline weiter. Status-Bericht am Ende.

---

# Reporting & Export

**Report:** eine HTML-Datei mit KPIs, Cluster-Tabelle, Charts, Karten-Link.
Bewusst kein Frontend-Framework. Verschickbar per Mail oder Slack.

<br>

**Export:** drei JSON-Dateien

| Datei | Inhalt |
|---|---|
| `clusters.json` | eine Zeile pro Cluster |
| `keywords.json` | eine Zeile pro Keyword |
| `report.json` | alles zusammen |

<br>

**Optional:** direkter Sync nach Airtable oder Google Sheets, per Schalter.

---

# Empfehlung 1: HR-Software

<div class="big" style="font-size: 2em;">45.000 Suchen / Monat</div>

89 % kommerziell · KD ⌀ 53 · 45 Keywords

<br>

**Top-Keywords:**
`dokumentenmanagement software` · `bewerbermanagement software` · `mitarbeiterverwaltung software` · `hr software kmu`

<br>

**Was tun:** Pillar-Pages zu Software-Kategorien, jeweils mit zvoove-Modul als Lösung.

**Hypothese:** 5 % CTR × 2 % MQL-Rate ≈ **45 MQLs / Monat**.

---

# Empfehlung 2: zvoove-Marken-Keywords

<div class="big" style="font-size: 2em;">23.000 Suchen / Monat</div>

97 % kommerziell · KD ⌀ 52 · 34 Keywords

<br>

**Auffällig:** KD 52 für Brand-Begriffe ist **ungewöhnlich hoch**.
→ Vergleichsseiten und Bewertungsportale belegen die SERP.

<br>

**Was tun:** zvoove-Erfahrungen-Hub unter `/produkte/`, der positive Bewertungen aggregiert.

**Defense und Offense in einem.**

---

# Empfehlung 3: Digitalisierung

<div class="big" style="font-size: 2em;">24.000 Suchen / Monat</div>

35 % kommerziell · KD ⌀ 36 · 37 Keywords · **Top-of-Funnel**

<br>

**Top-Keywords:**
`digitalisierung zeitarbeit` · `künstliche intelligenz personaldienstleistung` · `digitale zeiterfassung`

<br>

**Was tun:** Hub `/wissen/digitalisierung-personaldienstleistung/`, der Awareness-Traffic in die kommerziellen Cluster überführt.

**Wirkung:** Pipeline-Influence über 6–12 Monate, nicht direkte Conversion.

---

# Limits & nächste Schritte

<div style="display: flex; gap: 60px;">

<div style="flex: 1;">

### Was fehlt

- Discover ist Stub
- Keine Datenbank, nur Dateien
- Keine GSC-Anbindung

</div>

<div style="flex: 1;">

### Was als Nächstes

1. Discover live machen
2. Search Console anbinden
3. SQLite-Persistenz
4. CMS-Integration (Sanity)

</div>

</div>

<br>

**Bei einer zweiten Iteration:** Discover zuerst bauen, nicht zuletzt.

---

# Was diese Pipeline zeigen soll

**Architektur-Denken** statt Skript-Denken
→ jeder Schritt einzeln ersetzbar

<br>

**Pragmatismus** statt Polish
→ Heuristik klar markiert, Live-Daten optional

<br>

**Revenue-Lens** auf alles
→ jede Empfehlung mit MQL-Hypothese

---

<!-- _class: lead -->

# Danke.

<br>

**Repo:** `github.com/t1nak/seo-pipeline`
**Live-Dashboard:** `t1nak.github.io/seo-pipeline`

<br>

## Fragen?
