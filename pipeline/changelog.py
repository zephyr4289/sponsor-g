"""
Generates /changes/ - who gained and who lost a licence, by region.

This is the page the whole project exists to be able to publish. GOV.UK
publishes today's register and never what left it, so an employer losing its
licence is invisible in the official data the moment it happens. Because the
pipeline keeps a dated snapshot every day, we can show it.

It does three jobs at once:

- Answers a search nobody else answers ("new UK visa sponsors this week").
- Gives regional anchors, so a single region can be linked directly in an
  email to the people who work on that region.
- Emits data/regional_changes.json, the machine-readable version, so a weekly
  per-region email can be sent without anyone assembling it by hand.

Stdlib only. Static HTML, no JavaScript needed to read the numbers.
"""

import html
import json
from collections import defaultdict

import pages
from pages import GOATCOUNTER, SITE, slugify

I_NAME, I_TOWN, I_COUNTY, I_INDUSTRY, I_ROUTES, I_RATING = range(6)

# Regions shown as their own section. Beyond this the tail is grouped into
# one "elsewhere" block rather than a long list of one-employer headings.
TOP_REGIONS = 12
UNKNOWN_REGION = "Location not given"


def group_by_region(rows, limit=TOP_REGIONS):
    """Group employers by town, biggest first, with a tail bucket.

    Returns (regions, tail) where regions is [(town, rows)] and tail is the
    flat list of everything below the cut.
    """
    buckets = defaultdict(list)
    for row in rows:
        buckets[(row[I_TOWN] or "").strip() or UNKNOWN_REGION].append(row)

    ordered = sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0].lower()))
    for _, group in ordered:
        group.sort(key=lambda r: str(r[I_NAME]).lower())

    kept = ordered[:limit]
    tail = [row for _, group in ordered[limit:] for row in group]
    tail.sort(key=lambda r: str(r[I_NAME]).lower())
    return kept, tail


def regional_feed(added, removed, updated="", window_days=7):
    """The machine-readable per-region breakdown.

    This is what a weekly send reads, so a region's email can be assembled
    without a person deciding what goes in it.
    """
    regions = defaultdict(lambda: {"added": [], "removed": []})
    for row in added:
        regions[(row[I_TOWN] or "").strip() or UNKNOWN_REGION]["added"].append(row)
    for row in removed:
        regions[(row[I_TOWN] or "").strip() or UNKNOWN_REGION]["removed"].append(row)

    return {
        "updated": updated,
        "window_days": window_days,
        "totals": {"added": len(added), "removed": len(removed)},
        "regions": {
            name: {
                "added": sorted(v["added"], key=lambda r: str(r[I_NAME]).lower()),
                "removed": sorted(v["removed"], key=lambda r: str(r[I_NAME]).lower()),
                "slug": slugify(name),
            }
            for name, v in sorted(regions.items(),
                                  key=lambda kv: (-len(kv[1]["added"])
                                                  - len(kv[1]["removed"]),
                                                  kv[0].lower()))
        },
    }


def _table(rows, kind):
    """One region's employers. Routes are shown for additions only: for a
    removed employer they describe what it could do before, which would read
    as though it still can."""
    esc = html.escape
    body = []
    for row in rows:
        location = ", ".join(p for p in (row[I_TOWN], row[I_COUNTY]) if p)
        last = (f"<td>{esc(', '.join(row[I_ROUTES]))}</td>" if kind == "added"
                else "")
        body.append(f"<tr><td>{esc(str(row[I_NAME]))}</td>"
                    f"<td>{esc(location)}</td>"
                    f"<td>{esc(row[I_INDUSTRY])}</td>{last}</tr>")
    head = ("<th>Employer</th><th>Location</th><th>Industry</th>"
            + ("<th>Visa routes</th>" if kind == "added" else ""))
    return (f"<table><thead><tr>{head}</tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table>")


