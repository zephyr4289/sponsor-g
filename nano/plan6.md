### Mobile Viewport Diagnostic

```
┌───────────────────────────────────────────────────────────┐  ▲
│ UK REGISTER OF LICENSED SPONSORS...                       │  │
│ KNOWYOURSPONSOR.  UK VISA SPONSOR...                      │  │
│ Changes Numbers Data API For Business [☾]                 │  │ 100% OF MOBILE VIEWPORT
├───────────────────────────────────────────────────────────┤  │ CONSUMED BY CHROME & STATS
│ TOTAL LICENSED ENTITIES : 127,716                         │  │
│ WEEKLY ADDITIONS (+7D)  : +17                             │  │ (0 DATA ROWS VISIBLE)
│ INSOLVENCY WARNINGS     : 2,793                           │  │
│ FILING WARNINGS         : 6,697                           │  │
├───────────────────────────────────────────────────────────┤  │
│ CORPORATE FILING RATIO  : 91.0% / 6.8% / 2.2%             │  │
├───────────────────────────────────────────────────────────┤  │
│ [ Q Search by employer... [/] ] [ Export CSV ]            │  ▼
└───────────────────────────────────────────────────────────┘

```

The mobile breakpoint suffers from five structural layout failures:

1. **Complete Above-the-Fold Data Starvation:** The 4 metric cards collapsed from a horizontal desktop band into a single vertical column. Combined with the masthead, nav links, and solvency ratio, **100% of the mobile viewport is consumed by metadata**. The user cannot see a single row of data without scrolling past 650 vertical pixels.
2. **Desktop Shortcut Leaks on Touch Screens:** The `/` keyboard shortcut badge is rendered inside the search input. Mobile touch devices do not have physical keyboard shortcuts; it wastes input field width.
3. **Cramped Omnibar & Clipped Placeholders:** Placing `Export CSV` on the same flex row as the search input on a 360–390px viewport clips the placeholder text (`"Search by employer name,"`). Furthermore, CSV downloads are an edge case on mobile phones compared to searching.
4. **Redundant Captioning:** Captions like `"Home Office worker tier"` and `"Liquidation, strike-off, or administration"` take up three lines per metric card. On mobile screens, these must be compressed.
5. **Multi-Row Nav Wrap:** The navigation links (`Changes`, `Numbers`, `Data API`, `For Business`, theme toggle) form an awkward second horizontal row under the masthead, adding another 40px of vertical dead space.

---

### Target Mobile Viewport Budget (< 260px Total Header)

On a standard 390×844 viewport (iPhone / Android baseline), the entire header, telemetry, and search controls must fit within **260px**, leaving **at least 3 to 4 table rows visible immediately on load**.

```
┌───────────────────────────────────────────────────────────┐ 0px
│ THE REGISTER · ISSUE W37                 127.7k ENTITIES  │ 24px
│ KNOWYOURSPONSOR.                         [Changes] [☾]    │ 56px
├─────────────────────────────┬─────────────────────────────┤
│ 127,716 TOTAL               │ +17 NEW (7D)                │
│ 2,793 INSOLVENT             │ 6,697 OVERDUE               │ 120px
├─────────────────────────────┴─────────────────────────────┤
│ [████████████████████████████████████████████░░░░░░░░░░░] │
│ 91.0% SOLVENT · 6.8% OVERDUE · 2.2% DISTRESSED            │ 155px
├───────────────────────────────────────────────────────────┤
│ [ 🔍 Filter 127,716 sponsors...                         ] │ 205px
├───────────────────────────────────────────────────────────┤
│ [ All ] [ Added (17) ] [ Flagged (9.5k) ] [ ★ (0) ]       │ 245px
├───────────────────────────────────────────────────────────┤ 260px  ▲
│ A & A Mobile Ltd            Pontypridd         ● ACTIVE   │        │ FIRST ROWS
│ A & A RETAIL & PO LTD       Sutton             ▲ OVERDUE  │        │ VISIBLE
│ A & B Cabs Ltd              Leicester          ■ INSOLV.  │        │ ABOVE FOLD
└───────────────────────────────────────────────────────────┘        ▼

```

---

### The Production Responsive CSS Specification

Apply these targeted media query overrides for `@media (max-width: 640px)`.

#### 1. Compress Metric Band into a Compact 2×2 Micro-Grid

Replace the vertical stack with a fixed 2-column, dense grid. Strip description subtitles on mobile screens:

