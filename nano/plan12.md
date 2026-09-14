Alright, putting on the staff engineer hat. I went over both screenshots like a bug triage. The good news: your **design language is fine** — the gazette identity survives mobile well. What's broken is **composition**: the desktop layout is being *shrunk* instead of *re-composed*, and there are genuine overflow bugs. Let's fix it properly.

---

## 1. Defect Audit

| # | Defect | Evidence | Sev |
|---|--------|----------|-----|
| 1 | **CTA row clipped** — "Shortli…" cut mid-word | Sheet action buttons | P0 |
| 2 | **Verdict banner text clipped** — "Companies Hous…" runs past viewport edge | Status banner | P0 |
| 3 | **Stray "A-R" chip clipped** top-right of banner, colliding with title | Sheet banner | P0 |
| 4 | **Salary segments clipped** — "New Ent…" unreachable | SOC threshold widget | P0 |
| 5 | **Quick-view tabs clipped** — "Flagged (9…" | Filter tabs | P0 |
| 6 | **Preset chips clipped** — "Healthcare & C…" | Presets row | P0 |
| 7 | **Keyboard hints band overlapping/clipped** ("…ied J/K Navigate") and useless on touch | Above table | P0 |
| 8 | **Table = horizontal-scroll data grid** with wildly inconsistent row heights (the GBM routes row is 3× taller) | Register | P1 |
| 9 | Telemetry band wraps to 3 lines, eats ~15% of viewport | Header | P1 |
| 10 | Legend 4-across → each item wraps to 3 lines | Stats | P1 |
| 11 | Sheet title oversized, leading `.` data artifact (".LITTLE NOORIYAH LTD") | Sheet | P2 |
| 12 | Tap targets ~36–40px on chips/tabs (HIG minimum: 44px) | Global | P2 |
| 13 | iOS focus-zoom risk (input font size) | Search / SOC input | P2 |

**Root cause (all six P0 clipping bugs are the same bug):** fixed flex rows with no `min-width: 0` discipline, no overflow strategy, and desktop affordances (keyboard hints, Export CSV, wide tables) shipped to touch devices. Fix the *system*, not six spots.

---

## 2. The Build

> Rename selectors to your actual classnames — I'm writing against plausible structure since I don't have `index.html`.

### A. Global guards — kills the overflow class of bugs at the root

```css
/* ============ MOBILE ENGINEERING LAYER ============ */
:root {
  --tap: 44px;            /* minimum interactive target */
  --rail-fade: 28px;      /* scroll-rail edge fade */
  --bp: 720px;            /* stacked-layout breakpoint */
}

html, body {
  overflow-x: clip;                 /* nothing may ever widen the page */
  -webkit-text-size-adjust: 100%;
}

/* flex/grid children may shrink below content size — this is the
   #1 fix for clipped rows. Apply to every flex container. */
.sheet-actions, .banner, .tabs, .presets, .search-row,
.filters, .stat-row, .seg {
  min-width: 0;
}

/* long statutory names must wrap, never clip */
.sheet-title, .banner-body {
  overflow-wrap: anywhere;
}
```

Also grep your CSS for `100vw` and replace with `100%` / `100dvh` — `100vw` includes the scrollbar and is a classic silent overflow source.

### B. Scroll-rail utility — one pattern for tabs, presets, chips, salary segments

Anything that *can* overflow becomes a momentum rail with an edge fade so users **see** there's more:

```css
.rail {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scroll-snap-type: x proximity;
  scrollbar-width: none;
  padding-bottom: 2px;
  mask-image: linear-gradient(to right, #000 0, #000 calc(100% - var(--rail-fade)), transparent);
}
.rail::-webkit-scrollbar { display: none; }
.rail.is-end { mask-image: none; }          /* fade only when more content exists */
.rail > * {
  flex: 0 0 auto;
  scroll-snap-align: start;
  min-height: var(--tap);
}
```

```js
// Edge-fade affordance: fade dies exactly when the rail runs out.
function railify(rail) {
  const update = () => {
    const max = rail.scrollWidth - rail.clientWidth - 1;
    rail.classList.toggle('is-end', rail.scrollLeft >= max);
  };
  rail.addEventListener('scroll', update, { passive: true });
  new ResizeObserver(update).observe(rail);
  update();
}
document.querySelectorAll('.rail').forEach(railify);
```

