# KnowYourSponsor (sponsorsignal) — Staff UI & Frontend Systems Architecture

**Document Type:** Staff-Level UI/UX Architecture & Systems Specification

**Classification:** Public Domain / High-Density Technical Blueprint

**Status:** Approved for Implementation

**Aesthetic Grammar:** The Archival Gazette & Forensic Ledger (Warm Parchment / Hairline Rule / Optical Serif / Tabular Mono)

## 1. Design Philosophy & Visual Lexicon

### 1.1 The Epistemic Shift

Consumer web applications routinely prioritize marketing fluff: oversized hero banners, ambiguous saturated colors, heavy drop shadows, and low-density card grids that obscure actionable data.

For KnowYourSponsor, the UI must embody the gravitas, permanence, and exactitude of an **official national gazette and forensic intelligence terminal**. When an immigrant worker or an immigration attorney evaluates an employer, they are investigating legal residency risks and corporate solvency. The design must communicate uncompromising institutional authority:

* **Zero SaaS Bloat:** No rounded pill cards, no floating gradients, no decorative emojis, no ambiguous marketing adjectives ("supercharged", "seamless").

* **Physical Print Heritage:** Drawing from the Swiss grid system, central bank statistical bulletins, and 19th-century parliamentary papers (e.g., *The London Gazette*).

* **Information Density First:** 100% of above-the-fold screen real estate serves navigation, query filtering, and high-density tabular data. Zero vertical waste.

* **Typographic Hierarchy as Structure:** Boundaries are defined by 1px hairline rules and rigorous typographic scale, not box shadows or multi-layered container cards.

### 1.2 Mathematical Design Tokens & Color Space

All colors are strictly defined in high-fidelity neutral palettes with unbleached cellulose undertones, eliminating sterile digital blue-grays.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE ARCHIVAL COLOR PALETTE                                │
├───────────────────────────────┬───────────┬────────────────────────────────────────────┤
│ Token Identifier              │ Hex Value │ Functional Role / Semantics                │
├───────────────────────────────┼───────────┼────────────────────────────────────────────┤
│ `--surface-ground`            │ `#F4F1EA` │ Base canvas: Unbleached archival parchment │
│ `--surface-panel`             │ `#EAE5DA` │ Secondary fill: Pressed linen wash         │
│ `--surface-recessed`          │ `#DFD9CC` │ Inset search cavities & table headers      │
│ `--surface-paper`             │ `#FAF8F5` │ Selected entity docket / active inspection │
│                               │           │                                            │
│ `--ink-carbon`                │ `#141311` │ Primary typography: High-contrast deep ink │
│ `--ink-graphite`              │ `#5A564F` │ Secondary metadata: Aged pencil lead       │
│ `--ink-faint`                 │ `#8C867A` │ Captions, table column labels, timestamps  │
│                               │           │                                            │
│ `--rule-hairline`             │ `#D3CDC0` │ Structural separation: 1px oxidized rule   │
│ `--rule-prominent`            │ `#A8A193` │ Active boundaries, split panes, focus rings│
│ `--rule-master`               │ `#141311` │ Masthead and summary ledger framing        │
├───────────────────────────────┴───────────┴────────────────────────────────────────────┤
│                   EVIDENTIARY & LEGAL STATUS ACCENTS (DESATURATED)                     │
├───────────────────────────────┬───────────┬────────────────────────────────────────────┤
│ `--status-critical-ink`       │ `#8B1E1E` │ Liquidation, Strike-Off, Dissolved, Revoked│
│ `--status-critical-wash`      │ `#F5E1E1` │ Background fill for terminal warnings      │
│ `--status-critical-rule`      │ `#D8A4A4` │ Border for fatal corporate anomalies       │
│                               │           │                                            │
│ `--status-warning-ink`        │ `#7A5310` │ Dormant accounts, Overdue confirmation     │
│ `--status-warning-wash`       │ `#F3EAD8` │ Background fill for compliance cautions    │
│ `--status-warning-rule`       │ `#D8C496` │ Border for accounting irregularity badges  │
│                               │           │                                            │
│ `--status-regular-ink`        │ `#1D5837` │ A-Rated, Solvent, Active & Compliant       │
│ `--status-regular-wash`       │ `#E2EDE6` │ Background fill for solvent verifications  │
│ `--status-regular-rule`       │ `#A2C7B2` │ Border for standard verified status        │
└───────────────────────────────┴───────────┴────────────────────────────────────────────┘



