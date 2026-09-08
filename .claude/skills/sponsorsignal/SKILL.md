---
name: sponsorsignal
description: Operating brief for SponsorSignal — the mission, revenue thesis, quality bar and current priorities. Load this at the start of any session on this project, and before deciding what to build next, changing user-facing copy or design, touching the data pipeline, or discussing traffic, pricing or monetisation.
---

# SponsorSignal — operating brief

A live site at https://roshan1208.github.io/sponsorsignal/ that lets anyone
search the official UK register of employers licensed to sponsor work visas.
Static files on GitHub Pages, refreshed daily by a GitHub Actions job. No
server, no database, no running costs.

## What this is for

Someone job hunting in the UK on a visa can only work for an employer holding
a sponsor licence. That is roughly 127,000 employers out of about 5 million.
Every application sent to the other 98% is wasted effort, and most applicants
find that out too late. The Home Office publishes the list, but as a raw
multi-megabyte CSV with no search, no industries, and no way to see what
changed.

We make that list usable. Someone should be able to land on the site and know,
within seconds, which employers near them can sponsor a visa.

**The order is: accurate, then useful, then loved, then paid.**

Never trade a place down that list for a place higher up. This sits next to
someone's immigration status and livelihood. Wrong data costs a real person a
real job application, and once trust is gone the business is gone with it. If
a change would make money but degrade accuracy or clarity, do not make it.

## The honest strategic picture

Read this before proposing anything. Two facts drive every decision:

**The data is not a moat.** It is free, public, and anyone can rebuild the
pipeline in a weekend. Competing sites already exist. Being a nicer search box
over public data is not a durable business by itself.

**The change history is the moat.** GOV.UK publishes only the current state of
the register. It does not publish what changed. Every daily commit is a dated
snapshot, so the repo is quietly accumulating a time series that cannot be
reconstructed after the fact: who was newly licensed, who lost their licence,
which sectors are growing. In a year this is a dataset nobody else has.

Two consequences, and they are not optional:

- Start capturing changes properly **now**. Every day not captured is gone
  forever. This is why the new/removed sponsor work outranks cosmetic work.
- Never rewrite git history on this repo, and never let the pipeline commit
  data it has not sanity-checked. The history *is* the asset.

**Who actually pays.** The job seeker is the user, not the customer. They are
by definition short of money and leave the moment they get a visa. Recruiters,
immigration advisers and relocation firms have budgets, renew, and want exactly
what we uniquely hold: change feeds, exports, filtered alerts. Serve job
seekers free forever — they are the traffic, the SEO and the credibility — and
sell to the people who profit from them.

Details, pricing and sequencing: `references/revenue.md`.

## End goal

Income that arrives without weekly manual work. That means the whole loop —
fetch, validate, publish, notify, bill — runs unattended, and a human only
steps in when something is genuinely wrong.

This is realistic but not fast. Expect SEO to take months to compound. Do not
propose schemes that trade the long game for a spike, and do not tell the user
this will be quick.

Anything added must be judged on: *does this still work if nobody touches it
for a month?* If the answer is no, it needs a guard rail or it does not ship.

## Current state

*Last checked against the repo: 6 September 2026. Verify before trusting it;
this section goes stale faster than anything else in the brief.*

- Live, ~127,661 employers. `.github/workflows/refresh.yml` is scheduled at
  05:30 UTC but GitHub delays free-tier cron, so it lands nearer 09:00-10:00.
  That is normal, not a fault.
- **24 pages:** the homepage, `/changes/`, `/insights/`, `/data-api/`, and 20
  generated landing pages (8 industries, 12 cities). Plus `feed.xml`, sitemap,
  OG image, installable PWA. **191 passing tests.**
- `index.html` is the whole site. The pipeline is `pipeline/`: `refresh.py`
  (data), `changes.py` (history), `pages.py` (landing pages), `changelog.py`
  (`/changes/` and the regional feed), `insights.py`, `feed.py`, `datadocs.py`.
- **The change history is real and growing:** 242 added and 155 removed over
  the first six days. Zero-change days line up with bank holidays and
  weekends, when GOV.UK does not publish, so a zero is not a failure.

**Known gaps, in priority order.**

1. **Nobody has been told this exists.** Traffic is effectively zero and the
   list has one subscriber. Everything below is downstream of fixing that.
   The outreach playbook is in `outreach/` (gitignored, local only), and
   sending is the user's job, not ours.
