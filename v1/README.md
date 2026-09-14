# KnowYourSponsor

> Independent, statutory corporate solvency ledger and search terminal for the UK Register of Licensed Visa Sponsors.

KnowYourSponsor cross-references all ~127,000 organisations on the UK Home Office Register of Licensed Sponsors (Workers) against official Companies House insolvency filings, Department for Business and Trade (DBT) National Minimum Wage (NMW) enforcement records, and Office for National Statistics (ONS) SOC 2020 salary thresholds.

The entire application runs as a static client-side terminal powered by an off-main-thread Web Worker search engine, providing instant (<25ms) subview queries, zero-allocation table virtualization, and full keyboard-driven navigation.

---

## 1. Statutory Data Sources & Provenance

Every record rendered across KnowYourSponsor originates exclusively from verified UK statutory public registers published under Crown Copyright and the Open Government Licence (OGL v3.0). Zero synthetic or unverified placeholder data is utilized.

| Dataset / Source | Statutory Authority | Ingestion Cadence | Coverage / Scope |
| :--- | :--- | :--- | :--- |
| **Register of Licensed Sponsors (Workers)** | UK Home Office / UK Visas and Immigration (UKVI) | Daily (05:30 UTC) | 127,716 active licensed organisations; Skilled Worker, Global Business Mobility (GBM), Scale-up, and Temporary Worker visa routes. |
| **Free Company Data & Insolvency Index** | Companies House (Executive Agency) | Monthly snapshot + daily deltas | 5.2M UK limited entities; corporate status, liquidation, administration, overdue accounts, and confirmation statement delinquency. |
| **National Minimum Wage (NMW) Enforcement** | Department for Business and Trade (DBT) | Statutory Naming Rounds (Rounds 18–20) | Employers named under Section 19A of the National Minimum Wage Act 1998 for statutory wage arrears. |
| **Standard Occupational Classification (SOC 2020)** | Office for National Statistics (ONS) / Home Office | Statutory revision cycles (April 2024 revised rules) | Going rate 50th percentiles and legal minimum salary thresholds (£38,700 standard floor). |

---

### 2. Autonomous Ingestion Pipeline & Zero-Bloat Data Architecture

The automated data ingestion pipeline runs every business day at **06:00 UTC** via GitHub Actions ([`.github/workflows/daily_sync.yml`](.github/workflows/daily_sync.yml)). It enforces deterministic parsing, cryptographic diffing, and zero-bloat repository hygiene:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DECOUPLED ZERO-BLOAT INGESTION PIPELINE                         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Upstream Scraping & SHA-256 Idempotency Guard                                       │
│    • Dynamically resolves the latest Home Office CSV URL from GOV.UK.                  │
│    • Computes SHA-256 hash. If unchanged (weekends/holidays), terminates as no-op.     │
│                                                                                        │
│ 2. Pipeline Circuit Breakers & Validation                                              │
│    • Volume Floor: If parsed records < 10,000, execution halts and alerts.             │
│    • Byte Repair: Auto-detects and repairs Windows-1252 / UTF-8-BOM byte corruption.   │
│                                                                                        │
│ 3. Longitudinal Differential Engine (scripts/daily_ingest.py)                          │
│    • Loads rolling reference state from GitHub Release asset (state-anchor).           │
│    • Resolves entity changes: new grants, rescinded licences, and rating shifts.       │
│    • Updates static JSON payloads (sponsors.json, meta.json, new/removed_sponsors.json).│
│                                                                                        │
│ 4. Micro-Delta Audit Trails (Zero Git Bloat)                                           │
│    • Writes immutable daily delta (data/deltas/YYYY-MM-DD.json, ~18KB).                │
│    • Caps annual repository history growth to <15MB/year, eliminating DAG pack bloat.  │
│                                                                                        │
│ 5. Atomic Unified Deployment                                                           │
│    • Clobbers rolling release asset state-anchor out-of-band via GitHub CLI.           │
│    • Deploys static build directly to GitHub Pages via actions/deploy-pages in one run,│
│      completely bypassing the GITHUB_TOKEN downstream event suppression platform trap. │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. System Architecture & Technical Specifications

KnowYourSponsor is engineered as a zero-latency, client-side web application. It eliminates main-thread compute bottlenecks by delegating all indexing, bitmask filtering, sorting, and export generation to an isolated Web Worker thread.