**Apply `.rail` to:** quick-view tabs, presets row, banner chip row, salary segment tabs. This single utility clears defects #1, #4, #5, #6. For the banner chips, honestly `flex-wrap: wrap` is even better (chips are few) — wrap is fine there:

```css
.banner-chips { display: flex; flex-wrap: wrap; gap: 6px; }
```

And that stray clipped "A-R" badge: it's absolutely positioned against the banner title. On mobile, delete the absolute positioning and fold it into the chip row. One source of truth.

### C. Register table → dossier cards (the big mobile win)

A horizontally-scrolling data table on a phone is the anti-pattern. Under 720px, re-map the same DOM into a card using `grid-template-areas` — **no HTML changes**, virtualizer-safe:

```css
@media (max-width: 720px) {
  .tbl-head { display: none; }   /* cards are self-labelling */

  .row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    grid-template-areas:
      "name   rating"
      "meta   meta"
      "routes routes";
    row-gap: 6px;
    padding: 14px 16px;
    touch-action: manipulation;
  }
  .cell--name    { grid-area: name;   font-size: 1.05rem; }
  .cell--rating  { grid-area: rating; justify-self: end; }
  .cell--town,
  .cell--industry{ grid-area: meta; }        /* merge into one mono meta line */
  .cell--routes  { grid-area: routes; display: flex; flex-wrap: wrap; gap: 6px; }
}
```

Mobile reading order becomes: **Name → rating chip → town · industry → route chips**. That's a dossier listing — it actually *strengthens* the gazette metaphor (each row reads like a classified entry) instead of fighting it.

⚠️ **Integration risk — flag this in review:** your virtual pool positions rows via transforms against a computed row height. Card rows are ~104–116px, desktop rows ~44px, and they now vary per-row. You must:

```js
const mq = matchMedia('(max-width: 720px)');

function rowHeightFor(item) {
  if (!mq.matches) return DESKTOP_ROW_H;
  const routeLines = Math.ceil(item.routes.length / 2);   // chips wrap ~2 per line
  return 64 + routeLines * 30;                            // tune once
}

mq.addEventListener('change', () => {
  rebuildMeasurements();          // recompute total height + re-pool rows
});
```

If per-row measurement is too invasive, a fixed mobile height of `112px` with a single-line route clamp (`max 2 chips + "+n"`) is an acceptable v1. Do **not** ship mixed heights without telling the pool — that's how you get overlapping transforms.

### D. Bottom sheet rebuild — snap points, sticky CTAs, safe areas

Your sheet is currently a full-screen takeover with a decorative handle. Make it a real sheet: **peek shows the verdict, drag to read the docket** (Google Maps pattern — users get the answer without losing list context).

```css
.sheet {
  position: fixed;
  inset: auto 0 0 0;
  height: 94dvh;                          /* dvh, not vh — Android URL bar */
  transform: translateY(100dvh);
  transition: transform .34s cubic-bezier(.32,.72,.24,1);
  border-radius: var(--sheet-radius) var(--sheet-radius) 0 0;
  overscroll-behavior: contain;           /* inner scroll must not chain to page */
  will-change: transform;
  z-index: 50;
}

.sheet-grip {
  touch-action: none;                     /* handle owns its gestures */
  padding: 12px 0 8px;                    /* generous grab area */
  cursor: grab;
}

.sheet-body {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

/* CTA bar: sticky, wraps instead of clips. Fixes defect #1 forever. */
.sheet-actions {
  position: sticky;
  bottom: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  background: linear-gradient(to top, var(--paper) 72%, transparent);
}
.sheet-actions .cta--primary { grid-column: 1 / -1; }   /* GOV.UK full-width */

.sheet-title { font-size: clamp(1.35rem, 6vw, 1.9rem); }
```

