"""
Generates /data-api/ - documentation for the published JSON files.

The pipeline already writes clean JSON on a fixed schedule. Documenting it
turns a by-product into something a recruiter or an adviser can build on,
and it is a far stronger thing to offer in an email than a link to a search
box: they can poll it from whatever they already use, with no account and no
integration call.

It is deliberately described as published files rather than an API. There is
no authentication, no rate limit and no uptime promise beyond GitHub Pages,
and saying otherwise would be selling something that does not exist.

Stdlib only.
"""

import html

import pages
from pages import GOATCOUNTER, SITE

# Each entry: path, what it holds, and the shape, described honestly.
ENDPOINTS = [
    {
        "path": "data/sponsors.json",
        "what": "Every licensed sponsor on the register.",
        "shape": '{"updated": "...", "source": "...", "sponsors": [[name, town, county, industry, [routes], rating], ...]}',
        "note": "About 10MB uncompressed, served gzipped. Rows are arrays, "
                "not objects, to keep it small.",
    },
    {
        "path": "data/changes.json",
        "what": "Dated additions and removals, 90 days of history.",
        "shape": '{"updated": "...", "days": [{"date": "YYYY-MM-DD", "added": [row, ...], "removed": [row, ...]}, ...]}',
        "note": "The part you cannot rebuild from GOV.UK. The official "
                "register publishes only the current state.",
    },
    {
        "path": "data/regional_changes.json",
        "what": "The same changes, split by town or city.",
        "shape": '{"updated": "...", "window_days": 7, "totals": {...}, "regions": {"London": {"added": [...], "removed": [...], "slug": "london"}, ...}}',
        "note": "Built for exactly one job: sending someone the changes in "
                "their own area.",
    },
    {
        "path": "data/new_sponsors.json",
        "what": "Employers licensed in the last 7 days.",
        "shape": '{"updated": "...", "window_days": 7, "new": [row, ...]}',
        "note": "",
    },
    {
        "path": "data/removed_sponsors.json",
        "what": "Employers removed in the last 7 days.",
        "shape": '{"updated": "...", "window_days": 7, "removed": [row, ...]}',
        "note": "",
    },
    {
        "path": "data/meta.json",
        "what": "Counts and the last update time. Small, cheap to poll.",
        "shape": '{"updated": "...", "total": 0, "added_recently": 0, "removed_recently": 0, "window_days": 7}',
        "note": "Poll this first and only fetch the big files when "
                "\"updated\" has moved.",
    },
    {
        "path": "feed.xml",
        "what": "RSS feed, one item per day that changed.",
        "shape": "RSS 2.0",
        "note": "For readers, and for anything that turns a feed into email.",
    },
]


def render(meta=None):
    esc = html.escape
    meta = meta or {}
    title = "The data behind SponsorSignal"
    desc = ("Published JSON files of the UK register of licensed visa "
            "sponsors, including daily additions and removals. Free to use, "
            "no account needed.")

    rows = []
    for e in ENDPOINTS:
        note = f'<p class="note">{esc(e["note"])}</p>' if e["note"] else ""
        rows.append(f"""    <div class="endpoint">
      <p class="path"><a href="../{esc(e['path'])}">{esc(e['path'])}</a></p>
      <p class="what">{esc(e['what'])}</p>
      <pre><code>{esc(e['shape'])}</code></pre>
      {note}
    </div>""")

    total = f"{meta.get('total', 0):,}" if meta.get("total") else "127,000+"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} | SponsorSignal</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}/data-api/">