```
                  ┌─────────────────────────────────────────┐
                  │          USER BROWSER / CLIENT          │
                  └────────────────────┬────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
       ┌─────────────────────────┐           ┌─────────────────────────┐
       │   MAIN THREAD (DOM)     │           │   WEB WORKER THREAD     │
       │   index.html            │           │   worker.js             │
       ├─────────────────────────┤           ├─────────────────────────┤
       │ • Keyboard Grammar      │           │ • In-Memory Flat Index  │
       │ • Virtualized Row Pool  │◄─────────►│ • Bitmask Intersections │
       │ • Employer Details Pane │ postMessage│ • Exact/Prefix Scans    │
       │ • SVG Threshold Gauge   │           │ • Off-Thread CSV Engine │
       └─────────────────────────┘           └─────────────────────────┘
                    ▲                                     ▲
                    │                                     │
       ┌────────────┴────────────┐           ┌────────────┴────────────┐
       │ Service Worker (sw.js)  │           │ Static Data Storage     │
       │ Cache v3 (Network-First)│           │ data/*.json (Gzipped)   │
       └─────────────────────────┘           └─────────────────────────┘
```

### 3.1 Off-Main-Thread Search Engine (`worker.js`)
- **Memory Footprint:** The 127,000-row register is fetched in parallel and unpacked into columnar arrays and flat continuous search strings (`name town county industry crn`).
- **Multi-Facet Bitmask Filtering:** Filter evaluations across visa routes, rating status, solvency warnings, and sector tags execute in $< 25\text{ms}$.
- **Relevance Scoring:** Computes exact match (Rank 0), prefix match (Rank 1), boundary match (Rank 2), substring match (Rank 3), and broad inclusion (Rank 4).
- **Zero Garbage Collection Stutter:** The worker transfers only the visible 50-row window slice to the main thread via structured cloning, eliminating DOM memory thrashing.

### 3.2 Hardware-Accelerated Virtualization
- **Recycled DOM Pool:** The DOM maintains strictly the visible window plus an overscan buffer.
- **Continuous 120 FPS Rendering:** Elements are positioned via hardware-accelerated transforms, eliminating layout shifts during fast scrolling.

### 3.3 Employer Details & Verification Docket
Selecting any employer (via click or keyboard `J`/`K` + `Enter`) opens the side pane containing:
1. **Home Office Licence Details:** Licence rating tier (A-rating vs B-rating action plan), first-seen inception date, and eligible visa routes.
2. **Companies House Corporate Status:** Company registration number (CRN), statutory status (active, liquidation, administration, strike-off proposed), corporate age, accounting type, and filing delinquency.
3. **National Minimum Wage Enforcement Record:** Statutory arrears amount, worker count, and DBT publication round.
4. **Skilled Worker Salary Threshold Calculator:** Dynamic comparison of the Home Office standard minimum floor (£38,700) against the 50th percentile going rate for the matching SOC 2020 occupation code.
5. **Statutory External Verification Links:** Direct links to Companies House Beta, The London Gazette Insolvency Notices, and LinkedIn job openings.

### 3.4 Keyboard Command Grammar

| Key Binding | Target Scope | Action Executed |
| :--- | :--- | :--- |
| `/` or `Cmd/Ctrl+K` | Global | Focuses and selects the main search input. |
| `Escape` | Global | Clears search input; dismisses the side details docket; resets focus. |
| `J` or `DownArrow` | Data Table | Moves active highlight down to the next sponsor. |
| `K` or `UpArrow` | Data Table | Moves active highlight up to the previous sponsor. |
| `Enter` | Data Table | Expands the selected sponsor's full details docket. |
| `S` | Data Table | Toggles the saved/shortlist status of the highlighted employer. |
| `E` | Data Table | Triggers an immediate off-thread CSV export of active query results. |
| `1` – `6` | Quick Views | `[1] All`, `[2] Added`, `[3] Removed`, `[4] Flagged`, `[5] Downgraded`, `[6] NMW`. |

---

## 4. Archival Gazette Design System

All 781 pages across the site adhere to a unified editorial design system built on physical archival gazette principles:

- **Typography Stack:**
  - `EB Garamond` (Serif): Platform mastheads, editorial headings, brand authority.
  - `IBM Plex Mono` (Monospace): Telemetry band, dates, numerical indicators, CRN codes, and data tables.
  - `Inter` (Sans-Serif): Body copy, table cells, form controls, and interactive elements.
- **Palette Tokens:**
  - Light mode: Warm parchment ground (`#F4F1EA`), panel surface (`#EAE5DA`), paper card (`#FAF8F5`), carbon ink (`#141311`), graphite (`#5A564F`).
  - Dark mode: Recessed dark slate (`#121417`), panel (`#1A1D22`), paper (`#1E2229`), warm cream ink (`#EDE9DF`).
  - Status tokens: Critical/Liquidation (`#8B1E1E`), Warning/Overdue (`#7A5310`), Active/Compliant (`#1D5837`).