```

### 1.3 Typographic Matrix & Micro-Typography

Typography is divided strictly by cognitive domain:

|

| **Domain** | **Font Family** | **Weight & Optical Size** | **Tracking & Line Height** | **Target Elements** |
| **Gazette Masthead & Titles** | `EB Garamond` / `Newsreader` | 500 Medium (Display Optical Size) | `letter-spacing: +0.06em`, `line-height: 1.1` | Application title, Docket company name, Gazette volume headers. |
| **Operational Interface** | `Inter` / `Geist Sans` | 400 Regular / 500 Medium | `letter-spacing: -0.01em`, `line-height: 1.4` | Table content, sector tags, button labels, modal descriptions. |
| **Forensic Identifiers & Metrics** | `IBM Plex Mono` / `Geist Mono` | 400 Regular / 600 Semi-Bold | `letter-spacing: 0.00em`, `font-variant-numeric: tabular-nums` | CRN (Company Registration Number), LBA counts, Dates, Percentages, SIC Codes. |

## 2. Information Architecture & Viewport Topology

The layout replaces vertical scrolling sections with an ergonomic, split-plane analytical workspace that eliminates viewport thrashing.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ MASTHEAD & TELEMETRY BAND                                                                                              │
│ [ THE REGISTER OF LICENSED SPONSORS ]                 [ VOL. 2026 · ISSUE W37 ] [ SNAPSHOT: 2026-09-09 15:50 UTC ]    │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ SYSTEM LEDGER HUD (4-Column Continuous Rule)                                                                           │
│  TOTAL LICENSED ENTITIES   │  WEEKLY ADDITIONS (+7D)   │  TERMINAL DISTRESS (FLAGGED) │  OVERDUE / NON-COMPLIANT       │
│  127,716                   │  +302                     │  2,795                       │  6,695                         │
│  Home Office Worker Tier   │  Lowest Applicant Drag    │  Liquidation / Strike-Off    │  Companies House Deficiencies  │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ SOLVENCY MACRO RATIO (100% Width Proportional Continuous Meter)                                                        │
│ [██████████████████████████████████████████████████████████████████████████████████▒▒▒▒▒▒▒▒░░░░]                       │
│  ● Active & Solvent (91.0%)              ▲ Overdue / Dormant Accounts (6.8%)       ■ Strike-Off / Insolvent (2.2%)     │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ INTEGRATED OMNIBAR & FACET LEDGER                                                                                      │
│ [ 🔍 Query corporate identity, CRN, or town (Press '/' to focus)...                               ] [Export CSV]       │
│ [ VIEW: Master Index (127k) ] [ Recent Additions (302) ] [ Revocations (242) ] [ Flagged Only (9.5k) ] [ ★ Saved (0) ]│
│ [ City: All Jurisdictions ▾ ] [ Sector: All Classifications ▾ ] [ Route: Skilled Worker ▾ ] [ Rating: A / B ▾ ]       │
├─────────────────────────────────────────────────────────────────────────────────┬──────────────────────────────────────┤
│ PRIMARY DATA LEDGER (Virtualized 120 FPS Table)                                 │ FORENSIC DOCKET (Sticky Split-Pane)  │
│ COMPANY / CRN / INCORP   │ LOCALITY      │ SECTOR MATRIX │ STATUS EVALUATION    │ [ ACME LOGISTICS SYSTEMS LTD ]       │
├──────────────────────────┼───────────────┼───────────────┼──────────────────────┤ CRN: 06365302 · Incorporated: 2007   │
│ BAE Systems Plc          │ London        │ Aerospace &   │ [ A-Rated · Active ] │                                      │
│ CRN: 01470151 · 1979     │ Gr. London    │ Defence       │                      │ 1. Home Office Licence Lineage       │
├──────────────────────────┼───────────────┼───────────────┼──────────────────────┤ • Rating: A-Rating (Approved)        │
│ Acme Logistics Ltd       │ Manchester    │ Logistics &   │ [ ⚠️ Liquidation ]   │ • Routes: Skilled Worker             │
│ CRN: 06365302 · 2007     │ Lancashire    │ Freight       │                      │ • Recorded Inception: 2026-08-31     │
├──────────────────────────┼───────────────┼───────────────┼──────────────────────┤                                      │
│ MedCare Clinical LLP     │ Birmingham    │ Healthcare    │ [ A-Rated · Active ] │ 2. Companies House Solvency Autopsy  │
│ CRN: OC389210 · 2014     │ West Midlands │ & Nursing     │                      │ • Corporate Status: Liquidation      │
├──────────────────────────┼───────────────┼───────────────┼──────────────────────┤ • Accounts Category: Exemption Full  │
│ Apex Digital Media       │ Leeds         │ Media &       │ [ ▲ Accounts Late ]  │ • SIC Code: 49410 (Freight Transport)│
│ CRN: 09841239 · 2015     │ Yorkshire     │ Creative      │                      │ • Overdue Date: 2026-06-30           │
│                          │               │               │                      │                                      │
│                          │               │               │                      │ 3. Forensic Alert & Risk Appraisal   │
│                          │               │               │                      │ ┌──────────────────────────────────┐ │
│                          │               │               │                      │ │ ADVISORY: Company in liquidation.│ │
│                          │               │               │                      │ │ Legal rights to issue CoS are    │ │
│                          │               │               │                      │ │ legally impaired.                │ │
│                          │               │               │                      │ └──────────────────────────────────┘ │
│                          │               │               │                      │ [ Examine Companies House Record ↗ ] │
│                          │               │               │                      │ [ Search Open Roles on LinkedIn ↗ ]  │
└──────────────────────────┴───────────────┴───────────────┴──────────────────────┴──────────────────────────────────────┘



```