def _section(rows, kind, heading, blurb, empty):
    esc = html.escape
    if not rows:
        return (f'<section class="block"><h2>{esc(heading)}</h2>'
                f'<p class="sub">{esc(empty)}</p></section>')

    regions, tail = group_by_region(rows)
    parts = [f'<section class="block"><h2>{esc(heading)} ({len(rows)})</h2>',
             f'<p class="sub">{esc(blurb)}</p>']

    if len(regions) > 1:
        links = " ".join(
            f'<a href="#{kind}-{slugify(name)}">{esc(name)} ({len(group)})</a>'
            for name, group in regions)
        parts.append(f'<p class="jump"><strong>Jump to:</strong> {links}</p>')

    for name, group in regions:
        parts.append(f'<h3 id="{kind}-{slugify(name)}">{esc(name)} '
                     f'<span class="n">{len(group)}</span></h3>')
        parts.append(_table(group, kind))

    if tail:
        parts.append(f'<h3 id="{kind}-elsewhere">Elsewhere '
                     f'<span class="n">{len(tail)}</span></h3>')
        parts.append(_table(tail, kind))

    parts.append("</section>")
    return "\n".join(parts)


def render(added, removed, updated="", window_days=7):
    esc = html.escape
    title = "UK visa sponsors added and removed"
    desc = (f"{len(added)} employers gained a licence to sponsor UK work visas "
            f"in the last {window_days} days and {len(removed)} lost one. "
            f"Rebuilt daily from the official GOV.UK register.")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} | SponsorSignal</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}/changes/">
