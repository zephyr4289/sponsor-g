"""
Generates /insights/ - the numbers behind the register.

Why this page exists: it is the one page a recruiter or journalist can link
to, it targets searches the employer list itself cannot ("how many UK
employers sponsor visas"), and it is the natural home for the change history
as that accumulates.

Chart decisions, and the reasons, so they are not undone by accident:

- Every bar chart here is ONE measure across nominal categories, so all bars
  take a single hue. Colouring each bar by its own value would re-encode the
  bar length in the colour channel and say nothing new.
- The hue is the site's cobalt, which measures 7.61:1 against white, well
  past the 3:1 a mark needs. The brand yellow measures 1.54:1 and is
  therefore never a bar and never text, only a background behind ink.
- Bars are 20px thick with 12px of air, so neighbours are separated by the
  surface rather than by a stroke drawn around them.
- Each bar is direct-labelled at its tip, so no gridlines are needed and no
  value is reachable only by hovering.
- Every chart has a real table underneath it. The chart is the summary; the
  table is the accessible, copyable source.

Stdlib only, no build step, no chart library. The SVG is generated here so
the page needs no JavaScript to show its numbers.
"""

import html
from collections import Counter

import pages

SITE = "https://roshan1208.github.io/sponsorsignal"
GOATCOUNTER = "https://sponsorsignal.goatcounter.com/count"

I_NAME, I_TOWN, I_COUNTY, I_INDUSTRY, I_ROUTES, I_RATING = range(6)

# Validated against white with the palette checker: 7.61:1.
BAR = "#2145C9"
BAR_HOVER = "#17348F"

TOP_CITIES = 15
TOP_ROUTES = 8

# The classifier only recognises a keyword it has been taught, so most
# employers fall into "Other". Charting that bucket would say nothing except
# that the classifier is incomplete, which the note under the chart says
# in words instead.
UNCLASSIFIED = "Other"


def count_column(rows, index, skip=()):
    """Count values in one column, most common first."""
    counts = Counter()
    for row in rows:
        value = (row[index] or "").strip()
        if value and value not in skip:
            counts[value] += 1
    return counts.most_common()


def count_routes(rows):
    """Count visa routes. One employer can hold several, so this is a
    count of employers per route, not a partition of the register."""
    counts = Counter()
    for row in rows:
        for route in row[I_ROUTES]:
            if route:
                counts[route] += 1
    return counts.most_common()


def summarise(sponsors, added=(), removed=()):
    """Everything the page needs, as plain data. Pure, so it is testable."""
    ratings = Counter((r[I_RATING] or "").strip() for r in sponsors)
    industries = count_column(sponsors, I_INDUSTRY, skip={UNCLASSIFIED})
    classified = sum(n for _, n in industries)
    return {
        "total": len(sponsors),
        "added": len(added),
        "removed": len(removed),
        "b_rated": ratings.get("B", 0),
        "towns": len({r[I_TOWN] for r in sponsors if r[I_TOWN]}),
        "cities": count_column(sponsors, I_TOWN)[:TOP_CITIES],
        "routes": count_routes(sponsors)[:TOP_ROUTES],
        "industries": industries,
        "classified": classified,
        "unclassified": len(sponsors) - classified,
    }


# The label column is 232px wide. Public Sans at 13px averages a shade over
# 6px a character, so ~33 characters is the most that fits without running
# into the bars. SVG text has no ellipsis of its own, so shorten it here.
LABEL_CHARS = 32

# Several routes share a long prefix. Truncating them raw produced two
# different bars both reading "Global Business Mobility...", which is worse
# than a long label: the reader cannot tell which is which. Abbreviate the
# shared part first so the distinguishing words survive.
ABBREVIATIONS = [("Global Business Mobility:", "GBM:")]

# When the top item is more than this share of the chart, every other bar
# collapses to a sliver. Pull it out and state it in words instead.
DOMINANT_SHARE = 0.5


def split_dominant(items, threshold=DOMINANT_SHARE):
    """Separate a runaway leader from the rest so the bars stay comparable.

    Returns (leader_or_None, rest). The leader is never dropped: it is
    stated above the chart and still appears in the table twin.
    """
    if len(items) < 3:
        return None, items
    total = sum(n for _, n in items)
    if total and items[0][1] / total > threshold:
        return items[0], items[1:]
    return None, items