<meta property="og:type" content="article">
<meta property="og:url" content="{SITE}/data-api/">
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
  .wrap{{max-width:820px;margin:0 auto;padding:0 20px}}
  a{{color:var(--cobalt)}}
  header{{border-bottom:3px solid var(--ink);padding:14px 0}}
  .brand{{font-weight:800;font-size:1.1rem}}
  .brand a{{color:inherit;text-decoration:none}}
  .brand .dot{{color:var(--cobalt)}}
  {pages.HEADER_CSS}{pages.THEME_TOGGLE_CSS}
  h1{{font-size:clamp(1.6rem,4.5vw,2.3rem);font-weight:800;
     letter-spacing:-0.02em;margin:36px 0 10px;text-wrap:balance;max-width:20ch}}
  .lead{{color:var(--ink-soft);max-width:64ch;text-wrap:pretty}}
  h2{{font-size:1.2rem;font-weight:800;margin:44px 0 8px;text-wrap:balance}}
  p{{max-width:64ch;text-wrap:pretty}}
  p+p{{margin-top:10px}}
  .endpoint{{border:1.5px solid var(--line);border-radius:10px;
            padding:16px 18px;margin-top:14px}}
  .path{{font-weight:600;font-size:1rem}}
  .what{{color:var(--ink-soft);margin-top:2px}}
  pre{{margin-top:10px;background:var(--paper-dim);border-radius:8px;
      padding:12px 14px;overflow-x:auto}}
  code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
       font-size:.82rem;color:var(--ink)}}
  .note{{margin-top:10px;font-size:.9rem;color:var(--ink-soft)}}
  ul{{margin:10px 0 0 20px;color:var(--ink-soft);max-width:64ch}}
  li+li{{margin-top:6px}}
  .cta{{margin:48px 0;border:2px solid var(--ink);border-radius:10px;
       background:var(--paper-dim);padding:22px}}
  .cta p{{color:var(--ink-soft);margin-top:6px}}
  :is(a,button):focus-visible{{outline:3px solid var(--cobalt);outline-offset:2px}}
  footer{{margin-top:48px;border-top:3px solid var(--ink);padding:22px 0 40px;
         font-size:.85rem;color:var(--ink-soft)}}
  footer p+p{{margin-top:6px}}
</style>
{pages.THEME_BOOT}
</head>
<body>
{pages.site_header()}

<main class="wrap">
  <h1>{esc(title)}</h1>
  <p class="lead">Everything this site shows is published as plain JSON,
     rebuilt every day from the official GOV.UK register. It is free to use,
     needs no account, and you are welcome to build on it.</p>

  <h2>Start here</h2>
  <p>If you only want one thing, it is <a href="../data/regional_changes.json">
     <code>regional_changes.json</code></a>: the employers that gained or lost
     a licence in the last seven days, split by town. That is the part the
     official register does not publish, because it shows only who holds a
     licence today and never who stopped.</p>
  <p>There is also an <a href="../feed.xml">RSS feed</a> if you would rather
     not write any code at all.</p>

  <h2>The files</h2>
{chr(10).join(rows)}

  <h2>How to use it kindly</h2>
  <ul>
    <li>The pipeline runs once a day, at 05:30 UTC. Polling more often than
        hourly only costs you bandwidth.</li>
    <li>Check <code>meta.json</code> first. It is small, and its
        <code>updated</code> value tells you whether anything moved.</li>
    <li>These are static files on GitHub Pages. There is no authentication,
        no rate limit, and no uptime guarantee. Do not put anything critical
        behind them without caching your own copy.</li>
    <li>A row is an array, in this order: name, town, county, industry,
        routes, rating. Industry is our own guess from the employer's name,
        not official data.</li>
  </ul>

  <h2>Licence and credit</h2>
  <p>The underlying register is Crown copyright, published under the
     <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open
     Government Licence v3.0</a>. The cleaning, the industry tags and the
     change history are ours, and you may use them freely. A link back is
     appreciated but not required.</p>
  <p>The register covers {total} employers.</p>

  <div class="cta">
    <h2 style="margin-top:0">Need something that is not here?</h2>
    <p>If you need a different cut, a longer history, or a filtered feed for
       one region or sector, say so. It is easier to build the thing someone
       actually asked for than to guess.</p>
  </div>
</main>

<footer><div class="wrap">
  <p>Built on the official GOV.UK Register of Licensed Sponsors (Workers).
     SponsorSignal is an independent search tool built on open public data. It
     is not affiliated with the Home Office and is not immigration advice.</p>
  <p><a href="../">Search the register</a></p>
</div></footer>
<script data-goatcounter="{GOATCOUNTER}" async src="//gc.zgo.at/count.js"></script>
{pages.THEME_SCRIPT}
</body>
</html>
"""


def write(root, meta=None):
    directory = root / "data-api"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "index.html").write_text(render(meta), encoding="utf-8")
    return len(ENDPOINTS)
