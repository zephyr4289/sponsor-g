Right — the actual brand mark. Let's do this properly, and I'm keeping every code block small per our verification protocol from last turn.

---

## Diagnosis: why the logo is ignorable

1. **Scale** — ~22px on a 390px viewport. It occupies <5% of the first screen. The telemetry band above it visually out-ranks the brand.
2. **No glyph** — text-only wordmarks have nothing to recognize at a glance, and nothing survives shrinking to favicon/PWA-icon size.
3. **One impression** — it scrolls away and never returns. During the core activity (scrolling the register), the brand is absent.
4. **An unused asset** — you already end the wordmark with a colored period. That's the seed of a real brand device, left un-planted.

---

## The core idea: the dot IS the logo

Your entire product is a **verdict machine** — compliant / flagged / liquidated. Your table rows already lead with status dots. Your masthead already ends in a period. So the brand mark isn't something to invent — it's the dot you already have, elevated into a system: **the dot that verifies**. One glyph connects masthead → status dots → favicon → PWA icon → loading state. That's brand-system thinking, not decoration.

---

## Three directions (stacked, not either/or)

### A — "The Verdict Dot" · typographic system
Fluid display scale for the wordmark, optical tracking, and the period replaced by an *engineered* dot (a real element, sized in `em`, not a text character — so it's consistent across every font-rendering path).

- Green dot (`#1D5837` — your Compliant token): the masthead itself states the product promise. **Recommended.**
- Carbon ink: the conservative choice, if green feels too "status-y" for a masthead.

Considered and rejected: stacking "Know / Your / Sponsor" across lines — bigger type, but it dissolves the camelCase wordmark. Don't.

### B — "The Ledger Seal" · the glyph
A ring-and-dot seal: **the register encircles the sponsor; the dot is the verdict.** It reads as a notary's chop — exactly right for a statutory ledger. Place it top-right of the masthead, slightly rotated like an ink stamp applied to a document. It avoids competing with the wordmark for line width on phones, and it's the composition with the most editorial character.

Same SVG doubles as favicon + maskable PWA icon (ring-and-dot centers perfectly in the maskable safe zone).

### C — "The Condensing Masthead" · behavioral presence
When the masthead scrolls out, a compact fixed bar slides in: 24px seal + 1rem wordmark + live register count. This is the FT/Bloomberg pattern — repeated brand impressions during scroll instead of one. Hold for L3 after A/B verify.

---

## Patch L1 — Verdict Dot wordmark (ship this now)

**HTML** — replace the literal period inside your `<h1>` (text node stays intact for SEO/screen readers):

```html
<h1>KnowYourSponsor<span class="dot" aria-hidden="true"></span></h1>
```

**CSS:**

```css
.masthead h1 {
  font-size: clamp(1.75rem, 9vw, 3.5rem);
  letter-spacing: -0.01em;
  line-height: 1.05;
}
.dot {
  display: inline-block;
  width: .14em;
  height: .14em;
  margin-left: .06em;
  border-radius: 50%;
  background: #1D5837;
}
```

Resulting scale: **~29px @ 320px → ~35px @ 390px → 56px cap on desktop.** That's a 60% mobile presence gain over the current masthead with zero layout risk (clamped, single line, `overflow-wrap` not needed on 16 chars at these sizes).

## Patch L2 — Ledger Seal (tiny, static, ship with L1)

```html
<svg class="seal" viewBox="0 0 48 48" aria-hidden="true" focusable="false">
  <circle cx="24" cy="24" r="20" fill="none" stroke="currentColor" stroke-width="2.5"/>
  <circle cx="24" cy="24" r="8" fill="#1D5837"/>
</svg>
```

```css
.masthead { position: relative; }
.seal {
  position: absolute;
  top: 6px;
  right: 0;
  width: 44px;
  height: 44px;
  color: var(--ink, #141311);
  transform: rotate(-6deg);
  opacity: .92;
}
```

`stroke="currentColor"` means dark mode is automatic — cream ink on slate. One check on your build: if the theme toggle lives inside the masthead's top-right rather than the nav row, nudge the seal to `top: 2px; right: 0` or drop it behind the h1 with `z-index`.

**Favicon:** save the same SVG as `favicon.svg` — at 16px, ring + dot stays legible. Optional flourish for dark OS themes: embed `<style>@media (prefers-color-scheme: dark){circle{stroke:#EDE9DF}}</style>` inside the favicon file (works in Chromium/Firefox). Then point `manifest.json` icons at 192/512 PNGs of the seal for the maskable check.

---

## L3 preview (after you verify L1/L2)

The condensing bar JS is ~12 lines (IntersectionObserver + one class toggle + safe-area padding) — per protocol, I hold it until you've run L1/L2 and pasted back a screenshot.

---

## Surface checklist (what makes it a *system*, not a header tweak)

- **Masthead:** dot + seal (L1/L2)
- **Status dots in table rows:** same green token — they're now literally the brand glyph at work
- **Favicon / PWA icon:** the seal
- **Loading state:** pulse the dot while the worker warms up ("the stamp being inked") — respects `prefers-reduced-motion`
- **og:image:** 1200×630 parchment card, wordmark + seal, mono strapline — this is what renders when the link is shared in WhatsApp/Reddit/job boards, likely your top acquisition surface

And one restraint note: no gradients, no shadows, no 3D on the mark. On an archival-gazette identity, **restraint is the flex** — authority comes from typography and the stamp metaphor, not effects.

Run L1+L2, screenshot me the masthead at 390px, and we'll do the condensing bar as the verified third move.
