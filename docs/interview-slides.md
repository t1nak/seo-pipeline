---
marp: true
theme: default
paginate: true
size: 16:9
header: 'SEO-Pipeline für zvoove · Interview'
style: |
  :root {
    --bg: #0f172a;
    --bg-elevated: #1e293b;
    --text: #e2e8f0;
    --text-strong: #f8fafc;
    --muted: #94a3b8;
    --teal: #2dd4bf;
    --teal-soft: #5eead4;
    --amber: #fbbf24;
  }
  section {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', 'Helvetica Neue', sans-serif;
    padding: 80px 110px 70px 110px;
    line-height: 1.45;
    font-size: 24px;
  }
  section header {
    top: 28px;
    left: 110px;
    color: var(--muted);
    font-size: 0.65em;
    letter-spacing: 0.04em;
  }
  section::after {
    right: 60px;
    bottom: 30px;
    color: var(--muted);
    font-size: 0.7em;
  }
  h1 {
    color: var(--text-strong);
    font-size: 1.6em;
    font-weight: 700;
    margin-top: 0;
    margin-bottom: 18px;
    letter-spacing: -0.01em;
  }
  h2 {
    color: var(--teal);
    margin-bottom: 18px;
    font-weight: 600;
  }
  h3 {
    color: var(--text-strong);
    margin-bottom: 10px;
    font-size: 1.05em;
    font-weight: 600;
  }
  p { margin: 10px 0; color: var(--text); }
  ul, ol { margin: 10px 0; }
  li { margin: 6px 0; }
  strong { color: var(--text-strong); font-weight: 700; }
  em { color: var(--teal-soft); font-style: normal; }
  table {
    font-size: 0.85em;
    margin: 16px 0;
    border-spacing: 0;
    border-collapse: separate;
    width: 100%;
  }
  th {
    color: var(--muted);
    font-weight: 600;
    text-align: left;
    border-bottom: 1px solid var(--bg-elevated);
    padding: 10px 14px;
  }
  td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--bg-elevated);
  }
  code {
    background: var(--bg-elevated);
    color: var(--teal-soft);
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.9em;
  }
  blockquote {
    border-left: 3px solid var(--teal);
    margin: 18px 0;
    padding: 4px 18px;
    color: var(--text-strong);
  }
  pre {
    background: var(--bg-elevated);
    color: var(--text);
    padding: 18px 22px;
    border-radius: 6px;
    font-size: 0.78em;
    line-height: 1.45;
  }
  hr {
    border: none;
    border-top: 1px solid var(--bg-elevated);
    margin: 28px 0;
  }
  .big { font-size: 2.6em; font-weight: 700; color: var(--teal); line-height: 1.1; letter-spacing: -0.02em; }
  .sub { color: var(--muted); font-size: 0.92em; }
  .lead-sub { color: var(--muted); }
  .accent { color: var(--teal); }
  .amber { color: var(--amber); }
  .flow {
    text-align: center;
    margin: 22px 0;
    font-weight: 600;
    color: var(--teal);
    font-size: 1em;
  }
  .topright {
    position: absolute;
    top: 80px;
    right: 110px;
    color: var(--muted);
    font-size: 0.85em;
    text-align: right;
    max-width: 360px;
    line-height: 1.4;
  }
  .timeline {
    display: flex;
    justify-content: space-between;
    align-items: stretch;
    position: relative;
    margin: 40px 0 30px 0;
    gap: 20px;
  }
  .timeline::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 12%;
    right: 12%;
    height: 1px;
    background: var(--teal);
    opacity: 0.35;
    z-index: 0;
  }
  .step {
    flex: 1;
    text-align: center;
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .step h3 { color: var(--text-strong); margin: 0; font-size: 1.1em; }
  .step .desc { color: var(--muted); font-size: 0.85em; min-height: 50px; }
  .step .circle {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    border: 2px solid var(--teal);
    background: var(--bg);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: var(--teal);
    font-weight: 700;
    font-size: 1.05em;
    margin: 6px auto;
  }
  .step .circle.amber { border-color: var(--amber); color: var(--amber); }
  .step .metric { font-size: 1.25em; font-weight: 700; color: var(--teal); margin-top: 6px; }
  .step .metric.amber { color: var(--amber); }
  .step .footnote { color: var(--muted); font-size: 0.82em; }
  .fazit-row {
    display: flex;
    align-items: baseline;
    gap: 30px;
    margin-top: 8px;
  }
  .fazit-label { color: var(--teal); font-weight: 700; font-size: 1.05em; min-width: 70px; }
  .lesart {
    position: absolute;
    bottom: 30px;
    left: 110px;
    color: var(--muted);
    font-size: 0.72em;
  }
  section.lead { padding: 130px 110px; }
  section.lead h1 {
    font-size: 2.2em;
    margin-bottom: 14px;
    color: var(--text-strong);
  }
  section.lead h2 {
    color: var(--teal);
    font-size: 1.3em;
    font-weight: 500;
  }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# SEO-Keyword → ContentBrief Pipeline
## für zvoove

**500 Keywords · 13 Cluster · 0 Outlier**

<span class="lead-sub">Bewerbung als Revenue AI Architect</span>

---

# Agenda

<span class="sub">— hier später Outline einfügen —</span>

1. Aufgabe
2. Anforderungen & mein Ansatz
3. Ergebnis
4. Architektur
5. Cluster-Schritt im Detail
6. Briefs & Reporting
7. Drei Empfehlungen für zvoove
8. Limits & nächste Schritte

---

# Was ist die Aufgabe?

**Automatisiere den Prozess:**

<div class="flow">

Quelle → Keywords → Cluster → Content Brief → Reporting

</div>

**Beispiel:**

<div class="flow">

<code>zvoove.de/wissen/blog</code> → 500 Keywords → 13 Cluster → 13 Briefs → Dashboard

</div>

**Warum?**
Im Bereich Zeitarbeit und Personaldienstleistung **organischen Traffic gewinnen, der echte Kaufinteressenten bringt**.

---

# Leitkriterien

**1 · Integration & Continuous Delivery**
Quelle per API oder CSV · Reporting als JSON/CSV · code-seitig erweiterbar Richtung Google Sheets, Airtable, Notion, CMS.

**2 · Provider-unabhängig — keine Lock-in-Abhängigkeit**
LLM-Call über verschiedene Anbieter: Anthropic heute, OpenAI oder lokales Modell morgen — ohne Pipeline-Umbau.

**3 · Technisch maintainable und übergebbar**
42 Tests, versioniert, validiert (Silhouette + ARI), reproduzierbar.

**4 · Modular und testable**
Sechs entkoppelte Schritte. Jeder einzeln testbar, einzeln austauschbar.

---

# Ergebnis in zwei Zahlen

<div style="display: flex; justify-content: space-around; margin: 80px 0 60px 0;">

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

**Validiert** mit Silhouette 0,65 und ARI 0,81 gegen ein zweites Verfahren.

---

# Drei interessante Cluster

| Cluster | SV/Monat | Kommerziell | Hebel |
|---|---|---|---|
| HR- & Dokumentenverwaltungssoftware | 45.000 | 89 % | Bottom-of-Funnel |
| Zvoove Plattform & Preise | 23.000 | 97 % | Brand Defense |
| Digitalisierung Personaldienstleistung | 24.000 | 35 % | Top-of-Funnel |

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

**Warum entkoppelt?**

- Embeddings einmal rechnen
- Cluster-Tuning ohne Neukosten
- Briefs nicht versehentlich neu erzeugen
- Jeder Schritt einzeln ersetzbar

---

# Discover: ehrlicher Stand

**Aktuell:** Stub. Liest ein kuratiertes Keyword-Set aus CSV.

**Geplant:** Live-Scraping vom Blog plus Claude-basierte Keyword-Expansion.

**Warum nicht jetzt?**
Web-Scraping ist konzeptionell der schwierigste Schritt: Anti-Bot, JavaScript-Rendering, Pagination. Lieber **vier Schritte richtig fertig** als sechs halb fertig.

<span class="sub">Trade-off transparent in den Architecture Decision Records dokumentiert.</span>

---

# Cluster-Schritt: was ist ein Embedding?

Ein **Embedding** ist eine Zahlenfolge, die die Bedeutung eines Texts beschreibt.

**Beispiel:**
`Lohnabrechnung Software` ≈ `Payroll Tool`

Andere Wörter, gleiche Bedeutung, **ähnliche Zahlen**.

<span class="sub">Modell: <code>paraphrase-multilingual-MiniLM-L12-v2</code> · mehrsprachig · 120 MB · läuft ohne GPU</span>

---

# Cluster-Schritt: warum HDBSCAN?

<div style="display: flex; gap: 60px; margin-top: 20px;">

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

**Beispiel:** `fachkräftemangel deutschland` — gehört semantisch zu nichts. HDBSCAN sagt das. k-means würde es zwanghaft zuordnen.

---

# Woran erkennt man gutes Clustering?

<span class="sub">Nicht eine einzelne Kennzahl entscheidet — sondern ein konsistentes Gesamtbild.</span>

<div class="topright">Kein Goldstandard ohne Labels — deshalb validieren.</div>

<div class="timeline">

<div class="step">
<h3>Trennschärfe</h3>
<div class="desc">Innerhalb ähnlich, zwischen Clustern verschieden</div>
<div class="circle">1</div>
<div class="metric">Silhouette = 0,65</div>
<div class="footnote">solide Trennung<br>(&gt; 0,5 gilt als gut)</div>
</div>

<div class="step">
<h3>Stabilität</h3>
<div class="desc">Unabhängiges Verfahren findet ähnliche Struktur</div>
<div class="circle amber">2</div>
<div class="metric amber">ARI = 0,81</div>
<div class="footnote">hohe Übereinstimmung<br>mit Ward(k=10)</div>
</div>

<div class="step">
<h3>Plausibilität</h3>
<div class="desc">Parameter systematisch und Segmente interpretierbar</div>
<div class="circle">3</div>
<div class="metric">Grid Search</div>
<div class="footnote">reproduzierbar,<br>nichts geraten</div>
</div>

</div>

<hr>

<div class="fazit-row">
<div class="fazit-label">Fazit</div>
<div>
<strong>Die Cluster sind nicht zufällig, sondern belastbar und interpretierbar.</strong><br>
<span class="sub">Damit ist die Segmentierung stark genug für die nächste Ebene: Profilierung und fachliche Interpretation der Cluster.</span>
</div>
</div>

<div class="lesart">Lesart: gutes Clustering = getrennt + stabil + reproduzierbar + fachlich sinnvoll</div>

---

# Briefs mit Claude + Prompt Caching

**Pro Cluster ein Markdown-Brief mit:**
Hauptkeyword, Suchintention, Zielgruppe, Outline (H1–H3), 3 Benchmark-URLs, CTA.

**Prompt Caching:** System-Prompt wird einmal gecached, 13× wiederverwendet
→ rund **90 % Token-Ersparnis**, < 1 USD pro Lauf.

**Robust:** Retry mit Backoff. Wenn ein Brief fehlschlägt, läuft die Pipeline weiter. Status-Bericht am Ende.

---

# Reporting & Export

**Report:** eine HTML-Datei mit KPIs, Cluster-Tabelle, Charts, Karten-Link.
Bewusst kein Frontend-Framework. Verschickbar per Mail oder Slack.

**Export:** drei JSON-Dateien

| Datei | Inhalt |
|---|---|
| `clusters.json` | eine Zeile pro Cluster |
| `keywords.json` | eine Zeile pro Keyword |
| `report.json` | alles zusammen |

**Optional:** direkter Sync nach Airtable oder Google Sheets, per Schalter.

---

# Empfehlung 1: HR-Software

<div class="big" style="font-size: 2em;">45.000 Suchen / Monat</div>

<span class="sub">89 % kommerziell · KD ⌀ 53 · 45 Keywords</span>

**Top-Keywords:**
`dokumentenmanagement software` · `bewerbermanagement software` · `mitarbeiterverwaltung software` · `hr software kmu`

**Was tun:** Pillar-Pages zu Software-Kategorien, jeweils mit zvoove-Modul als Lösung.

**Hypothese:** 5 % CTR × 2 % MQL-Rate ≈ <span class="amber">**45 MQLs / Monat**</span>.

---

# Empfehlung 2: zvoove-Marken-Keywords

<div class="big" style="font-size: 2em;">23.000 Suchen / Monat</div>

<span class="sub">97 % kommerziell · KD ⌀ 52 · 34 Keywords</span>

**Auffällig:** KD 52 für Brand-Begriffe ist <span class="amber">**ungewöhnlich hoch**</span>.
→ Vergleichsseiten und Bewertungsportale belegen die SERP.

**Was tun:** zvoove-Erfahrungen-Hub unter `/produkte/`, der positive Bewertungen aggregiert.

**Defense und Offense in einem.**

---

# Empfehlung 3: Digitalisierung

<div class="big" style="font-size: 2em;">24.000 Suchen / Monat</div>

<span class="sub">35 % kommerziell · KD ⌀ 36 · 37 Keywords · **Top-of-Funnel**</span>

**Top-Keywords:**
`digitalisierung zeitarbeit` · `künstliche intelligenz personaldienstleistung` · `digitale zeiterfassung`

**Was tun:** Hub `/wissen/digitalisierung-personaldienstleistung/`, der Awareness-Traffic in die kommerziellen Cluster überführt.

**Wirkung:** Pipeline-Influence über 6–12 Monate, nicht direkte Conversion.

---

# Limits & nächste Schritte

<div style="display: flex; gap: 60px; margin-top: 20px;">

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

**Bei einer zweiten Iteration:** Discover zuerst bauen, nicht zuletzt.

---

# Was diese Pipeline zeigen soll

**Architektur-Denken** statt Skript-Denken
→ jeder Schritt einzeln ersetzbar

**Pragmatismus** statt Polish
→ Heuristik klar markiert, Live-Daten optional

**Revenue-Lens** auf alles
→ jede Empfehlung mit MQL-Hypothese

---

<!-- _class: lead -->

# Danke.

**Repo:** `github.com/t1nak/seo-pipeline`
**Live-Dashboard:** `t1nak.github.io/seo-pipeline`

## Fragen?