- **Telemetry Band:** Uniform header displaying dataset volume, current issue week, and statutory authority across every route.

---

## 5. Repository File Structure

```
.
├── index.html                  # Main Sponsor Register & Verification Directory
├── worker.js                   # Dedicated Web Worker Search & Compute Engine
├── sw.js                       # Service Worker (Cache v3, Network-First Revalidation)
├── manifest.json               # Progressive Web Application (PWA) Manifest
├── robots.txt                  # Search engine crawler permissions & sitemap reference
├── sitemap.xml                 # XML sitemap covering all canonical URLs
├── feed.xml                    # Master RSS 2.0 feed of daily sponsor register changes
├── .nojekyll                   # Disables Jekyll processing for raw static file hosting
│
├── scripts/                    # Ingestion & Diff Automation
│   └── daily_ingest.py         # Autonomous UKVI CSV scraper, diff engine & validator
│
├── data/                       # Static Columnar Payloads
│   ├── deltas/                 # Daily micro-delta immutable audit logs (~18KB)
│   ├── sponsors.json           # Active sponsor register (~1.4MB gzipped tuples)
│   ├── company_flags.json      # Companies House insolvency and filing flags
│   ├── nmw.json                # DBT National Minimum Wage Section 19A records
│   ├── soc_thresholds.json     # ONS SOC 2020 salary going rates & legal baselines
│   ├── regional_changes.json   # 7-day additions and removals by UK town/region
│   ├── new_sponsors.json       # Newly granted sponsor licences
│   ├── removed_sponsors.json   # Rescinded / departed sponsor licences
│   ├── rating_changes.json     # A-to-B rating downgrades and restorations
│   ├── licensed_since.json     # Historical first-seen inception timestamps
│   ├── meta.json               # Lightweight polling header (timestamps, counts)
│   └── sponsors_index.json     # Auxiliary index metadata
│
├── about/                      # Project history, founder, ethics, non-goals
├── methodology/                # Provenance, disambiguation rules, circuit breakers
├── data-api/                   # Public JSON API schemas and documentation
├── pricing/                    # B2B compliance monitoring and data licensing
├── privacy/                    # Zero-knowledge search privacy policy & GDPR
├── watchlist/                  # Technical monitoring specifications
├── insights/                   # Statistical macro breakdown & sector distributions
├── changes/                    # Weekly additions, removals, and permanent archive issues
│   ├── 2026-W36/               # Immutable archive for Week 36
│   └── 2026-W37/               # Immutable archive for Week 37
│
├── feeds/                      # Regional & sector-specific RSS feeds
├── employer/                   # 677 standalone employer intelligence dossier pages
└── [city]/[sector]/            # SEO hub pages for major UK cities and industry sectors
```

---

## 6. Public Data Endpoints

All datasets powering the application are publicly accessible as unauthenticated static JSON endpoints:

- **Active Register:** [`data/sponsors.json`](data/sponsors.json)
- **Daily Micro-Deltas:** [`data/deltas/`](data/deltas/)
- **Solvency Flags:** [`data/company_flags.json`](data/company_flags.json)
- **Minimum Wage Enforcement:** [`data/nmw.json`](data/nmw.json)
- **Salary Thresholds (SOC 2020):** [`data/soc_thresholds.json`](data/soc_thresholds.json)
- **Rolling 7-Day Net Changes:** [`data/regional_changes.json`](data/regional_changes.json)
- **Polling Metadata Header:** [`data/meta.json`](data/meta.json)

---

## 7. Deployment & Local Development

### Local Execution & Testing
The application requires zero build tools, node compilers, or bundlers. It runs directly on any local HTTP server:

```bash
# Run local HTTP server
python3 -m http.server 8000

# Run daily ingestion & diff engine manually
python3 scripts/daily_ingest.py --prev data/sponsors.json --out-dir ./data --out-delta ./data/deltas
```

### Automated GitHub Actions Deployment
The production deployment is hosted on GitHub Pages:
- **Canonical URL:** `https://zephyr4289.github.io/sponsor-g/`
- **Branch:** `main` (synchronized with archive branch `V1`)
- **Automated Cadence:** 06:00 UTC Monday through Friday via [`.github/workflows/daily_sync.yml`](.github/workflows/daily_sync.yml)

---

## 8. Disclaimer & Legal Notice

KnowYourSponsor is an independent data analysis tool built on open public records. It is **not affiliated with the UK Home Office or Companies House** and does **not provide immigration advice**. UK immigration advice is strictly regulated under the Immigration and Asylum Act 1999. For formal advice, consult an adviser registered with the Office of the Immigration Services Commissioner (OISC).
