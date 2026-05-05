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
  section.dense { font-size: 21px; padding: 70px 110px 60px 110px; }
  section.dense h1 { margin-bottom: 22px; }
  section.dense p { margin: 8px 0; }
  .auto-flow {
    display: flex;
    align-items: stretch;
    gap: 10px;
    margin: 18px 0 14px 0;
  }
  .auto-card {
    flex: 1;
    border-radius: 10px;
    padding: 14px 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    text-align: center;
    font-size: 0.7em;
  }
  .auto-card .num { font-weight: 700; font-size: 0.9em; opacity: 0.85; letter-spacing: 0.04em; }
  .auto-card .ttl { color: var(--text-strong); font-weight: 700; font-size: 1.3em; line-height: 1.15; min-height: 2.6em; display: flex; align-items: center; justify-content: center; }
  .auto-card .dsc { color: var(--muted); font-size: 0.95em; line-height: 1.3; min-height: 3.6em; }
  .auto-card .chips { display: flex; flex-wrap: wrap; gap: 4px; justify-content: center; padding: 4px 0; }
  .auto-card .chip { background: rgba(0,0,0,0.25); border: 1px solid currentColor; padding: 2px 8px; border-radius: 12px; font-size: 0.92em; color: currentColor; }
  .auto-card .out { color: var(--muted); font-size: 0.85em; margin-top: auto; padding-top: 4px; }
  .auto-card.c1 { color: #60a5fa; background: rgba(96,165,250,0.1); border: 1px solid #60a5fa; }
  .auto-card.c2 { color: #fb923c; background: rgba(251,146,60,0.1); border: 1px solid #fb923c; }
  .auto-card.c3 { color: #4ade80; background: rgba(74,222,128,0.1); border: 1px solid #4ade80; }
  .auto-card.c4 { color: #a78bfa; background: rgba(167,139,250,0.1); border: 1px solid #a78bfa; }
  .infra-row {
    margin-top: 18px;
    padding-top: 14px;
    border-top: 1px solid var(--bg-elevated);
  }
  .infra-label { color: var(--muted); font-size: 0.75em; margin-bottom: 10px; text-align: center; }
  .infra-chips { display: flex; gap: 12px; justify-content: center; }
  .infra-chips .chip { background: var(--bg-elevated); padding: 5px 14px; border-radius: 6px; font-size: 0.78em; color: var(--text); border: 1px solid #334155; }
  .auto-trigger { color: var(--muted); font-size: 0.78em; text-align: center; margin-bottom: 6px; }
  .cost-grid { display: flex; gap: 40px; align-items: center; margin: 30px 0 20px 0; }
  .cost-grid .cost-table { flex: 1.5; }
  .cost-grid .cost-table table { font-size: 0.85em; margin: 0; }
  .cost-grid .cost-headline { flex: 1; text-align: right; }
  .cost-grid .cost-headline .big { font-size: 2.4em; line-height: 1.05; }
  .cost-grid .cost-headline .row { margin-bottom: 18px; }
  .cost-footer { text-align: center; margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--bg-elevated); color: var(--text); font-size: 0.95em; }
  .cluster-cards { display: flex; gap: 16px; margin: 24px 0 16px 0; }
  .cluster-card { flex: 1; padding: 18px 18px 16px 18px; border-radius: 10px; background: var(--bg-elevated); border-top: 3px solid var(--teal); display: flex; flex-direction: column; gap: 8px; }
  .cluster-card.green { border-top-color: #4ade80; }
  .cluster-card.amber { border-top-color: var(--amber); }
  .cluster-card.blue { border-top-color: #60a5fa; }
  .cluster-card .name { color: var(--text-strong); font-weight: 700; font-size: 0.95em; line-height: 1.25; min-height: 2.5em; }
  .cluster-card .sv { color: var(--teal); font-weight: 700; font-size: 1.6em; line-height: 1; margin-top: 4px; }
  .cluster-card .sv-label { color: var(--muted); font-size: 0.75em; margin-top: -2px; }
  .cluster-card .meta { color: var(--text); font-size: 0.78em; margin-top: 6px; }
  .cluster-card .hebel { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 0.75em; font-weight: 600; margin-top: 8px; align-self: flex-start; }
  .cluster-card.green .hebel { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid #4ade80; }
  .cluster-card.amber .hebel { background: rgba(251,191,36,0.15); color: var(--amber); border: 1px solid var(--amber); }
  .cluster-card.blue .hebel { background: rgba(96,165,250,0.15); color: #60a5fa; border: 1px solid #60a5fa; }
  .funnel-legend { display: flex; gap: 24px; padding: 12px 18px; background: var(--bg-elevated); border-radius: 8px; margin-top: 8px; font-size: 0.78em; color: var(--muted); justify-content: space-between; }
  .funnel-legend strong { color: var(--text-strong); font-weight: 600; }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# SEO-Keyword → ContentBrief Pipeline
## für zvoove

**500 Keywords · 13 thematische Cluster**

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

<!-- _class: dense -->

# Leitkriterien

**1 · Flexible Integration in bestehende Systeme**
Daten können per API oder CSV angebunden werden. Ergebnisse werden als JSON oder CSV bereitgestellt und lassen sich technisch problemlos in Google Sheets, Airtable, Notion oder ein CMS erweitern.

**2 · Provider-unabhängig, kein Vendor Lock-in**
Der LLM-Call ist abstrahiert und kann über verschiedene Anbieter laufen: heute Anthropic, morgen OpenAI oder ein lokales Modell — ohne Umbau der Pipeline.

**3 · Wartbar, validiert und übergabefähig**
Die Pipeline ist versioniert, reproduzierbar und durch 42 Tests abgesichert. Die Cluster-Qualität wird zusätzlich über etablierte Metriken wie Silhouette und ARI validiert.

**4 · Modularer, testbarer Aufbau**
Der Prozess besteht aus sechs klar getrennten Schritten. Jeder Schritt ist einzeln testbar, nachvollziehbar und bei Bedarf austauschbar.

---

# Ergebnis in zwei Zahlen

<div style="display: flex; justify-content: space-around; margin: 80px 0 60px 0;">

<div style="text-align: center;">
<div class="big">500</div>
<div class="sub">Keywords</div>
</div>

<div style="text-align: center;">
<div class="big">13</div>
<div class="sub">Cluster</div>
</div>

<div style="text-align: center;">
<div class="big">240k</div>
<div class="sub">Suchen / Monat</div>
</div>

</div>

**Validiert** mit Silhouette 0,65 und ARI 0,81 gegen ein zweites Verfahren.

---

# Drei interessante Cluster

<div class="cluster-cards">

<div class="cluster-card green">
<div class="name">HR- &amp; Dokumenten­verwaltungs­software</div>
<div class="sv">45.000</div>
<div class="sv-label">Suchen / Monat</div>
<div class="meta">89 % kommerziell · KD ⌀ 53</div>
<div class="hebel">Bottom-of-Funnel</div>
</div>

<div class="cluster-card amber">
<div class="name">zvoove Plattform &amp; Preise</div>
<div class="sv">23.000</div>
<div class="sv-label">Suchen / Monat</div>
<div class="meta">97 % kommerziell · KD ⌀ 52</div>
<div class="hebel">Brand Defense</div>
</div>

<div class="cluster-card blue">
<div class="name">Digitalisierung Personal­dienstleistung</div>
<div class="sv">24.000</div>
<div class="sv-label">Suchen / Monat</div>
<div class="meta">35 % kommerziell · KD ⌀ 36</div>
<div class="hebel">Top-of-Funnel</div>
</div>

</div>

<div class="funnel-legend">
<div><strong>Bottom-of-Funnel</strong> · kaufbereit, vergleicht Lösungen</div>
<div><strong>Brand Defense</strong> · sucht nach uns, will Beweise</div>
<div><strong>Top-of-Funnel</strong> · recherchiert, noch früh</div>
</div>

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

# Automatisierung

<div class="auto-trigger">GitHub Actions · Auslöser per Cron-Schedule oder manueller Trigger</div>

<div class="auto-flow">

<div class="auto-card c1">
<div class="num">Step 1</div>
<div class="ttl">Keywords holen<br>& anreichern</div>
<div class="dsc">Volumen, Difficulty und SERP-Merkmale je Keyword</div>
<div class="chips">
<span class="chip">SEMrush</span>
<span class="chip">DataForSEO</span>
<span class="chip">LLM-Set</span>
<span class="chip">CSV</span>
</div>
<div class="out">→ keywords.json</div>
</div>

<div class="auto-card c2">
<div class="num">Step 2</div>
<div class="ttl">Semantisches Clustering</div>
<div class="dsc">Embeddings, Dimensions­reduktion. Anzahl ergibt sich aus den Daten.</div>
<div class="chips">
<span class="chip">MiniLM</span>
<span class="chip">UMAP</span>
<span class="chip">HDBSCAN</span>
</div>
<div class="out">→ clusters.json</div>
</div>

<div class="auto-card c3">
<div class="num">Step 3</div>
<div class="ttl">Content-Briefings</div>
<div class="dsc">Intention, Persona, Outline, SERP-Lücken, CTA. Provider auswechselbar.</div>
<div class="chips">
<span class="chip">Anthropic</span>
<span class="chip">OpenAI</span>
</div>
<div class="out">→ briefing_[cluster].md</div>
</div>

<div class="auto-card c4">
<div class="num">Step 4</div>
<div class="ttl">Reporting</div>
<div class="dsc">Konsolidiertes Dashboard. Plattformen austauschbar.</div>
<div class="chips">
<span class="chip">Pages</span>
<span class="chip">Notion</span>
<span class="chip">Airtable</span>
<span class="chip">Slack</span>
</div>
<div class="out">→ HTML + JSON</div>
</div>

</div>

<div class="infra-row">
<div class="infra-label">Infrastruktur · unsichtbar aber überall</div>
<div class="infra-chips">
<span class="chip">Secrets</span>
<span class="chip">Run-Logs</span>
<span class="chip">Retry-Logik</span>
<span class="chip">Git-Versionierung</span>
</div>
</div>

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

# Was kostet ein Pipeline-Run?

<div class="cost-grid">

<div class="cost-table">

| Komponente | Pro Lauf |
|---|---|
| Embeddings · lokal (MiniLM) | **0 USD** |
| UMAP + HDBSCAN · CPU | **0 USD** |
| DataForSEO Search Volume *(optional)* | ~ 0,75 USD |
| Cluster-Labels (Anthropic Haiku, 1 Batch) | ~ 0,01 USD |
| Briefs (Claude Sonnet, 13× mit Caching) | ~ 0,20 USD |

</div>

<div class="cost-headline">

<div class="row">
<div class="big">≈ 1 USD</div>
<span class="sub">pro vollem Lauf</span>
</div>

<div class="row">
<div class="big amber">≈ 50 USD</div>
<span class="sub">/ Jahr bei wöchentlichem Lauf</span>
</div>

</div>

</div>

<div class="cost-footer">
Vernachlässigbar gegenüber dem Wert <strong>eines</strong> rankenden Pillar-Artikels.
</div>

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