def shorten(label, limit=LABEL_CHARS):
    """Trim a label to fit its column, breaking at a word where possible.

    The full text stays in the bar's hover title and in the table twin, so
    nothing is lost, and a clipped label is never rendered.
    """
    for long_form, short_form in ABBREVIATIONS:
        label = label.replace(long_form, short_form)
    if len(label) <= limit:
        return label
    cut = label[:limit - 1]
    if " " in cut[limit // 2:]:
        cut = cut[:cut.rindex(" ")]
    return cut.rstrip(" ,:") + "…"


def _bar_path(x, y, width, height, radius=4):
    """A bar with its data-end rounded and its baseline square.

    A plain rect with rx would round the baseline too, which detaches the
    bar from the axis it grows from.
    """
    if width <= radius:
        return f"M{x},{y} h{width:.1f} v{height} h-{width:.1f} Z"
    r = radius
    return (f"M{x},{y} "
            f"H{x + width - r:.1f} "
            f"Q{x + width:.1f},{y} {x + width:.1f},{y + r} "
            f"V{y + height - r} "
            f"Q{x + width:.1f},{y + height} {x + width - r:.1f},{y + height} "
            f"H{x} Z")


def bar_chart(items, chart_id, label, value_word="employers"):
    """A ranked horizontal bar chart as standalone SVG."""
    if not items:
        return ""

    esc = html.escape
    bar_h, band = 20, 32
    left, bar_x, bar_max = 0, 232, 400
    width, height = 720, len(items) * band + 8
    biggest = max(n for _, n in items) or 1

    parts = [
        f'<svg class="chart" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="{chart_id}-t" '
        f'preserveAspectRatio="xMinYMin meet">',
        f'<title id="{chart_id}-t">{esc(label)}</title>',
    ]
    for i, (name, count) in enumerate(items):
        y = i * band + 4
        w = max(1.0, count / biggest * bar_max)
        parts.append(
            f'<g class="bar"><title>{esc(name)}: {count:,} {value_word}</title>'
            f'<text class="cat" x="{left}" y="{y + bar_h - 5}">'
            f'{esc(shorten(name))}</text>'
            f'<path d="{_bar_path(bar_x, y, w, bar_h)}"/>'
            f'<text class="val" x="{bar_x + w + 8:.1f}" y="{y + bar_h - 5}">'
            f'{count:,}</text></g>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def table_twin(items, caption, first_header, total=None):
    """The accessible twin of a chart. Never hidden behind the chart."""
    esc = html.escape
    rows = []
    for name, count in items:
        share = f"{count / total:.1%}" if total else ""
        rows.append(f"<tr><td>{esc(name)}</td><td>{count:,}</td>"
                    + (f"<td>{share}</td>" if total else "") + "</tr>")
    share_head = "<th>Share</th>" if total else ""
    return (
        f'<details class="twin"><summary>{esc(caption)}</summary>'
        f'<table><thead><tr><th>{esc(first_header)}</th><th>Employers</th>'
        f'{share_head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'
        f"</details>"
    )


def _tile(label, value, note=""):
    note_html = f'<span class="note">{html.escape(note)}</span>' if note else ""
    return (f'<div class="tile"><span class="label">{html.escape(label)}</span>'
            f'<span class="value">{value}</span>{note_html}</div>')


def render(stats, updated="", window_days=7):
    """The whole page."""
    esc = html.escape
    title = "UK visa sponsorship in numbers"
    desc = (f"{stats['total']:,} UK employers hold a licence to sponsor work "
            f"visas. Where they are, what they do, and which visa routes they "
            f"can use. Updated every day from the official GOV.UK register.")

    unclassified_share = (stats["unclassified"] / stats["total"]
                          if stats["total"] else 0)

    # A runaway leader is stated in words and given its own callout, so the
    # remaining bars are compared against each other rather than against it.
    city_lead, city_rest = split_dominant(stats["cities"])
    route_lead, route_rest = split_dominant(stats["routes"])

    def lead_block(lead, rest, noun):
        if not lead:
            return "", ""
        name, count = lead
        others = sum(n for _, n in rest)
        text = (f"{esc(name)} alone has {count:,} of them, more than the next "
                f"{len(rest)} {noun} put together ({others:,}). "
                f"It is left out of the chart below so the rest can be "
                f"compared with each other.")
        html_block = (f'<p class="lead-figure"><span class="n">{count:,}</span>'
                      f'<span class="who">in {esc(name)}</span></p>')
        return text, html_block

    city_lead_text, city_lead_html = lead_block(city_lead, city_rest, "cities")
    route_lead_text, route_lead_html = lead_block(route_lead, route_rest, "routes")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} | SponsorSignal</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}/insights/">
