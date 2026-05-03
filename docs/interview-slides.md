---
marp: true
theme: default
paginate: true
size: 16:9
header: 'SEO-Pipeline für zvoove · Interview'
style: |
  section {
    font-family: 'Inter', 'Helvetica Neue', sans-serif;
    padding: 90px 110px 70px 110px;
    line-height: 1.5;
  }
  section header {
    top: 24px;
    left: 110px;
    color: #8a99a8;
    font-size: 0.7em;
  }
  section::after {
    right: 60px;
    bottom: 30px;
    color: #8a99a8;
  }
  h1 {
    color: #0d3b66;
    font-size: 1.8em;
    margin-top: 0;
    margin-bottom: 36px;
  }
  h2 { color: #0d3b66; margin-bottom: 24px; }
  h3 { color: #0d3b66; margin-bottom: 16px; }
  p { margin: 14px 0; }
  ul, ol { margin: 14px 0; }
  li { margin: 8px 0; }
  strong { color: #0d3b66; }
  table { font-size: 0.85em; margin: 20px 0; border-spacing: 0; }
  th, td { padding: 8px 14px; }
  code { background: #f0f4f8; padding: 2px 6px; border-radius: 3px; font-size: 0.92em; }
  blockquote { border-left: 4px solid #0d3b66; margin: 20px 0; padding: 6px 20px; color: #0d3b66; }
  .big { font-size: 3em; font-weight: 700; color: #0d3b66; line-height: 1.1; }
  .sub { color: #5b6b7c; }
  section.lead { padding: 120px 110px; }
  section.lead h1 { font-size: 2.4em; margin-bottom: 12px; }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# SEO-Keyword → ContentBrief Pipeline
## für zvoove

**500 Keywords · 13 Cluster · 0 Outlier**

<span class="sub">Bewerbung als Revenue AI Architect</span>

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

<div style="text-align: center; margin: 36px 0; font-size: 1.15em;">

**Quelle** → **Keywords** → **Cluster** → **Content Brief pro Cluster** → **Reporting**

</div>

**Beispiel:**

<div style="text-align: center; margin: 24px 0; font-size: 1.05em;">

<code>zvoove.de/wissen/blog</code> → **500 Keywords** → **13 Cluster** → **13 Briefs** → **Dashboard**

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

# Cluster-Schritt: Validierung

| Metrik | Wert | Bedeutung |
|---|---|---|
| Silhouette | **0,65** | Werte > 0,5 gelten als solide |
| ARI gegen Ward(k=10) | **0,81** | Zwei unabhängige Verfahren stimmen zu 4/5 überein |
| Hyperparameter | Grid Search | Reproduzierbar, nichts geraten |

**Plausibilitätsprobe bestanden:** zwei mathematisch unabhängige Methoden sehen ähnliche Cluster.

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

89 % kommerziell · KD ⌀ 53 · 45 Keywords

**Top-Keywords:**
`dokumentenmanagement software` · `bewerbermanagement software` · `mitarbeiterverwaltung software` · `hr software kmu`

**Was tun:** Pillar-Pages zu Software-Kategorien, jeweils mit zvoove-Modul als Lösung.

**Hypothese:** 5 % CTR × 2 % MQL-Rate ≈ **45 MQLs / Monat**.

---

# Empfehlung 2: zvoove-Marken-Keywords

<div class="big" style="font-size: 2em;">23.000 Suchen / Monat</div>

97 % kommerziell · KD ⌀ 52 · 34 Keywords

**Auffällig:** KD 52 für Brand-Begriffe ist **ungewöhnlich hoch**.
→ Vergleichsseiten und Bewertungsportale belegen die SERP.

**Was tun:** zvoove-Erfahrungen-Hub unter `/produkte/`, der positive Bewertungen aggregiert.

**Defense und Offense in einem.**

---

# Empfehlung 3: Digitalisierung

<div class="big" style="font-size: 2em;">24.000 Suchen / Monat</div>

35 % kommerziell · KD ⌀ 36 · 37 Keywords · **Top-of-Funnel**

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
