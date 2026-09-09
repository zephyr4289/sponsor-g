Every feature in your proposal addresses a real user friction point, but to keep the application lean, authoritative, and zero-maintenance, you must separate **structural leverage** from **interface bloat**.

---

### Tier 1: Non-Negotiable (True Zero-Bloat, Maximum Leverage)

These require almost zero bundle weight, use native browser APIs, and immediately multiply the utility of the data you already have:

* **Deep-Link Query State (`URLSearchParams` Sync)**
* **Verdict:** Essential.
* **Why:** In immigration tools, search results are meant to be passed to recruiters, lawyers, and peers. Storing `?q=...&city=...&sponsor=...` via `history.replaceState` turns the application into a shareable citation engine. Zero extra bytes transferred, zero runtime cost.


* **Salary Threshold Rule Selector (New Entrant & STEM Discounts)**
* **Verdict:** The single highest-value product differentiator.
* **Why:** The £38,700 blanket threshold discourages international graduates who don't realize they qualify for the **£30,960 New Entrant floor** (70% of going rate) or the **£34,830 STEM PhD discount** (80%). Adding a pure-arithmetic 3-pill toggle in the docket costs ~15 lines of JavaScript and transforms the tool from a raw registry into an eligibility engine.


* **Direct Careers & Visa Dork Links in the Docket**
* **Verdict:** High utility, pure HTML.
* **Why:** Candidates don't want to know just that a company holds a license; they want to know if a live vacancy exists. Generating dynamic search URLs (`[https://www.google.com/search?q=](https://www.google.com/search?q=)"[Employer]"+("careers"+OR+"visa+sponsorship")` and direct Indeed/LinkedIn queries) costs zero compute and saves users from manually copying and pasting names.


* **Mobile Bottom-Sheet UX Polish**
* **Verdict:** Essential for retention.
* **Why:** If 60%+ of social traffic (Reddit, LinkedIn, WhatsApp) arrives on mobile devices, a desktop split-pane breaks usability. Implementing a native-feeling bottom sheet via pure CSS (`transform: translateY`, `overscroll-behavior: contain`) ensures the mobile experience matches the desktop polish without pulling in external gesture libraries.



---

### Tier 2: Strong Additions (Require Editorial Discipline)

* **Export Shortlist CSV with Application Workflow Columns**
* **Verdict:** Keep, but keep it lightweight.
* **Refinement:** Don't just dump the raw data. Exporting starred employers with pre-populated tracking columns (`[Employer, Town, Visa Routes, Status, Applied Date, Contact/Link, Notes]`) instantly turns the export into a functional job-hunt tracker for Google Sheets or Excel.


* **Quick Filter Preset Chips**
* **Verdict:** Good, but eliminate playful aesthetic conventions.
* **Refinement:** Drop the emojis (`✨`, `💻`, `🏥`) to maintain the Archival Gazette and Forensic Ledger design language. Style them as understated, ink-bordered text chips directly beneath the search bar:
`[ Newly Licensed (7D) ]` `[ London Tech ]` `[ Graduate Friendly (<£31k) ]` `[ Insolvency Alerts ]`


* **Top 5,000 Programmatic Employer Pages (pSEO)**
* **Verdict:** High organic traffic potential, but execute strictly out-of-tree.
* **Refinement:** Generating 5,000 individual HTML files directly into your Git repository will bloat the commit tree with thousands of file nodes. Only build these static pages into the **ephemeral `/dist` deployment artifact** during the CI build run. Keep the repository source clean.



---

### Tier 3: The Feature to Cut (Classic Feature Bloat)

* **Side-by-Side Sponsor Compare Mode**
* **Verdict:** **Cut.**
* **Why:** This is a classic "sounds cool on paper, never used in practice" feature.
* It introduces multi-selection checkbox states, diffing algorithms, complex mobile responsive tables, and modal overlay overhead.
* In practice, job seekers evaluate employers sequentially or simply open two browser tabs side by side. The engineering and UI complexity far outweighs the marginal utility.



---

### Implementation Order

| Priority | Feature | Complexity | Footprint | Primary Impact |
| --- | --- | --- | --- | --- |
| **P0** | **Deep-Link State Sync** | ~20 lines JS | 0 KB | Virality, forum sharing, and direct docket referencing |
| **P0** | **Salary Discount Selector** | ~35 lines JS | 0 KB | Solves the primary question of graduate and student switchers |
| **P1** | **Dynamic Vacancy Dork Links** | ~10 lines HTML | 0 KB | Bridges the gap between holding a licence and hiring |
| **P1** | **Mobile Bottom-Sheet Refactor** | CSS + Touch handler | 0 KB | Fixes mobile UX for all inbound social traffic |
| **P2** | **Shortlist Workflow CSV Export** | Reuses CSV worker | ~15 lines JS | Creates an instant application tracking system |
| **P2** | **Gazette Quick Filter Chips** | HTML/CSS triggers | 0 KB | Reduces search friction for first-time visitors |

Would you like to draft the exact arithmetic and condition logic for the New Entrant and STEM salary discount toggle first, or wire up the `URLSearchParams` bidirectional state sync?
