Screenshot triage first, because two things landed and two things went sideways:

**Landed:** the wordmark scale + green dot — that's a real masthead now. Good.
**Sideways #1:** the seal fell out of the masthead and is sitting in the **nav row** next to "Changes" — it reads like a stray radio button, not a brand mark. My absolute positioning lost the fight with your DOM; we'll fix with flex, not absolutes.
**Sideways #2:** that rotating green script ("Solve"…) — agreed, kill it. And here's the *why*, because it matters for everything we do next:

> It's a cursive font cycling through words with a perpetual pen animation. Three identity violations at once: wrong register (wedding-invitation script on a statutory gazette), wrong behavior (motion that never resolves — the eye re-reads it every cycle), wrong hierarchy (it sits at the same optical weight as the wordmark, so the brand competes with an annotation).

The creative principle for a mark like yours: **one mark, one moment.** Craft lives in the mark itself, and motion is spent once — on load — like ink, not repeated like a screensaver. Here are the three treatments, in ship order.

---

## Patch M1 — Remove the rotator

Search `index.html` for the word list (look for "Solve" or a JS array cycling strings — likely a `.rotator` / `.typewriter` span). Delete the element and its script/CSS. Don't replace it with anything — the masthead's job is authority, and silence is authority. The tagline underneath already does the explanatory work.

---

## Patch M2 — The Inked Seal (the signature move)

Same ring-and-dot, but rendered as a **stamped chop**: ink-bleed texture via SVG turbulence, slight rotation, and a one-time press on load — like the register just got notarized. This is the creativity you're asking for, and it's *of* the product: a stamp on a document.

**SVG** (replace the current seal — the filter is the whole trick):

```html
<svg class="seal" viewBox="0 0 48 48" aria-hidden="true">
  <defs>
    <filter id="ink">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2"/>
      <feDisplacementMap in="SourceGraphic" scale="1.8"/>
    </filter>
  </defs>
  <g filter="url(#ink)">
    <circle cx="24" cy="24" r="20" fill="none" stroke="currentColor" stroke-width="2.5"/>
    <circle cx="24" cy="24" r="8" fill="#1D5837"/>
  </g>
</svg>
```

**CSS** — flex placement (fixes the nav-row escape) + the stamp press:

```css
.masthead { display: flex; align-items: flex-start; gap: 12px; }
.masthead .brand { flex: 1; min-width: 0; }
.seal {
  flex: none;
  width: clamp(38px, 11vw, 54px);
  margin-top: 4px;
  transform: rotate(-8deg);
  animation: stamp .5s cubic-bezier(.2,.8,.3,1) .35s both;
}
@keyframes stamp {
  0%   { transform: rotate(-8deg) scale(1.7); opacity: 0; }
  65%  { transform: rotate(-8deg) scale(.94); opacity: 1; }
  100% { transform: rotate(-8deg) scale(1);   opacity: .92; }
}
@media (prefers-reduced-motion: reduce) { .seal { animation: none; } }
```

The press happens once, 500ms after load, then it's a static stamp for the rest of the session. **One caveat:** keep the favicon/PWA icon as the *clean* ring-and-dot — `feTurbulence` noise doesn't survive 16px, it turns to mud. Texture is for the masthead render only.

---

## Patch M3 — The Ledger Rule (the tasteful pen stroke)

You don't hate pen strokes — you hate a pen that never stops writing. So: a hand-ruled hairline under the wordmark that **draws itself once** and then simply *is* a rule line, the way a clerk rules an entry in a ledger. Ends at the dot. No cursive font anywhere.

**HTML** (directly after the `<h1>`, inside `.brand`):

```html
<svg class="rule" viewBox="0 0 300 8" preserveAspectRatio="none" aria-hidden="true">
  <path d="M2 6 C 80 3.5, 220 3.5, 296 5" pathLength="1"
        fill="none" stroke="#1D5837" stroke-width="1.5"/>
</svg>
```

**CSS:**

```css
.rule { display: block; width: min(100%, 340px); height: 8px; margin-top: 2px; }
.rule path {
  stroke-dasharray: 1;
  stroke-dashoffset: 1;
  animation: draw .7s ease-out .55s forwards;
}
@keyframes draw { to { stroke-dashoffset: 0; } }
@media (prefers-reduced-motion: reduce) { .rule path { stroke-dashoffset: 0; animation: none; } }
```

The slight curve in the path (`C 80 3.5…`) is what reads as "ruled by hand" — 2px of imperfection, which is exactly the amount a real pen gives you. Sequence check: dot is part of h1, rule draws beneath it, seal presses beside it. Three one-time inks, then stillness.

---

## Patch M4 — The Living Dot (behavioral brand, my favorite)

Make the dot mean something. It already mirrors your row status dots — now tie it to the register itself:

- **On load:** one soft pulse (the register "checking in").
- **On daily sync:** when your worker/meta layer detects the snapshot date changed, the dot pulses again. Every morning at 06:00 UTC, the masthead marks the new issue — users learn "when the dot beats, the register moved."

```css
.dot.pulse { animation: beat .9s ease-out 2; }
@keyframes beat {
  0%   { box-shadow: 0 0 0 0 rgba(29,88,55,.45); }
  100% { box-shadow: 0 0 0 12px rgba(29,88,55,0); }
}
```

```js
const dot = document.querySelector('.masthead .dot');
dot.classList.add('pulse');
dot.addEventListener('animationend', () => dot.classList.remove('pulse'), { once: true });
// later: when your meta.json poll reports a new snapshot date, re-add .pulse
```

That's a brand behavior no competitor has — the logo is literally an indicator of statutory freshness. Cost: ~10 lines.

---

## Verify before the next patch

1. M1: rotator gone — grep for "Solve"/the word array, confirm zero hits.
2. M2: seal sits **right of the wordmark**, top-aligned, rotated, stamped once. Not in the nav row.
3. M3: rule draws once under the wordmark; after 1.5s the header is fully static.
4. Dark mode: seal stroke should follow `currentColor` (cream ink on slate); the dot stays green.
5. Reduced motion: no stamp, no draw — everything appears in final state.

Ship M1→M4 in that order (M1 first — everything else composes better without the rotator fighting for attention). Screenshot me the masthead at 390px again and, if it's clean, next move is the condensing scroll bar — seal + wordmark + live count in a fixed 48px bar — which is where this brand system starts paying rent during scroll.