```js
// Pointer-driven drag with flick physics. Reuse your existing Escape/close path.
(() => {
  const sheet = document.querySelector('.sheet');
  const grip  = sheet.querySelector('.sheet-grip');
  const SNAPS = [0.42, 0.94];                     // peek, full
  let y0 = 0, top0 = 0, lastY = 0, lastT = 0, vel = 0, on = false;
  const vh = () => visualViewport?.height ?? innerHeight;

  const snapTo = f => {
    sheet.style.transition = 'transform .34s cubic-bezier(.32,.72,.24,1)';
    sheet.style.transform = `translateY(${(1 - f) * 100}dvh)`;
    sheet.dataset.state = f > 0.7 ? 'full' : 'peek';
  };

  grip.addEventListener('pointerdown', e => {
    on = true; y0 = lastY = e.clientY;
    top0 = sheet.getBoundingClientRect().top;
    lastT = performance.now();
    grip.setPointerCapture(e.pointerId);
    sheet.style.transition = 'none';
  });
  grip.addEventListener('pointermove', e => {
    if (!on) return;
    const t = performance.now();
    vel = (e.clientY - lastY) / Math.max(1, t - lastT);   // px/ms
    lastY = e.clientY; lastT = t;
    const dy = Math.max(0, e.clientY - y0);               // no overdrag past full
    sheet.style.transform = `translateY(${top0 + dy}px)`;
  });
  grip.addEventListener('pointerup', () => {
    on = false;
    const shown = 1 - sheet.getBoundingClientRect().top / vh();
    let target = SNAPS.reduce((a, b) =>
      Math.abs(b - shown) < Math.abs(a - shown) ? b : a);
    if (vel >  0.5) target = SNAPS[Math.max(0, SNAPS.indexOf(target) - 1)]; // flick down
    if (vel < -0.5) target = SNAPS[Math.min(SNAPS.length - 1, SNAPS.indexOf(target) + 1)];
    if (target === SNAPS[0] && vel > 0.5) closeSheet();   // flick from peek = dismiss
    else snapTo(target);
  });
})();
```

A11y contract (non-negotiable): `role="dialog"`, `aria-modal="true"`, focus moves into the sheet on open, returns to the triggering row on close, scrim tap-to-dismiss, body scroll locked while open.

### E. Header & density

```css
/* Telemetry: one scrollable ticker line instead of three wrapped lines */
.telemetry {
  white-space: nowrap;
  overflow-x: auto;
  scrollbar-width: none;
  font-size: 0.72rem;
}

/* Keyboard grammar is a desktop feature. On touch it's noise + it's
   glitching (defect #7). Kill it. */
@media (pointer: coarse) { .kbd-hints { display: none; } }

/* Legend: 4-cramped columns → 2×2 */
@media (max-width: 720px) {
  .legend { grid-template-columns: 1fr 1fr; gap: 10px 16px; }
}

/* Give the search room: Export becomes icon-only on mobile */
@media (max-width: 720px) {
  .export-btn .label { display: none; }
  .export-btn { padding-inline: 14px; }
}
.search-row input { font-size: 16px; }   /* prevents iOS focus zoom — keep 16px+ */
```

Stat numerals: `font-size: clamp(1.8rem, 8vw, 2.6rem)` — fluid, no media query needed.

### F. Platform specifics (the last 5% that reads as "peak")

```html
<meta name="viewport"
      content="width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content">
```

- `viewport-fit=cover` + `env(safe-area-inset-bottom)` → you're a PWA (`manifest.json`), so in standalone mode the home-indicator will otherwise sit on your UI.
- `interactive-widget=resizes-content` → when the keyboard opens over the sheet's SOC job-title input, the sheet resizes instead of the keyboard covering it. You have an input at the bottom of the sheet — you need this.
- Update `<meta name="theme-color">` in both light/dark via `media` attributes so the browser chrome matches parchment/slate.

---

## 3. Rollout Order

1. **PR-1 (hotfix):** Global guards (§A) + `.rail` (§B) + wrap banner chips + hide `.kbd-hints` on coarse pointers. ~80 lines, clears all six P0 clipping defects. Ship today.
2. **PR-2:** Card rows (§C) + virtualizer height sync. Needs the most careful testing.
3. **PR-3:** Sheet rebuild (§D).
4. **PR-4:** Header density + platform meta (§E/§F) + tap-target pass (`min-height: var(--tap)` on all chips/tabs/selects).

**QA matrix before each merge:** 360×740 (Pixel), 375×667 (iPhone SE), landscape, dark mode, PWA standalone, keyboard-open-over-sheet-input. Assertion: `document.documentElement.scrollWidth <= window.innerWidth` on every route — make it a console assert in dev so regressions fail loudly.

Two data-side notes I spotted while in there: the leading `.` in the sheet title — trim it in the render layer (`name.replace(/^[.\s·-]+/, '')`), display only, don't touch source data. And the sheet shows **£41.7k** standard threshold while your README still says £38,700 — the app looks updated, the README copy is stale. Worth a one-line PR.

Want me to do a pass on the tablet breakpoint (768–1024 is usually where sheet + card + rail hybrids either sing or fall apart), or draft PR-1 as a complete drop-in diff?
