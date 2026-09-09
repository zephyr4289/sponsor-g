The peak engineering answer is to **completely decouple data state persistence from the Git commit tree**.

Committing full snapshots to Git is an antipattern. Git is an append-only Directed Acyclic Graph (DAG) designed for source text diffs, not an object store for 11MB database dumps. If you commit full snapshots daily, your `.git/objects/pack` directory will choke on uncompressible hash variance.

Here is the zero-cost, zero-bloat architecture that eliminates the problem at the systems level.

---

### The Three-Tier Zero-Bloat Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DECOUPLED ZERO-COMMIT DATA PIPELINE                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  GitHub Actions Cron (06:00 UTC)                                                       │
│         │                                                                              │
│         ▼                                                                              │
│  [ Step 1: Ingest Upstream CSV ]                                                       │
│         │                                                                              │
│         ▼                                                                              │
│  [ Step 2: Fetch Yesterday's State via GitHub Release Asset (Out-of-Tree) ]            │
│         │  (GET api.github.com/.../releases/tags/state-v1/latest.bin)                  │
│         ▼                                                                              │
│  [ Step 3: Compute Daily Diff Engine ] ──────────────────────────────────────────────┐ │
│         │                                                                            │ │
│         ├──► Outputs Micro-Delta (302 Added, 242 Removed) ~20KB                      │ │
│         │    (Committed to Git: data/deltas/2026-W37.json)                           │ │
│         │                                                                            │ │
│         ├──► Clobbers Rolling Release Asset (Zero Git Bloat)                         │ │
│         │    (gh release upload state-v1 latest.bin --clobber)                       │ │
│         │                                                                            │ │
│         └──► Compiles Ephemeral Distribution Directory (/dist)                       │ │
│              - index.html                                                            │ │
│              - worker.js                                                             │ │
│              - data/sponsors.bin (Brotli Columnar ~780KB)                            │ │
│              - data/meta.json                                                        │ │
│                     │                                                                │ │
│                     ▼                                                                │ │
│  [ Step 4: Ephemeral Pages Deployment (No Commit to Main) ]                          │ │
│         │  (actions/upload-pages-artifact -> actions/deploy-pages)                   │ │
│         ▼                                                                              │
│  Live Production on GitHub Pages (github.io)                                          │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘

```

---

### 1. The Zero-Commit Deployment (Ephemeral Artifact Pipeline)

GitHub Pages does **not** require data to live in your `main` branch. Modern Pages deploys an uploaded artifact bundle (`actions/deploy-pages`).

* **How it works:** The GitHub Actions runner executes the ingestion script, downloads yesterday's reference, builds the site into a temporary `dist/` folder on the runner's NVMe drive, and hands `dist/` directly to the GitHub Pages deployment daemon.
* **The Result:** The live site receives the daily 127k dataset, but **exactly zero commits are added to `main**`. Your repository history remains pure code (<5MB total size forever).

---

### 2. Out-of-Band State Persistence (GitHub Release Asset Clobbering)

To compute daily additions, revocations, and rating changes, the daily runner must know what existed yesterday ($S_{\text{today}} \setminus S_{\text{yesterday}}$). Instead of checking this snapshot into Git:

* Use a persistent GitHub Release tag named `ledger-state` marked as `prerelease: true`.
* Releases store assets on GitHub's S3/Azure blob storage backing, completely outside Git's commit DAG.
* In the workflow, retrieve and update the state using the pre-authenticated GitHub CLI (`gh`):

```bash
# 1. Download yesterday's state into the runner
gh release download ledger-state -p "state_yesterday.bin" --output /tmp/yesterday.bin

# 2. Run diff engine against today's freshly fetched Home Office CSV
python scripts/diff_engine.py --yesterday /tmp/yesterday.bin --today /tmp/today.csv --out-dir ./dist/data

# 3. Overwrite yesterday's state with today's state in-place (Zero Git objects created)
gh release upload ledger-state /tmp/today.bin#state_yesterday.bin --clobber

```

The storage impact on your git repository is **zero bytes**.

---

### 3. Micro-Delta Git History (If Auditability is Required)

If you want public audit trails and Git provenance, **commit only the deltas, never the full snapshot**.

* The full database is 127,716 records (~11.4MB JSON).
* The daily turnover is only ~300 additions, ~240 revocations, and ~3 rating changes.
* Serializing solely the day's delta into `data/deltas/2026-09-10.json` generates a file of **~18KB**.

$$\text{Annual History Growth} = 18\text{ KB} \times 365 \approx 6.5\text{ MB / year}$$

A full decade of daily audits occupies less than 70MB of Git history, well within normal repository limits.

---

### 4. Binary Columnar Layout (Slashing Bandwidth from 11.4MB to 780KB)

Serving an 11.4MB JSON file to mobile clients is an unforced architectural bottleneck. Replacing raw JSON with a packed columnar binary layout drops payload size by 93% and eliminates browser JSON parsing overhead entirely.

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                    SPONSOR BINARY RECORD LAYOUT (10 BYTES / ROW)                     │
├──────────────────────────┬───────────┬───────────┬────────────┬───────────┬──────────┤
│ Name Arena Offset (u32)  │ Length(u8)│ TownID(u16│SectorID(u8)│Routes (u8)│Flags (u8)│
├──────────────────────────┼───────────┼───────────┼────────────┼───────────┼──────────┤
│ 4 Bytes                  │ 1 Byte    │ 2 Bytes   │ 1 Byte     │ 1 Byte    │ 1 Byte   │
└──────────────────────────┴───────────┴───────────┴────────────┴───────────┴──────────┘

```

* **Dictionary Encoded Fields:**
* **Town/City:** ~600 distinct UK localities. Encoded as a `uint16_t` dictionary index (2 bytes).
* **Industry/Sector:** 8 primary categories. Encoded as a `uint8_t` index (1 byte).
* **Visa Routes:** There are only 6 standard routes. Encoded as an 8-bit bitfield (`0b00000001` = Skilled Worker, `0b00000010` = Global Mobility, etc.) (1 byte).
* **Rating & Health Flags:** Rating (`A` vs `B`) + Status (`Active`, `Liquidation`, `Overdue`) packed into 1 byte.


* **String Arena:** All company names concatenated into a single contiguous UTF-8 byte buffer.
* **Payload Footprint:**
* Fixed table: $127,716 \times 10\text{ bytes} \approx 1.27\text{ MB}$.
* String arena: $\approx 1.80\text{ MB}$.
* Total uncompressed binary: **~3.07 MB** (down from 11.4 MB).
* **Brotli Compressed Wire Size:** **~780 KB**.



---

### Comparison of Architectural Tradeoffs

| Architecture Pattern | Daily Git Bloat | Monthly Growth | Client Payload Size | Compute Cost | Risk / Failure Mode |
| --- | --- | --- | --- | --- | --- |
| **Current (Naive Commit to Main)** | +11.4 MB / day | ~350 MB | 11.4 MB (Raw JSON) | $0.00 | Repo hits 1GB soft limit in 3 months; clones break. |
| **Orphan Branch Force-Push** | 0 MB (replaces head) | Variable | 11.4 MB | $0.00 | Remote `git gc` delays keep loose unreachable blobs. |
| **The Peak Engineering Solution** | **0.00 MB** | **0.00 MB** | **~780 KB** (Brotli Binary) | **$0.00** | **None.** Releases store state; Pages serves ephemeral binary artifact. |

---

### Implementation Workflow (`.github/workflows/sync_ledger.yml`)

```yaml
name: Sync Ledger & Deploy Ephemeral Artifact

on:
  schedule:
    - cron: '0 6 * * 1-5' # Mon-Fri 06:00 UTC
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  pipeline:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code Repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Build Tools
        run: pip install -r scripts/requirements.txt

      - name: Pull Previous Snapshot from Release Asset
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          mkdir -p /tmp/state
          gh release download state-anchor -p "previous_state.bin" --dir /tmp/state || touch /tmp/state/previous_state.bin

      - name: Execute Pipeline (Ingest, Diff, & Pack Binary)
        run: |
          python scripts/engine.py \
            --prev /tmp/state/previous_state.bin \
            --out-dist ./dist \
            --out-state /tmp/state/current_state.bin \
            --out-delta ./data/deltas

      - name: Update State Anchor in GitHub Releases (Zero Git Bloat)
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release upload state-anchor /tmp/state/current_state.bin#previous_state.bin --clobber

      - name: Commit Daily Micro-Delta Only (Optional Provenance)
        run: |
          git config user.name "ledger-bot"
          git config user.email "bot@users.noreply.github.com"
          if [ -d "./data/deltas" ] && [ -n "$(git status --porcelain ./data/deltas)" ]; then
            git add ./data/deltas/
            git commit -m "ledger(audit): delta $(date -u +'%Y-%m-%d')"
            git push origin main
          fi

      - name: Upload Static Pages Artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: './dist'

      - name: Publish to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4

```

This ensures complete automation, sub-megabyte transfers for clients, zero dollars spent, and zero repository bloating.