## 3. High-Density Analytical Visualizations

Instead of decorative, low-information charts (pie charts, standard donut graphs), all visual components are precision instruments designed for immediate data extraction.

### 3.1 The Solvency Macro Proportional Rule

A 4px horizontal rule spanning the entire viewport directly below the telemetry band. It provides an immediate macro-overview of the entire UK sponsor ecosystem:

* **Active & Solvent Segment:** Green tone (`--status-regular-ink`), scaled precisely to $91.0\%$.

* **Compliance Overdue / Dormant Segment:** Amber tone (`--status-warning-ink`), scaled precisely to $6.8\%$.

* **Insolvency / Strike-Off Segment:** Crimson tone (`--status-critical-ink`), scaled precisely to $2.2\%$.

* **Interaction:** Hovering or clicking any segment instantly locks the table to that specific health subset without dropdown hunting.

### 3.2 Longitudinal Churn Matrix (Weekly Delta Comparison)

A compact, typeset ledger module that visualizes the rate of churn across the register:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ LONGITUDINAL REGISTRY CHURN MATRIX (ROLLING 4-WEEK OBSERVATION)                        │
├──────────────┬──────────────────┬──────────────────┬─────────────────┬─────────────────┤
│ WEEK CYCLE   │ NEW LICENCES (+) │ RESCINDED (-)    │ NET DELTA       │ DOWNGRADED (A→B)│
├──────────────┼──────────────────┼──────────────────┼─────────────────┼─────────────────┤
│ 2026-W37     │ +302 sponsors    │ -242 sponsors    │ +60 net         │ 3 sponsors      │
│ 2026-W36     │ +288 sponsors    │ -261 sponsors    │ +27 net         │ 1 sponsor       │
│ 2026-W35     │ +315 sponsors    │ -210 sponsors    │ +105 net        │ 5 sponsors      │
│ 2026-W34     │ +274 sponsors    │ -298 sponsors    │ -24 net         │ 2 sponsors      │
└──────────────┴──────────────────┴──────────────────┴─────────────────┴─────────────────┘



```

### 3.3 The Skilled Worker Salary & Threshold Compatibility Calculator

Integrated directly into the Forensic Docket for any inspected company:

* Computes the UK Home Office April 2024 revised threshold (£38,700 minimum baseline or the 50th percentile of the Standard Occupational Classification / SOC code, whichever is higher).

* Displays a compact, horizontal threshold gauge comparing typical sector salaries against the sponsor's eligibility minimum.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ SKILLED WORKER SALARY THRESHOLD CALCULATOR (SOC 2136: SOFTWARE PROFESSIONALS)          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Minimum Legal Baseline: £38,700/yr  │  Going Rate (50th percentile): £49,400/yr        │
│                                                                                        │
│ Threshold Gauge:                                                                       │
│ £0k                        £38.7k (Gov Minimum)         £49.4k (Going Rate)      £80k  │
│ ├────────────────────────────┼───────────────────────────┼─────────────────────────┤   │
│                              ▲                           ▲                             │
│                              │ Current Legal Floor       │ Required Sponsorship Level  │
└────────────────────────────────────────────────────────────────────────────────────────┘



```

## 4. Frontend Systems & Performance Architecture

The current production bottleneck stems from forcing the browser to fetch, parse, and evaluate **11.4 MB of raw JSON on the main UI thread**. This creates a 2–4 second time-to-interactive penalty on mobile devices and drops UI render loops to 15–30 FPS during rapid typing.

We overhaul the frontend engine into a **zero-jank, off-thread compute architecture**:

```
graph TD
    subgraph Network & Storage Layer
        CDN[GitHub Pages / CDN] -->|Compressed Payload 1.4MB| Cache[Cache API / IndexedDB]
        Cache --> Buffer[SharedArrayBuffer / Transferable Array]
    end

    subgraph Dedicated Web Worker Thread (Engine)
        Buffer --> Worker[Query & Bitset Search Worker]
        Worker --> Bitmask[Multi-Facet Bitmask Intersection]
        Worker --> Fuzzy[SIMD WASM Levenshtein / Exact Match]
        Worker --> Sort[Index Sort & Projection]
    end

    subgraph Main Browser UI Thread (DOM)
        Sort -->|Transferable 50-Item Page Slice| Window[Zero-Allocation Virtualizer]
        Window --> DOM[120 FPS Gazette Table Render]
        DOM --> Docket[Forensic Inspection Docket]
        User[Keystroke / Filter Interaction] -->|PostMessage Zero-Copy| Worker
    end



```

### 4.1 The 11.4MB Payload Liquidation: Columnar Binary Packing

Instead of downloading bloated JSON arrays of strings and nested arrays, the dataset is compiled at build time into an indexed, columnar binary array:

1. **Dictionary Encoding:** All repetitive strings (Towns, Counties, Industries, Visa Routes) are mapped to 16-bit integers (`uint16`).

   * Example: `"London"` is encoded as `0x0001`, `"Tech & Software"` as `0x0004`.

2. **Compact Binary Layout (`sponsors.bin`):**

   * Each record occupies a fixed **32-byte struct** in memory:

     ```
     [0..3]   uint32 : Company Name String Pool Offset
     [4..5]   uint16 : Town Index
     [6..7]   uint16 : County Index
     [8..9]   uint16 : Industry / SIC Index
     [10..11] uint16 : Route Bitmask (Bit 0: Skilled Worker, Bit 1: GBM, etc.)
     [12]     uint8  : Rating (0 = A, 1 = B)
     [13]     uint8  : Solvency Status (0 = Active, 1 = Overdue, 2 = Liquidation, 3 = Strike-Off)
     [14..17] uint32 : Companies House CRN Integer
     [18..21] uint32 : Licence First-Seen Epoch Days
     [22..31] uint8[10]: Reserved Padding (16-byte aligned)
     
     
     
     ```

3. **Payload Compression:**

   * $127,716 \text{ records} \times 32 \text{ bytes} \approx \mathbf{4.08 \text{ MB}}$ raw uncompressed memory.

   * Compressing this highly repetitive columnar binary struct using Zstandard or Brotli reduces the initial network download to $\sim 1.1 \text{ MB}$ **to** $1.4 \text{ MB}$—an $88\%$ **reduction in network payload**.

### 4.2 Off-Main-Thread Search Engine (Web Worker Architecture)

The main thread must never execute multi-term string matching. All compute is isolated to a Web Worker:

* **Bitmask Filtering:** Route selection, status warnings, and rating filters are executed as pure bitwise operations on `Uint32Array` buffers:

  $$
  \text{FilterMask} = \text{RouteBitmask} \ \& \ \text{StatusBitmask} \ \& \ \text{IndustryBitmask}
  $$

  Evaluating 127,000 integers using bitwise AND takes $< 0.8\text{ ms}$.

* **Trigram Index / Exact Prefix Scan:** The worker evaluates company names using a pre-computed suffix/prefix table. Keystroke latency drops below $4\text{ ms}$, eliminating input lag.

* **Transferable Page Slices:** When the user types or scrolls, the worker computes the visible window (e.g., records 0 to 50) and transfers the slice back to the main thread via `postMessage(slice, [slice.buffer])` with **zero object duplication and zero garbage collector pressure**.

### 4.3 Hardware-Accelerated Virtualization Engine

Rather than mounting thousands of DOM elements or paginating with clunky page buttons:

* **The Viewport Engine:** Renders a fixed container with an absolute-positioned scroll spacer representing the total dataset height ($\text{Count} \times 44\text{px}$).

* **Recycled Row Pool:** The DOM maintains strictly the visible window plus a 4-row overscan buffer ($\sim 24 \text{ DOM nodes}$ total).

* **0-Byte Frame Budget:** Rows are transformed via `style.transform = translateY(...)`. No DOM nodes are created or destroyed during fast flings, locking scroll performance to **120 FPS on ProMotion / high-refresh displays**.

## 5. The Forensic Inspection Docket (Slide-Over Pane)

