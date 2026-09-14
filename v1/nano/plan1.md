Before proceeding, you need to address **three critical technical landmines** in that proposal. If you deploy it as written, the automation will either silently fail to publish or bloat the repository into gigabytes within months.

---

### Critical Traps to Address

**1. The `GITHUB_TOKEN` Push Recursion Trap**

* **The Problem:** If a GitHub Action commits and pushes code to `main` using the default `secrets.GITHUB_TOKEN`, **GitHub deliberately suppresses all downstream `on: push` workflows**. This is a hardcoded platform guardrail designed to prevent accidental infinite workflow loops.
* **The Consequence:** `daily_update.yml` will commit the new JSON files successfully, but `static.yml` **will not trigger**. The data in the repo will update, but the live site on `github.io` will stay frozen on the old build.
* **The Fix:** Do not split this into two workflows. Consolidate ingestion and deployment into a single unified workflow (`daily_sync_and_deploy.yml`) that runs the script, commits the diff, and calls `actions/deploy-pages` directly in step 2.

**2. The 11.4MB Daily Git History Explosion**

* **The Problem:** Git stores compressed packfile diffs. Committing an 11.4MB JSON file every single morning will bloat the hidden `.git/` directory by **~300MB–400MB every month** (over 4GB/year).
* **The Consequence:** Anyone cloning the repo (or future CI runners) will face massive checkout latencies, and GitHub may eventually flag the repository size (>1GB soft limit, 5GB hard limit).
* **The Fix:** Either keep the raw 127k database in a GitHub Release asset / orphan branch, or ensure the commit step checks if the Home Office CSV actually changed before touching git.

**3. Content-Hash / ETag Idempotency Guard**

* **The Reality:** The UK Home Office does not update the register every single calendar day (they often skip weekends and bank holidays).
* **The Fix:** Have the script inspect the HTTP `ETag` / `Last-Modified` header or compute the `SHA-256` of the downloaded CSV. If the hash matches yesterday's snapshot, the workflow should print `"No upstream change detected"` and terminate with exit code 0 without writing a ghost commit.

**4. Companies House Rate Limits**

* **The Reality:** The Home Office list is a single flat CSV download. Companies House, however, enforces strict API rate limits (600 requests per 5-minute window).
* **The Fix:** The script must not query the Companies House REST API for 127,000 entities inside GitHub Actions—the runner will hit 429 errors or exceed the 6-hour execution timeout. It should either parse the free Companies House monthly bulk CSV snapshot or run incremental diff checks strictly on newly added/modified companies.

---

### Clean Architecture Blueprint

Replace the disconnected commit-then-trigger model with a single atomic pipeline:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ UNIFIED DAILY SYNC & DEPLOY PIPELINE (.github/workflows/daily_sync.yml)                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [ Cron: 06:00 UTC ] ──► [ 1. Fetch Home Office CSV & Check SHA-256 ]                  │
│                                  │                                                     │
│                                  ├── Hashes Match ──► [ Exit 0 (No-Op) ]               │
│                                  │                                                     │
│                                  └── New Hash Detected                                 │
│                                         │                                              │
│                                         ▼                                              │
│                            [ 2. Compute Diffs & Flags ]                                │
│                            - new_sponsors.json (+302)                                  │
│                            - removed_sponsors.json (-242)                              │
│                            - rating_changes.json (A -> B)                              │
│                            - NMW sanction matches                                      │
│                                         │                                              │
│                                         ▼                                              │
│                            [ 3. Atomic Git Commit & Push ]                             │
│                            - Commit updated data/*.json                                │
│                                         │                                              │
│                                         ▼                                              │
│                            [ 4. Deploy Artifact to Pages ]                             │
│                            - actions/upload-pages-artifact                             │
│                            - actions/deploy-pages                                      │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘

```

---

### Proposed Workflow Implementation

```yaml
name: Daily Ledger Ingestion & Deployment

on:
  schedule:
    - cron: '0 6 * * 1-5'  # 06:00 UTC Monday through Friday
  workflow_dispatch:        # Manual back-up trigger

permissions:
  contents: write
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  ingest-and-publish:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Ingestion Dependencies
        run: pip install -r scripts/requirements.txt

      - name: Execute Ingestion Engine
        id: ingest
        run: |
          python scripts/daily_ingest.py
          # Output variable to determine if changes occurred
          if git diff --quiet data/; then
            echo "changed=false" >> $GITHUB_OUTPUT
          else
            echo "changed=true" >> $GITHUB_OUTPUT
          fi

      - name: Commit Updated Ledger Snapshots
        if: steps.ingest.outputs.changed == 'true'
        run: |
          git config user.name "sponsor-ledger-bot"
          git config user.email "bot@users.noreply.github.com"
          git add data/
          git commit -m "chore(data): ledger snapshot $(date -u +'%Y-%m-%d %H:%M UTC')"
          git push origin main

      - name: Upload Pages Artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4

```

With this consolidation, the runner handles data diffing, commits the delta back to the repo, and deploys the live site in one step—bypassing the `GITHUB_TOKEN` event suppression completely. Proceed with writing the ingestion script under this single-workflow pattern.