<meta property="og:type" content="article">
<meta property="og:url" content="{SITE}/insights/">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="../favicon.png" type="image/png">
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
     margin:36px 0 10px;text-wrap:balance;max-width:18ch}}
  .lead{{color:var(--ink-soft);max-width:60ch;text-wrap:pretty}}
  .updated{{margin-top:8px;font-size:.85rem;color:var(--ink-soft)}}

  /* the one number the page leads with */
  .hero{{margin:34px 0 6px;font-size:clamp(2.6rem,9vw,4rem);font-weight:800;
        letter-spacing:-0.03em;line-height:1}}
  .hero-label{{color:var(--ink-soft);max-width:46ch;text-wrap:pretty}}

  .tiles{{display:grid;gap:12px;margin:28px 0 8px;
         grid-template-columns:repeat(auto-fit,minmax(160px,1fr))}}
  .tile{{border:1.5px solid var(--line);border-radius:10px;padding:14px 16px}}
  .tile .label{{display:block;font-size:.82rem;color:var(--ink-soft)}}
  .tile .value{{display:block;font-size:1.7rem;font-weight:600;letter-spacing:-0.02em;
               margin-top:2px}}
  .tile .note{{display:block;font-size:.78rem;color:var(--ink-soft);margin-top:2px;
              text-wrap:pretty}}

  section.block{{margin:52px 0}}
  h2{{font-size:1.25rem;font-weight:800;letter-spacing:-0.01em;text-wrap:balance}}
  .sub{{color:var(--ink-soft);font-size:.92rem;margin-top:4px;max-width:62ch;
       text-wrap:pretty}}

  /* the pulled-out leader: stated, not squeezed into the bars */
  .lead-figure{{display:flex;align-items:baseline;gap:10px;margin-top:16px;
               padding:12px 14px;border-radius:8px;background:var(--paper-dim);
               border-left:4px solid var(--cobalt)}}
  .lead-figure .n{{font-size:1.6rem;font-weight:600;letter-spacing:-0.02em}}
  .lead-figure .who{{color:var(--ink-soft)}}

  .chart{{width:100%;height:auto;margin-top:18px;overflow:visible}}
  .chart .cat{{font-size:13px;fill:var(--ink)}}
  .chart .val{{font-size:13px;fill:var(--ink-soft);font-variant-numeric:tabular-nums}}
  .chart path{{fill:var(--cobalt)}}
  /* opacity only: a compositor property, so hover cannot cause layout work */
  .chart .bar{{opacity:1;transition:opacity .12s ease-out}}
  .chart:hover .bar{{opacity:.55}}
  .chart .bar:hover{{opacity:1}}
  @media (prefers-reduced-motion:reduce){{.chart .bar{{transition:none}}}}

  .twin{{margin-top:16px;font-size:.9rem}}
  .twin summary{{cursor:pointer;color:var(--cobalt);font-weight:600}}
  .twin table{{width:100%;border-collapse:collapse;margin-top:10px}}
  .twin th{{text-align:left;font-size:.8rem;color:var(--ink-soft);
           border-bottom:2px solid var(--ink);padding:6px 8px}}
  .twin td{{padding:7px 8px;border-bottom:1px solid var(--line);
           font-variant-numeric:tabular-nums}}
  .twin td:first-child{{font-variant-numeric:normal}}

  .caveat{{margin-top:14px;padding:12px 14px;border-radius:8px;
          background:var(--paper-dim);border:1.5px solid var(--line);
          font-size:.88rem;color:var(--ink-soft);max-width:62ch;text-wrap:pretty}}
  .caveat strong{{color:var(--ink)}}

  .cta{{margin:56px 0;border:2px solid var(--ink);border-radius:10px;
       background:var(--paper-dim);padding:24px}}
  .cta h2{{font-size:1.2rem}}
  .cta p{{color:var(--ink-soft);margin-top:6px;max-width:52ch;text-wrap:pretty}}
  .cta a.btn{{display:inline-block;margin-top:14px;background:var(--cobalt);
             color:#fff;text-decoration:none;font-weight:600;padding:11px 22px;
             border-radius:8px}}
  :is(a,summary,button):focus-visible{{outline:3px solid var(--cobalt);outline-offset:2px}}

  footer{{margin-top:48px;border-top:3px solid var(--ink);padding:22px 0 40px;
         font-size:.85rem;color:var(--ink-soft)}}
  footer p+p{{margin-top:6px}}
  {pages.HEADER_CSS}{pages.THEME_TOGGLE_CSS}
  @media (max-width:640px){{ .chart .cat{{font-size:11px}} .chart .val{{font-size:11px}} }}