```css
@media (max-width: 640px) {
  /* 2x2 Grid instead of stacked vertical blocks */
  .ledger-band {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 0 !important;
    margin-bottom: 12px !important;
    border-top: 1px solid var(--rule) !important;
    border-bottom: 1px solid var(--rule) !important;
  }

  .ledger-cell {
    padding: 8px 10px !important;
    border-right: 1px solid var(--rule) !important;
    border-bottom: 1px solid var(--rule) !important;
  }
  .ledger-cell:nth-child(2n) {
    border-right: none !important;
  }
  .ledger-cell:nth-child(3),
  .ledger-cell:nth-child(4) {
    border-bottom: none !important;
  }

  .ledger-label {
    font-size: 9px !important;
    margin-bottom: 2px !important;
  }

  .ledger-metric {
    font-size: 18px !important;
    line-height: 1.1 !important;
  }

  /* Hide verbose subtext on mobile */
  .ledger-sub {
    display: none !important;
  }
}

```

#### 2. Streamline Masthead & Navigation

Collapse secondary links and shrink vertical padding:

```css
@media (max-width: 640px) {
  body {
    padding: 12px 14px !important;
  }

  header {
    margin-bottom: 12px !important;
    padding-bottom: 8px !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 6px !important;
  }

  .masthead-title {
    font-size: 24px !important;
    letter-spacing: 0.08em !important;
  }

  /* Hide long descriptive right-hand column in masthead */
  .masthead-desc, 
  .masthead-meta-long {
    display: none !important;
  }

  /* Compact top utility bar */
  .nav-links {
    display: flex !important;
    width: 100% !important;
    justify-content: space-between !important;
    font-size: 11px !important;
  }
  
  /* Hide non-critical marketing links on mobile header */
  .nav-links a:not([data-critical="true"]) {
    display: none !important;
  }
}

```

#### 3. Full-Width Search Omnibar (Relocate Export CSV & Hide Desktop Shortcut)

Give 100% of horizontal real estate to the search input:

```css
@media (max-width: 640px) {
  .search-container {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    margin-bottom: 12px !important;
  }

  .search-input-wrapper {
    width: 100% !important;
  }

  /* Hide desktop keyboard shortcut badge */
  .search-kbd-shortcut,
  .search-input-wrapper kbd {
    display: none !important;
  }

  /* Move Export CSV out of the primary line or style as icon */
  .btn-export-csv {
    display: none !important; /* Move to table footer or dock */
  }

  .search-input {
    font-size: 14px !important; /* Prevents iOS auto-zoom on focus (<16px can zoom, or use 16px font-size) */
    padding: 8px 12px !important;
  }
}

```

#### 4. Macro Ratio Bar Optimization

Remove the multi-line legend on small screens and replace with a single tabular summary line:

```css
@media (max-width: 640px) {
  .ratio-container {
    margin-bottom: 12px !important;
  }

  .ratio-bar {
    height: 3px !important;
    margin-bottom: 4px !important;
  }

  /* Transform legend to a single horizontal line */
  .ratio-legend {
    display: flex !important;
    justify-content: space-between !important;
    font-size: 9px !important;
    gap: 0 !important;
  }

  .ratio-legend-item span {
    font-size: 9px !important;
  }
  
  .ratio-dot {
    display: none !important;
  }
}

```

#### 5. Horizontal Scrolling Filter Tabs

Ensure filter pills scroll horizontally without line breaks:

```css
@media (max-width: 640px) {
  .filter-tabs {
    display: flex !important;
    overflow-x: auto !important;
    white-space: nowrap !important;
    -webkit-overflow-scrolling: touch !important;
    scrollbar-width: none !important;
    padding-bottom: 4px !important;
  }
  
  .filter-tabs::-webkit-scrollbar {
    display: none !important;
  }

  .filter-tab {
    flex: 0 0 auto !important;
    padding: 6px 10px !important;
    font-size: 11px !important;
  }
}

```

---

### Implementation Verification Checklist

* [ ] **First Paint Metric:** At least 3 sponsor records visible without user interaction on a 390×844 viewport.
* [ ] **Font Size Threshold:** Search input font size set to at least `16px` on mobile (or scaled via meta viewport) to prevent Safari iOS from triggering automatic viewport zoom on input tap.
* [ ] **Touch Target Integrity:** All filter tabs maintain at least a `36px` touch-height tap area despite compact typography.
* [ ] **Clean Input Surface:** Zero text overflow or ellipsis clipping inside the primary search box.
