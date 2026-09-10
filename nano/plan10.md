Speaking as the staff engineer who just had this land in my review queue — here's the honest pass. Good news first, because it's earned:

**Already right — don't touch:**
- Two-pane master/detail is the correct pattern for a data terminal.
- The telemetry band with live counts is a real differentiator.
- The gazette identity is memorable instead of being Inter-on-gray-dashboard #4,812.
- Keyboard grammar shows genuine respect for power users.

**P0 — trust breakers, and I found them in your own screenshots:**

1. **Your vocabulary drifts between views.** The same stat appears as "terminal distress" / "compliance defects" in one build, and "insolvency & administration warnings" / "filing warnings" in another. In a compliance product, label drift *reads as* data drift. Pick statutory-precise terms (also legally safer — "distress" is an editorial verdict; "Company status: Liquidation" is a fact), and use them identically in the masthead, summary, table, docket, and CSV headers. Dramatic names belong in marketing copy, never on data.

2. **Your headline stat went +302 → +17 between 00:47 and 11:23 the same day.** Either your rolling 7-day window logic is off, or you have two different metrics sharing one label — both are bugs. A stats tile is a promise; one broken screenshot costs more trust than all the polish you'll ever add.

3. **Every stat should be a door, not wallpaper.** "2,793 insolvency warnings" → click → filtered view. "Hospitality & Food −5" → click → that sector's removals. "+302 new" → quick view 2. Put live counts on the quick-view chips themselves ("Flagged 2,793"). Cheapest UX upgrade available in a data terminal.

4. **All five of your screenshots are from Android Brave.** That tells me your real user is on a phone. If the two-pane only works via "request desktop site," mobile is your actual P0: stacked layout, search as the hero element, docket becomes a bottom sheet, ≥44px tap targets, and visible buttons for save/export — the `S` and `E` keys don't exist on touch.

**P1 — the docket is your money screen:**

5. **Verdict first, evidence second.** The user's question is *"is this employer safe to trust?"* Answer it in two seconds with a synthesis strip — Licence A ● Companies House: Active ● No NMW record ● Licensed since 2019 — *then* let the sections support it. Right now the user has to assemble the verdict themselves from five sections.

6. **The SOC dropdown assumes users know SOC 2020 codes. They don't.** Make it a job-title typeahead ("software engineer" → 2134 → its going rate), defaulting to the employer's dominant occupation where known. Your salary calculator is the killer feature and it's gated behind a code only Home Office caseworkers memorize.

7. **Put the flags in the table rows.** A solvency/NMW colored dot per row. Your differentiator shouldn't be hidden behind clicks — if I have to open the docket to find the 2,793 distressed companies, the data is locked in a vault.

8. **Low-entropy columns.** "A - Rating" on ~90% of rows and "Skilled Worker" on most = the column carries almost no information. Collapse to compact badges and make B-ratings the *loud* exception. And if "Other" is your top industry, that column is mostly noise — fix the classifier or de-weight it.

9. **Fix the default view.** Landing on an alphabetical list starting at "A K SUPERSTORE" is a phone book. Land on search-focused + a "this week" digest (new, downgraded, flagged) as the hero — your changelog is your best content and it's currently your least prominent.

**P2 — quick wins:**

- Deep links: filtered view + selected row as a shareable URL, canonical per-employer URLs (also feeds your SEO pages).
- Net "±0" hides movement — show "+12 / −12" splits.
- Empty states that explain: "0 of 127,716 match" + one-click filter reset chips. In the docket, distinguish "no record" from "not checked".
- Freshness stamp on every data surface: "Home Office register as of 2026-09-10 06:00 UTC", stale banner if cache >24h.
- A11y: `role="grid"`, `aria-rowcount`, `aria-live` on result count, focus returns to the row on Escape.
- Sortable columns with visible state; "Showing 1–50 of 43,210".

**One-line summary for the PR review:** you've built a terminal that impresses engineers; now build the two seconds of verdict that serves the job seeker on a phone. Everything else is secondary to that.

Want me to take one of these to spec level — e.g., a concrete layout for the docket's synthesis strip, or the mobile master-detail flow?