</style>
{pages.THEME_BOOT}
</head>
<body>
{pages.site_header('insights')}

<main class="wrap">
  <h1>{esc(title)}</h1>
  <p class="lead">Every employer allowed to sponsor a UK work visa is on one
     official register. Here is what is actually in it.</p>
  <p class="updated">From the GOV.UK Register of Licensed Sponsors{
      f", updated {esc(updated)}" if updated else ""}.</p>

  <p class="hero">{stats['total']:,}</p>
  <p class="hero-label">employers can sponsor a UK work visa. Every other
     employer in the country cannot, however good your application.</p>

  <div class="tiles">
    {_tile("Added in the last " + str(window_days) + " days",
           f"{stats['added']:,}", "newly licensed")}
    {_tile("Lost their licence", f"{stats['removed']:,}",
           f"in the last {window_days} days")}
    {_tile("On a B rating", f"{stats['b_rated']:,}",
           "usually cannot issue new certificates")}
    {_tile("Towns and cities", f"{stats['towns']:,}", "with at least one sponsor")}
  </div>

  <section class="block">
    <h2>Where the sponsors are</h2>
    <p class="sub">London is not a tie-breaker, it is the whole race.
       {city_lead_text}</p>
    {city_lead_html}
    {bar_chart(city_rest, "cities", "Licensed employers by town or city, outside the largest")}
    {table_twin(stats['cities'], "See these numbers as a table, including "
                + (city_lead[0] if city_lead else "every city"), "Town or city",
                total=stats['total'])}
  </section>

  <section class="block">
    <h2>Which visa routes they can use</h2>
    <p class="sub">A licence covers named routes, and most employers hold only
       one. {route_lead_text}</p>
    {route_lead_html}
    {bar_chart(route_rest, "routes", "Employers licensed for each visa route, "
               "excluding the most common")}
    {table_twin(stats['routes'], "See these numbers as a table, including "
                + (route_lead[0] if route_lead else "every route"), "Visa route")}
    <p class="caveat">One employer can hold several routes, so these add up to
       more than {stats['total']:,}.</p>
  </section>

  <section class="block">
    <h2>What they do</h2>
    <p class="sub">Industries are not in the official register. We work them
       out from each employer's name, which only succeeds when the name says
       what the business does.</p>
    {bar_chart(stats['industries'], "industries", "Licensed employers by industry")}
    {table_twin(stats['industries'], "See these numbers as a table", "Industry",
                total=stats['classified'])}
    <p class="caveat"><strong>Read this before quoting these figures.</strong>
       They cover the {stats['classified']:,} employers whose industry we could
       work out. The other {stats['unclassified']:,},
       {unclassified_share:.0%} of the register, have names that do not say what
       the business does, so they are not counted here. This is a limit of our
       own guesswork, not of the register.</p>
  </section>

  <section class="cta">
    <h2>Get the changes each week</h2>
    <p>The register moves every week. We send the newly licensed employers,
       and the ones that lost their licence, so you are not applying into the
       dark.</p>
    <a class="btn" href="../#alerts">Get the weekly email</a>
  </section>
</main>

<footer><div class="wrap">
  <p>Built on the official GOV.UK Register of Licensed Sponsors (Workers).
     SponsorSignal is an independent search tool built on open public data.
     It is not affiliated with the Home Office and is not immigration advice.</p>
  <p><a href="../">Search the full list</a></p>
</div></footer>
<script data-goatcounter="{GOATCOUNTER}" async src="//gc.zgo.at/count.js"></script>
{pages.THEME_SCRIPT}
</body>
</html>
"""


def write(root, sponsors, added=(), removed=(), updated="", window_days=7):
    """Generate insights/index.html. Returns the stats used."""
    stats = summarise(sponsors, added, removed)
    directory = root / "insights"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "index.html").write_text(
        render(stats, updated=updated, window_days=window_days),
        encoding="utf-8",
    )
    return stats