2. **Nobody is sending the newsletter.** `data/digest.md` and
   `data/regional_changes.json` are generated daily and MailerLite holds the
   list, but no send happens. Prove the content by hand once, then automate.
3. **The automated weekly send is blocked** on whether MailerLite API access
   is on the user's plan. RSS-to-email is the paid-plan alternative;
   `feed.xml` already exists to feed it either way.
4. **Alert scope is unverified.** The form sends `fields[city]` and
   `fields[industry]`, and MailerLite's tags look right, but nobody has
   confirmed a real signup stores them. MailerLite accepts unknown fields
   silently, so a mismatch would lose data without any error.
5. **The classifier still leaves 56% as "Other".** Mostly names with no
   signal, so this is near the ceiling for guessing from a name. Improving it
   further has poor returns.

Done, so do not rebuild: email capture, analytics on every page, Search
Console and sitemap, the publish guard, additions **and** removals tracking
plus the `/changes/` page that shows them, CSV export, scoped alert signup,
the city filter, the header nav, `/insights/`, `feed.xml` and `/data-api/`.

## What to do next

Each step unlocks the next. Do not skip ahead.

1. **Get the first ten emails sent** (user's job, see `outreach/`). Ten
   replies teach more about pricing and features than any amount of building.
2. **Automate the weekly send** once the MailerLite plan question is answered.
   That closes the loop and is the last piece of the passive-income machine.
3. **Weekly archive pages** (`/changes/2026-W36/`), so each week becomes a
   permanent URL. The only feature that grows more valuable purely with time.
4. **Only then, charge.** A paid tier before there is a list, a history and
   traffic is premature.

Resist adding features while traffic is zero. A feature nobody sees is not
progress, and the honest bottleneck is distribution, not the product.

## Decision rights

Own the work. Do not ask permission for ordinary decisions — make the call,
say what you chose and why, and move on.

**Decide without asking:** code, copy, layout, UX, data modelling, SEO
structure, refactors, tests, what to build next from the priority list.

**Ask first:**
- Anything that spends money or signs the user up to a paid service.
- Anything published to an audience: posting to Reddit, LinkedIn or X,
  emailing the list, submitting to directories. Drafting is fine; sending is
  the user's call.
- Pricing, and how the site positions itself legally.
- Rewriting git history, force-pushing, or anything that risks the snapshots.
- Adding a backend, a framework, a build step or a paid dependency.

Flag honestly when something will not work, including when the user asks for
it. Saying "this looks good" about a thin idea costs them real money.

## Constraints

These come from the user and are not up for renegotiation without asking:

- No build step, no framework, no backend. `index.html` is the whole site.
- The pipeline is Python standard library only.
- Keep the existing visual design. Improve within it.
- One task per commit, message written for a human reading it in a year.
- Never commit secrets. Never commit generated `__pycache__`.

## Quality bar

Non-negotiable, because a confusing free tool never becomes a paid one.

- Fast to something useful. Never a bare spinner: say what is loading.
- No empty state that looks broken. If a feature has nothing to show, say why.
- Mobile first. Most people searching for visa sponsorship are on a phone.
- Real focus states, working keyboard navigation, sensible ARIA.
- Keep the disclaimers. This is a search tool, not immigration advice.

Full checklist: `references/quality.md`.

## Writing rules

The copy must read as if a person wrote it. Plain words, short sentences, no
padding. Do not join two clauses with an em dash — write two sentences. Do not
hedge, apologise or explain the implementation to the visitor. Say "employers",
not "organisations" or "companies" (much of the register is councils, NHS
trusts, schools and charities).

This applies to the site, the landing pages, the newsletter, and anything
written for the user's audience. Full rules and worked examples:
`references/copy.md`.

## Growth and engagement

How to get people here and keep them: `references/growth.md`.

## Start of a session

Do these checks before proposing work, and lead with anything that is broken:

1. Is the site up, and how fresh is the data?
   `curl -s https://roshan1208.github.io/sponsorsignal/data/meta.json`
2. Did the last scheduled run pass?
   `https://api.github.com/repos/roshan1208/sponsorsignal/actions/runs?per_page=3`
3. Is the working tree clean and in sync with `origin/main`?
4. Do the tests pass? `python -m unittest discover -s pipeline`
5. Have the gaps above been closed since this was written?

Then say plainly what is worth doing next and start. Do not present a menu of
options when one of them is clearly right.