When any sponsor is selected (via click or keyboard navigation `J`/`K` + `Enter`), the right-hand split docket reveals the full legal and operational dossier of the company.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FORENSIC DOCKET SPECIFICATION                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. HEADER SECTION                                                                      │
│    • Legal Registered Corporate Name                                                   │
│    • Companies House CRN (Direct Link to Beta Search)                                  │
│    • Registered Office Address & Geo-Coordinates                                       │
│                                                                                        │
│ 2. IMMIGRATION AUTHORITY PROFILE                                                       │
│    • Licence Reference Tier (Worker / Temporary Worker)                                │
│    • Current Rating: A-Rating (Ordinary) vs B-Rating (Action Plan Imposed)             │
│    • Longitudinal Licence Age: First seen date and uninterrupted tenure                │
│    • Approved Visa Categories (Skilled Worker, Scale-up, Senior Specialist Worker)     │
│                                                                                        │
│ 3. COMPANIES HOUSE CORPORATE AUTOPSY                                                   │
│    • Filing Health Indicator (Clean / Late Accounts / Pending Strike-Off / Liquidation)│
│    • Incorporation Date & Corporate Age                                                │
│    • Accounting Standard (Total Exemption Micro, Full Accounts, Dormant)               │
│    • Latest Accounts Date & Next Required Filing Deadline                              │
│    • Nature of Business (Standard Industrial Classification / SIC Codes)               │
│                                                                                        │
│ 4. RISK & VIABILITY APPRAISAL                                                          │
│    • Calculated Viability Warning Box (Rendered if solvency flags exist)               │
│    • Legal Impact Assessment: Warning to candidate regarding visa curtailment risks    │
│                                                                                        │
│ 5. ACTIONABLE NEXT STEPS                                                               │
│    • Primary Link: "Verify Official Companies House Public Filing ↗"                  │
│    • Secondary Link: "Search Active Job Openings for this Employer on LinkedIn ↗"      │
│    • Tertiary Link: "View Registered UK Insolvency Notices on The Gazette ↗"           │
└────────────────────────────────────────────────────────────────────────────────────────┘



```

## 6. Keyboard Ergonomics & Command Grammar

To meet the requirements of professional immigration case workers, recruiters, and power users, the platform implements a complete keyboard navigation grammar:

| **Key Binding** | **Scope** | **Action Executed** |
| `/` or `Ctrl+K` / `Cmd+K` | Global | Focuses and selects the main query omnibar. |
| `Escape` | Global | Clears search input; dismisses the Forensic Docket; resets focus. |
| `ArrowDown` or `J` | Data Table | Moves active selection down to the next sponsor in the register. |
| `ArrowUp` or `K` | Data Table | Moves active selection up to the previous sponsor. |
| `Enter` | Data Table | Expands the selected sponsor's full Forensic Docket in the side pane. |
| `S` | Data Table | Toggles the saved/shortlist status of the active highlighted row. |
| `E` | Data Table | Triggers an immediate CSV export of the current active query results. |
| `1` – `4` | Controls | Quick-switches between views: `[1] All`, `[2] Added`, `[3] Removed`, `[4] Flagged`. |

## 7. Implementation Execution Roadmap

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               PHASED EXECUTION ROADMAP                                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 🔹 PHASE 1: Data Pipeline Modernization (Build-Time Optimization)                      │
│    ├─ Create columnar binary serialization script (`scripts/pack_binary.py`)           │
│    ├─ Integrate official Companies House 5-digit SIC codes into entity matcher         │
│    └─ Reduce 11.4MB JSON down to 1.4MB Brotli-packed columnar array                    │
│                                                                                        │
│ 🔹 PHASE 2: Core Frontend Engine Overhaul                                              │
│    ├─ Build dedicated Web Worker search engine (`src/worker/query_engine.ts`)          │
│    ├─ Implement Bitset intersection filters and SIMD-accelerated string scan           │
│    └─ Build 120 FPS hardware-accelerated zero-allocation table virtualizer             │
│                                                                                        │
│ 🔹 PHASE 3: The Archival Gazette Design System                                         │
│    ├─ Implement typographic scale with `EB Garamond` and `IBM Plex Mono`               │
│    ├─ Construct split-pane layout: Master Ledger + Sticky Forensic Docket              │
│    ├─ Build Macro Solvency Ratio rule and Longitudinal Churn Matrix                    │
│    └─ Implement keyboard navigation engine (`J`/`K`/`Enter`/`/`)                       │
│                                                                                        │
│ 🔹 PHASE 4: Actionable Intelligence & Integration                                      │
│    ├─ Add Skilled Worker salary & SOC code threshold calculator                        │
│    ├─ Embed deep-links to Companies House, The Gazette, and live LinkedIn job searches │
│    └─ Deploy static release to GitHub Pages via automated GitHub Actions               │
└────────────────────────────────────────────────────────────────────────────────────────┘



```