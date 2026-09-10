### 1. Deterministic Entity Resolution State Machine

To eliminate false-linkage defamation risks, string similarity can no longer be treated as legal identity. Entity resolution must be modeled as a deterministic state machine with strict refusal capabilities.

```
                      [ Home Office Sponsor Record ]
                                    │
                                    ▼
                     [ 1. Exact CRN Cross-Index ]
                     (Known statutory register link)
                                    │
                     ├── MATCH ──► [ CONFIRMED_CRN (Conf: 1.0) ]
                     │
                     ▼ NO
                [ 2. Canonical Legal Name Match ]
            (Exact string after corporate suffix normalization)
                                    │
                     ├── MATCH ──► [ Check Postcode / Town Centroid ]
                     │                    │
                     │                    ├── VERIFIED ──► [ HIGH_CONFIDENCE_GEO (Conf: 0.95) ]
                     │                    │
                     │                    └── COLLISION ──► [ AMBIGUOUS_COLLISION (Conf: 0.0) ]
                     ▼ NO
              [ 3. Historical Name Alias Registry ]
           (Companies House Previous Names Database)
                                    │
                     ├── MATCH ──► [ HISTORICAL_ALIAS (Conf: 0.85) ]
                     │
                     ▼ NO
                 [ UNRESOLVED_SPONSOR (Conf: 0.0) ]

```

#### Core Invariant: The Negative-Assertion Airbag

Negative legal or financial flags (`IN_LIQUIDATION`, `ADMINISTRATION`, `PROPOSAL_TO_STRIKE_OFF`, `NMW_ENFORCEMENT`) **must never be bound to an entity** unless the match resolution confidence is strictly $\ge 0.95$ (`CONFIRMED_CRN` or `HIGH_CONFIDENCE_GEO`).

If an entity falls under `AMBIGUOUS_COLLISION` or `UNRESOLVED_SPONSOR`, corporate health tags are suppressed entirely, and the record renders purely with its verified Home Office attributes.

#### Schema: Linkage Provenance Object (`data/company_flags.json`)

Replace the raw status dictionary with an evidentiary record:

```typescript
interface ResolutionRecord {
  // Identity
  crn: string | null;
  match_state: "CONFIRMED_CRN" | "HIGH_CONFIDENCE_GEO" | "HISTORICAL_ALIAS" | "AMBIGUOUS_COLLISION" | "UNRESOLVED";
  match_confidence: number; // 1.0, 0.95, 0.85, or 0.0
  match_rule: string;       // e.g., "RULE_EXACT_NAME_AND_OUTCODE"
  
  // Corporate House Facts
  legal_name: string | null;
  corporate_status: "active" | "liquidation" | "administration" | "dissolved" | null;
  accounts_type: "total-exemption-full" | "dormant" | "micro-entity" | "overdue" | null;
  accounts_overdue: boolean;
  confirmation_statement_overdue: boolean;
  incorporation_date: string | null;
  sic_codes: string[];

  // Historical NMW Enforcement Facts
  nmw_enforcement: {
    named: boolean;
    publication_round: number | null; // e.g. 22
    published_date: string | null;     // e.g. "2025-10-17"
    arrears_period: string | null;     // e.g. "2017-2019"
    arrears_amount: number | null;
    workers_affected: number | null;
  } | null;

  // Provenance Audit Hash
  source_snapshot_date: string;       // e.g. "2026-09-01"
  resolution_timestamp: string;      // ISO UTC
}

```

---

### 2. Multi-Dataset Provenance & Bitemporal Cadence

The claim of a "daily updated corporate solvency ledger" fails because upstream datasets operate on desynchronized publication schedules. The system must expose a bitemporal model separating **Statutory Event Time (Valid Time)** from **Ingestion Observation Time**.

#### Per-Dataset Freshness Matrix (`data/meta.json`)

Update `meta.json` to expose source truth for every constituent dataset:

```json
{
  "schema_version": "2.0.0",
  "generated_at": "2026-09-10T06:00:14Z",
  "sources": {
    "home_office_register": {
      "source_published_at": "2026-09-09",
      "ingested_at": "2026-09-10T06:00:02Z",
      "cadence": "DAILY_BUSINESS_DAYS",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "row_count": 127716,
      "unique_legal_entities": 122840
    },
    "companies_house_bulk": {
      "source_snapshot_date": "2026-09-01",
      "ingested_at": "2026-09-02T12:00:00Z",
      "cadence": "MONTHLY_BULK",
      "sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
      "total_corpus": 5240182
    },
    "dbt_nmw_enforcement": {
      "naming_round": 22,
      "source_published_at": "2025-10-17",
      "ingested_at": "2025-10-18T00:00:00Z",
      "cadence": "IRREGULAR_ANNUAL"
    },
    "immigration_rules_thresholds": {
      "statutory_basis": "Statement of Changes in Immigration Rules (HC 590 / April 2024 - 2026 Update)",
      "effective_from": "2024-04-04",
      "baseline_floor": 41700,
      "lower_floor_new_entrant": 30960
    }
  },
  "metrics": {
    "total_registered_records": 127716,
    "resolved_entities": 104230,
    "unresolved_entities": 23486,
    "entities_in_formal_insolvency": 2793,
    "entities_with_overdue_filings": 6697
  }
}

```

#### The Solvency Ratio Denominator Fix

The frontend macro bar currently claims `91.0% SOLVENT`, masking unresolved records. The denominator must be mathematically explicit:

$$\text{Active \& Compliant Rate} = \frac{\text{Resolved Compliant Entities}}{\text{Total Resolved Entities}} = \frac{94,740}{104,230} = 90.9\%$$

The UI macro bar must visually render four discrete segments:

1. **Compliant Corporate Standing:** (74.2% of master register)
2. **Accounts / Statement Overdue:** (5.2% of master register)
3. **Formal Insolvency Proceedings:** (2.2% of master register)
4. **Unlinked / Ambiguous Resolution:** (18.4% of master register — *clearly tagged as unverified against Companies House*)

---

### 3. Regulatory Accuracy: Skilled Worker Salary Engine

The hardcoded £38,700 threshold is legally obsolete and must be updated to the current Home Office Immigration Rules.

#### Threshold Specification Matrix

| Category / Discount Option | Statutory Floor | Going Rate Minimum | Regulatory Anchor |
| --- | --- | --- | --- |
| **Standard Worker (Option A)** | **£41,700** | 100% of 50th percentile | General Skilled Worker Route |
| **STEM PhD Relevant to Job (Option B)** | **£37,530** | 80% of 50th percentile | Relevant Doctorate in Science/Tech |
| **Non-STEM PhD (Option C)** | **£37,530** | 90% of 50th percentile | Relevant Non-STEM Doctorate |
| **Immigration Salary List / ISL (Option D)** | **£30,960** | 100% of going rate (or floor) | Statutory Shortage Occupations |
| **New Entrant / Graduate Switcher (Option E)** | **£30,960** | 70% of 50th percentile | Under 26, Student/Graduate visa switchers |

#### Implementation Logic (`salary_calculator.js`)

```javascript
export function evaluateSalaryCompliance(socCodeData, candidateContext, offeredGrossSalary) {
  const { goingRate50th, eligibleForISL } = socCodeData;
  let statutoryFloor = 41700;
  let goingRateMultiplier = 1.0;

  switch (candidateContext.status) {
    case 'NEW_ENTRANT': // Student/Graduate switchers, age < 26
      statutoryFloor = 30960;
      goingRateMultiplier = 0.70;
      break;
    case 'STEM_PHD':
      statutoryFloor = 37530;
      goingRateMultiplier = 0.80;
      break;
    case 'ISL_SHORTAGE':
      if (!eligibleForISL) throw new Error("SOC code not eligible for ISL discount");
      statutoryFloor = 30960;
      goingRateMultiplier = 1.0;
      break;
    case 'STANDARD':
    default:
      statutoryFloor = 41700;
      goingRateMultiplier = 1.0;
      break;
  }

  const effectiveGoingRate = Math.round(goingRate50th * goingRateMultiplier);
  const requiredThreshold = Math.max(statutoryFloor, effectiveGoingRate);
  const passesSalaryCheck = offeredGrossSalary >= requiredThreshold;

  return {
    passesSalaryCheck,
    requiredThreshold,
    statutoryFloor,
    effectiveGoingRate,
    delta: offeredGrossSalary - requiredThreshold,
    regulatoryDisclaimer: "Meets statutory minimum salary condition under Immigration Rules. This calculation assesses salary feasibility only and does not establish visa eligibility (e.g. English language, ATAS, financial maintenance, or genuine vacancy rules)."
  };
}

```

---

### 4. Legal Protection, Audit Chains & Dispute Workflows

Publishing negative corporate health signals (e.g., liquidation, strike-off, HMRC minimum wage sanctions) requires a strict evidentiary audit trail to prevent commercial libel liabilities.

#### 1. Evidentiary Dossier Header (The Transparency Block)