<meta property="og:type" content="article">
<meta property="og:url" content="{SITE}/changes/">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="../favicon.png" type="image/png">
<link rel="alternate" type="application/rss+xml" title="Sponsor changes" href="../feed.xml">
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;800&display=swap" rel="stylesheet">
<style>
{pages.THEME_CSS}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Public Sans',system-ui,sans-serif;color:var(--ink);
       line-height:1.55;background:var(--paper)}}
  .wrap{{max-width:960px;margin:0 auto;padding:0 20px}}
  a{{color:var(--cobalt)}}
  header{{border-bottom:3px solid var(--ink);padding:14px 0}}
  .brand{{font-weight:800;font-size:1.1rem}}
  .brand a{{color:inherit;text-decoration:none}}
  .brand .dot{{color:var(--cobalt)}}
  h1{{font-size:clamp(1.6rem,4.5vw,2.4rem);font-weight:800;letter-spacing:-0.02em;
     margin:36px 0 10px;text-wrap:balance;max-width:20ch}}
  .lead{{color:var(--ink-soft);max-width:62ch;text-wrap:pretty}}
  .updated{{margin-top:8px;font-size:.85rem;color:var(--ink-soft)}}
  .tiles{{display:grid;gap:12px;margin:28px 0;
         grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}}
  .tile{{border:1.5px solid var(--line);border-radius:10px;padding:14px 16px}}
  .tile.warn{{border-color:#E7B4AE;background:#FBE3E1}}
  .tile .label{{display:block;font-size:.82rem;color:var(--ink-soft)}}
  .tile .value{{display:block;font-size:1.9rem;font-weight:600;
               letter-spacing:-0.02em;margin-top:2px}}
  section.block{{margin:52px 0}}
  h2{{font-size:1.3rem;font-weight:800;letter-spacing:-0.01em;text-wrap:balance}}
  h3{{font-size:1rem;margin:26px 0 8px;padding-bottom:4px;
     border-bottom:2px solid var(--ink)}}
  h3 .n{{color:var(--ink-soft);font-weight:400;font-variant-numeric:tabular-nums}}
  .sub{{color:var(--ink-soft);font-size:.92rem;margin-top:6px;max-width:64ch;
       text-wrap:pretty}}
  .jump{{margin-top:14px;font-size:.88rem;color:var(--ink-soft)}}
  .jump a{{margin-right:10px;white-space:nowrap}}
  table{{width:100%;border-collapse:collapse;font-size:.93rem;margin-top:6px}}
  th{{text-align:left;font-size:.78rem;color:var(--ink-soft);
     border-bottom:1px solid var(--line);padding:6px 8px}}
  td{{padding:8px;border-bottom:1px solid var(--line);vertical-align:top}}
  tbody tr:hover{{background:var(--paper-dim)}}
  .cta{{margin:56px 0;border:2px solid var(--ink);border-radius:10px;
       background:var(--paper-dim);padding:24px}}
  .cta p{{color:var(--ink-soft);margin-top:6px;max-width:52ch;text-wrap:pretty}}
  .cta a.btn{{display:inline-block;margin-top:14px;background:var(--cobalt);
             color:#fff;text-decoration:none;font-weight:600;padding:11px 22px;
             border-radius:8px}}
  :is(a,button):focus-visible{{outline:3px solid var(--cobalt);outline-offset:2px}}
  footer{{margin-top:48px;border-top:3px solid var(--ink);padding:22px 0 40px;
         font-size:.85rem;color:var(--ink-soft)}}
  footer p+p{{margin-top:6px}}
  {pages.HEADER_CSS}{pages.THEME_TOGGLE_CSS}
  @media (max-width:640px){{
    th:nth-child(4),td:nth-child(4){{display:none}}
  }}
</style>
{pages.THEME_BOOT}
</head>
<body>
{pages.site_header('changes')}

<main class="wrap">
  <h1>{esc(title)}</h1>
  <p class="lead">The official register shows who can sponsor a visa today. It
     does not show what changed. This page does, because we keep a copy of the
     register every day.</p>
  <p class="updated">Covering the last {window_days} days{
      f", updated {esc(updated)}" if updated else ""}.</p>

  <div class="tiles">
    <div class="tile"><span class="label">Newly licensed</span>
      <span class="value">{len(added):,}</span></div>
    <div class="tile warn"><span class="label">Lost their licence</span>
      <span class="value">{len(removed):,}</span></div>
  </div>

  {_section(added, "added", "Newly licensed employers",
            "These employers can sponsor a work visa for the first time in "
            "this period. Fewer applicants know they exist yet.",
            "No employers gained a licence in this period. The register does "
            "not change every day.")}

  {_section(removed, "removed", "Employers that lost their licence",
            "These were on the register recently and have since been removed. "
            "They cannot sponsor a visa now, so an application to them for "
            "sponsored work is unlikely to lead anywhere.",
            "No employer lost their licence in this period. That is good news "
            "for anyone job hunting right now.")}

  <section class="cta">
    <h2>Get this each week</h2>
    <p>One email a week with the employers that gained and lost a licence. No
       need to check back.</p>
    <a class="btn" href="../#alerts">Get the weekly email</a>
    <p style="margin-top:12px">Prefer no email? There is an
       <a href="../feed.xml">RSS feed</a>, and the
       <a href="../data-api/">raw data</a> if you would rather build on it.</p>
  </section>
</main>

<footer><div class="wrap">
  <p>Built on the official GOV.UK Register of Licensed Sponsors (Workers).
     SponsorSignal is an independent search tool built on open public data. It
     is not affiliated with the Home Office and is not immigration advice.</p>
  <p>Always confirm an employer's current status on the official register
     before making decisions. <a href="../">Search the full list</a>.</p>
</div></footer>
<script data-goatcounter="{GOATCOUNTER}" async src="//gc.zgo.at/count.js"></script>
{pages.THEME_SCRIPT}
</body>
</html>
"""


def write(root, added, removed, updated="", window_days=7):
    """Write changes/index.html and the machine-readable regional feed."""
    directory = root / "changes"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "index.html").write_text(
        render(added, removed, updated, window_days), encoding="utf-8")

    feed = regional_feed(added, removed, updated, window_days)
    (root / "data" / "regional_changes.json").write_text(
        json.dumps(feed, separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8")
    return feed
