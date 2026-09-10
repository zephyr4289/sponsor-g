Dropping the engineer hat, putting on the design one. The reframe first, because everything else falls out of it:

**You're not designing a terminal. You're designing a reassurance machine.**

Your user's psychological state: they're deciding whether to move their *life* across a border for an employer. High stakes, high anxiety, low trust — and they've probably seen the fake-sponsor-list scam industry, so their default assumption is that any site like yours could be part of it. They scan, they don't read. They're on a phone. Possibly in their second language.

Design north star: **calm authority** — a broadsheet of record, not a crime scene. Your current register ("forensic," "autopsy," walls of monospace) reads insider-cold and slightly threatening. Same gazette aesthetic family, warmer register: the *public ledger that exists to protect you*, not the analyst's dungeon.

**The emotional arc — design each stage on purpose:**

1. **Arrive (orientation):** Front page = curated "This Week's Ledger" — new licences, downgrades, flags. Curation is perceived competence: an alphabetical dump says "database," a front page says "editor of record." No newspaper opens with its index.
2. **Search (control):** Result count updating per keystroke, autosuggest. Perceived responsiveness *is* competence — every instant count is a micro-dose of "this thing works."
3. **Scan (verdict-seeking):** The flag dot must be fixation #1 on every row — pre-attentive, before they consciously read anything.
4. **Verdict (closure):** Two seconds in the docket, discussed below.
5. **Action (efficacy):** This is the missing stage. Fear appeals only persuade when people feel they can *act* — classic protection-motivation finding. Your flags supply the fear; the design must supply the plan: "Verify at source → Save → Share." Anxiety with no action path curdles into avoidance — and into blaming you.

**The docket should be an inverted pyramid — and you already own the metaphor:**

You're a gazette. So structure the docket like a news article:
- **Headline:** the verdict strip — Licence A ● Companies House: Active ● No NMW record ● Since 2019.
- **Lede:** four key facts.
- **Body:** evidence sections (what you have now).
- **Citations:** source chips per data point, external verify links.

Bonus move that's *thematically perfect* for you: an ink-stamp style verdict — **"ON REGISTER — NO ADVERSE RECORDS FOUND."** The word "found" does epistemic work (no record ≠ proof of health), and stamps psychologically trigger finality and officialdom. One caution: users *will* read any verdict as advice no matter your disclaimer — so word it as record-synthesis, never as recommendation ("no adverse records," not "safe to apply").

**Severity calibration — the psychology of warnings:**

- Red = statutory distress only (liquidation, administration). If 7% of the register is red, nothing is red — alarm fatigue destroys the signal. Exceptions must be the only loud things on screen (von Restorff).
- Never color alone: color + icon + word. Roughly 8% of male users have color vision deficiency, and your audience is heavily male and international.
- Represent uncertainty honestly: "No Companies House record located" ≠ "not checked." Systems that admit uncertainty are trusted *more*, not less.

**Row anatomy = perception order:** flag dot → name (strongest type) → town/sector (muted) → route/rating (compact badges). Rule: **ink proportional to information value.** "A - Rating" on 90% of rows deserves 10% of the visual weight.

**Stat band: aliveness = trust.**

- Dead stats kill it — "+0 net change" says *this register is a corpse*. Show "+12 / −12" pairs and sparklines: humans parse a trend shape pre-attentively, faster than any number.
- Kill false precision: 7.4%, not 7.43%. Over-precise numbers imply accuracy you don't have, and users can smell it.
- Tabular figures, right-aligned, deltas with direction arrows.
- One pulse on the "updated 06:00 UTC today" dot, then stop. Looping motion = low-grade anxiety; calm interfaces don't twitch.

**Numbers as anchors:** on the threshold gauge, show the *delta*, not just the bar — "£4,300 above the £38,700 floor." People reason about surpluses and shortfalls far better than absolutes.

**Motion rules:** 150–200ms, eased, and *causal* — the docket should grow out of the row the user tapped (object permanence: they never lose track of where they are). Respect `prefers-reduced-motion`.

**Mobile psychology:** search hero at top, primary actions in the thumb zone at the bottom, docket as a bottom sheet with the table still visible behind it — context preservation is what keeps anxious users oriented. Rows at 48–56px. And yes, the aesthetic-usability effect is real: your gazette identity is *already* doing trust work — polish isn't vanity, it's conversion.

**If you change only five things:**

1. Verdict strip + stamp on the docket (the peak moment — and per the peak-end rule, the last thing they see should be the action row).
2. Flag dots in table rows, leftmost.
3. Front page = "This Week's Ledger," not the alphabet.
4. Stat band: +X/−Y + sparkline, no dead numbers.
5. Mobile: search hero + bottom-sheet docket.

The one-liner: **your engine is forensic, but your user is scared — design the surface to be the calmest, most official-looking thing in their visa journey.**

Want me to spec one of these concretely — the verdict strip layout with tokens, or the front-page composition?