Every employer view and programmatic SEO subpage must output an immutable provenance declaration:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STATUTORY AUDIT & PROVENANCE NOTICE                                                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Entity Matching: CONFIRMED_CRN (Company #01470151)                                     │
│ Sources Cross-Referenced:                                                              │
│ - UK Home Office Register of Licensed Sponsors (Snapshot: 09 Sep 2026)                 │
│ - Companies House Statutory Filing Register (Snapshot: 01 Sep 2026)                    │
│ Disclaimer: This ledger is an algorithmic collation of official public records. It     │
│ does not constitute legal, immigration, or financial advice.                           │
│ Record ID: 01470151:2026W37:v2.0                                                       │
└────────────────────────────────────────────────────────────────────────────────────────┘

```

#### 2. Statutory Right of Rectification & Correction Engine

Add an explicit dispute link on every company card:
`[ Notice a data discrepancy or recent corporate change? Submit formal rectification notice ]`

This links directly to a GitHub-backed or mailto-based structured ingestion format:

```
To: compliance-corrections@knowyoursponsor.co.uk (or dedicated GitHub Issue)
Subject: Data Rectification Request: [Company Name] (CRN: [00000000])

Required Verification Data:
1. Companies House CRN:
2. Home Office Sponsor Licence Reference (if known):
3. Nature of Correction: [ ] Name Change  [ ] Incorrect Entity Linkage  [ ] Updated Accounts
4. Statutory Evidence Link (e.g., Companies House WebFiling confirmation, London Gazette notice):

```

#### 3. Strict Semiotic Vocabulary

Strip colloquial or inflammatory language across the entire frontend and SEO metadata:

* Replace `"INSOLVENCY WARNINGS"` with `"STATUTORY INSOLVENCY FILINGS"`.
* Replace `"Stopped trading"` with `"Formal insolvency proceedings or strike-off action initiated"`.
* Replace `"NMW Underpaid"` with `"Named in DBT Enforcement Round [X] (Historical)"`.

---

### 5. Verified Latency & Hot-Path Memory Specification

To substantiate performance claims without marketing hyperbole:

#### 1. Formal Definition of Zero-Allocation

Update documentation to claim: **"Zero heap allocation in the hot rendering cycle."**

* The virtualized DOM table recycles a fixed pool of 50 `<tr>` DOM nodes via absolute coordinate translation (`transform: translateY`).
* Scrolling mutations only update `element.textContent` and `element.className`.
* No new HTML string allocations, innerHTML parsing, or object allocations occur on scroll.

#### 2. Benchmark Reproduction Script (`benchmarks/latency_audit.js`)

Provide a synthetic benchmark suite executed across 1,000 randomized queries on 127,716 records:

```javascript
// Telemetry harness to measure P50, P95, P99 across the Web Worker search channel
export async function runSearchLatencyBenchmark(worker, iterations = 1000) {
  const testQueries = ["tech", "care", "consulting", "london", "manchester", "ltd", "06365302", "soft"];
  const latencies = [];

  for (let i = 0; i < iterations; i++) {
    const q = testQueries[i % testQueries.length];
    const t0 = performance.now();
    
    await new Promise((resolve) => {
      const channel = new MessageChannel();
      channel.port1.onmessage = () => resolve();
      worker.postMessage({ type: "BENCHMARK_QUERY", payload: { q } }, [channel.port2]);
    });
    
    latencies.push(performance.now() - t0);
  }

  latencies.sort((a, b) => a - b);
  return {
    p50: latencies[Math.floor(iterations * 0.50)].toFixed(2) + " ms",
    p95: latencies[Math.floor(iterations * 0.95)].toFixed(2) + " ms",
    p99: latencies[Math.floor(iterations * 0.99)].toFixed(2) + " ms",
    max: latencies[latencies.length - 1].toFixed(2) + " ms",
  };
}

```

---

### Execution Roadmap

1. **Step 1: Regulatory Patch**
Update `soc_thresholds.json` baseline from £38,700 to £41,700, and embed the 5-option statutory discount calculation logic into the detail sheet.
2. **Step 2: Evidentiary Schemas**
Update the Python ingestion pipeline to output the `match_state` confidence score and explicit dataset timestamps into `meta.json`.
3. **Step 3: Terminology & Denominator Refactor**
Align the macro ratio bar and UI copy with statutory legal terminology, rendering unlinked entities as a distinct analytical category.
4. **Step 4: Dispute Linkage**
Insert the rectification and provenance blocks into both the interactive SPA drawer and the static pSEO templates.
