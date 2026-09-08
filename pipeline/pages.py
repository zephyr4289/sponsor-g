"""
Static landing-page generator for SponsorSignal.

Builds one small SEO page per top industry and per top town, e.g.
    /tech-software/index.html
    /london/index.html
Each page carries real content (a lead paragraph plus a sample of the
sponsors it covers) and links through to the main app pre-filtered using
the query params from index.html.

Also regenerates sitemap.xml and the "browse" nav injected into the
homepage footer between the BROWSE-LINKS markers.

Everything except write_all() is a pure function so it can be unit tested
(see pipeline/test_pages.py). Stdlib only.
"""

import html
import json
import re
import unicodedata
from urllib.parse import urlencode

SITE = "https://roshan1208.github.io/sponsorsignal"

# Must match the tag at the bottom of index.html. These pages are the whole
# SEO channel, so leaving them untracked would hide the traffic that matters.
GOATCOUNTER = "https://sponsorsignal.goatcounter.com/count"

TOP_INDUSTRIES = 8
TOP_TOWNS = 12
EXAMPLES_PER_PAGE = 25

# Record layout in sponsors.json
I_NAME, I_TOWN, I_COUNTY, I_INDUSTRY, I_ROUTES, I_RATING = range(6)

# Not a useful landing page - it is the classifier's fallback bucket.
SKIP_INDUSTRIES = {"", "Other"}

BROWSE_START = "<!-- BROWSE-LINKS:START -->"
BROWSE_END = "<!-- BROWSE-LINKS:END -->"


def site_header(current=""):
    """The shared header. `current` is 'changes' or 'insights' on those pages,
    so the link to the page you are already on is not repeated as a link.

    Every generated page sits one directory below the root, so the paths are
    always '../'.
    """
    links = []
    for slug, label in (("changes", "This week's changes"),
                        ("insights", "The numbers")):
        if slug == current:
            links.append(f'<span aria-current="page">{label}</span>')
        else:
            links.append(f'<a href="../{slug}/">{label}</a>')
    return (
        '<header><div class="wrap header-inner">'
        '<div class="brand"><a href="../">SponsorSignal'
        '<span class="dot">.</span></a></div>'
        f'<nav class="topnav" aria-label="Sections">{"".join(links)}'
        f'{THEME_TOGGLE}</nav>'
        "</div></header>"
    )


# The whole palette, both modes, in one place. Every generated page pulls
# this in, and index.html carries an identical copy: keep the two in step.
#
# Dark is *selected*, not an inversion. Each value was picked against the dark
# surface and then checked with a contrast calculation, not by eye. The
# darkest pairing clears 5.4:1 and the rest are well above, so all body text
# meets WCAG AA in both modes. If you change a value here, re-check it.
#
# --on-signal exists because text on the yellow highlight must stay dark in
# both modes. Using --ink there would turn it near-white on yellow in dark.
THEME_CSS = """
  :root{
    --ink:#17233B; --ink-soft:#4A5670;
    --paper:#FFFFFF; --paper-dim:#F5F7FB;
    --cobalt:#2145C9; --cobalt-dark:#17348F;
    --signal:#FFC933; --on-signal:#17233B;
    --line:#D9DFEA; --good:#0E7B4F; --bad:#B3261E;
    --warn-bg:#FDF1F0; --warn-bg-2:#FBE3E1; --warn-border:#E7B4AE;
    --warn-ink:#8A1E18; --warn-solid:#B3261E;
    --mark-bg:#17233B; --mark-fg:#FFFFFF;
    --note-bg:#FFF6DC; --note-border:#EAD48A;
    --shadow:rgba(23,35,59,.10);
    color-scheme:light;
  }
  @media (prefers-color-scheme:dark){
    :root:not([data-theme="light"]){
      --ink:#E8ECF3; --ink-soft:#A3AEC2;
      --paper:#10151F; --paper-dim:#1A2230;
      --cobalt:#6B93F5; --cobalt-dark:#8FADF8;
      --signal:#FFC933; --on-signal:#17233B;
      --line:#2A3444; --good:#4FBF8B; --bad:#F08A82;
      --warn-bg:#2A1A19; --warn-bg-2:#3A1F1D; --warn-border:#6B2B26;
      --warn-ink:#F5B5AE; --warn-solid:#B3261E;
      --mark-bg:#E8ECF3; --mark-fg:#10151F;
    --note-bg:#2A2412; --note-border:#5A4A1E;
      --note-bg:#2A2412; --note-border:#5A4A1E;
      --shadow:rgba(0,0,0,.45);
      color-scheme:dark;
    }
  }
  :root[data-theme="dark"]{
    --ink:#E8ECF3; --ink-soft:#A3AEC2;
    --paper:#10151F; --paper-dim:#1A2230;
    --cobalt:#6B93F5; --cobalt-dark:#8FADF8;
    --signal:#FFC933; --on-signal:#17233B;
    --line:#2A3444; --good:#4FBF8B; --bad:#F08A82;
    --warn-bg:#2A1A19; --warn-bg-2:#3A1F1D; --warn-border:#6B2B26;
    --warn-ink:#F5B5AE; --warn-solid:#B3261E;
    --mark-bg:#E8ECF3; --mark-fg:#10151F;
    --note-bg:#2A2412; --note-border:#5A4A1E;
    --shadow:rgba(0,0,0,.45);
    color-scheme:dark;
  }
"""

# Sets the theme before first paint, so a dark-mode visitor never sees a
# white flash. Kept tiny and inline on purpose: an external file would be a
# render-blocking round trip for four lines of work.
THEME_BOOT = (
    "<script>(function(){try{var t=localStorage.getItem('theme');"
    "if(t)document.documentElement.setAttribute('data-theme',t);}catch(e){}})();"
    "</script>"
)


# One button, in the shared header, so every page can switch theme. Labelled
# for screen readers and reflects the current state in aria-pressed.
THEME_TOGGLE = (
    '<button class="themebtn" type="button" data-theme-toggle'
    ' aria-label="Switch between light and dark theme">'
    '<span aria-hidden="true">&#9789;</span></button>'
)

THEME_TOGGLE_CSS = """
  .themebtn{
    font:inherit;font-size:1rem;line-height:1;cursor:pointer;
    background:transparent;border:1.5px solid var(--line);border-radius:99px;
    color:var(--ink-soft);padding:5px 10px;
  }
  .themebtn:hover{border-color:var(--ink-soft);color:var(--ink)}
"""

# Applies the toggle on every page that includes it. Stores the choice so it
# survives navigation, and leaves the system preference alone until asked.
THEME_SCRIPT = (
    "<script>(function(){var b=document.querySelector('[data-theme-toggle]');"
    "if(!b)return;var r=document.documentElement;"
    "function dark(){return r.getAttribute('data-theme')==='dark'||"
    "(!r.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme:dark)').matches);}"
    "function sync(){b.setAttribute('aria-pressed',String(dark()));}"
    "b.addEventListener('click',function(){var next=dark()?'light':'dark';"
    "r.setAttribute('data-theme',next);try{localStorage.setItem('theme',next);}catch(e){}"
    "sync();});sync();})();</script>"
)


HEADER_CSS = """
  .header-inner{display:flex;align-items:center;justify-content:space-between;
                gap:16px;flex-wrap:wrap}
  .topnav{display:flex;gap:18px;font-size:.9rem;font-weight:600}
  .topnav a{text-decoration:none}
  .topnav a:hover{text-decoration:underline}
  .topnav [aria-current]{color:var(--ink-soft)}
  @media (max-width:520px){.topnav{gap:14px;font-size:.85rem;width:100%}}
"""


def slugify(value):
    """'Tech & Software' -> 'tech-software'."""
    value = unicodedata.normalize("NFKD", str(value))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value


def top_values(sponsors, index, limit, skip=()):
    """Most common values at `index`, as [(label, count)], count desc."""
    counts = {}
    for row in sponsors:
        label = (row[index] or "").strip()
        if not label or label in skip:
            continue
        counts[label] = counts.get(label, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    return ordered[:limit]


def examples_for(sponsors, index, label, limit=EXAMPLES_PER_PAGE):
    """A stable alphabetical sample of the sponsors on a page."""
    matches = [r for r in sponsors if (r[index] or "").strip() == label]
    matches.sort(key=lambda r: str(r[I_NAME]).lower())
    return matches[:limit]


def filter_query(kind, label):
    """Query string that reproduces this page's view in the main app.

    Both kinds map to a real filter. Towns used to fall back to the
    free-text search, which also matched employers with the town in their
    name, so a city page overstated its own count.
    """
    key = "industry" if kind == "industry" else "city"
    return urlencode({key: label})


def build_pages(sponsors):
    """Plan every landing page. Pure - returns a list of dicts."""
    pages = []
    for label, count in top_values(sponsors, I_INDUSTRY, TOP_INDUSTRIES,
                                   skip=SKIP_INDUSTRIES):
        pages.append({
            "kind": "industry",
            "label": label,
            "count": count,
            "slug": slugify(label),
            "examples": examples_for(sponsors, I_INDUSTRY, label),
        })
    industry_slugs = {p["slug"] for p in pages}
    for label, count in top_values(sponsors, I_TOWN, TOP_TOWNS):
        slug = slugify(label)
        if not slug or slug in industry_slugs:
            continue
        pages.append({
            "kind": "town",
            "label": label,
            "count": count,
            "slug": slug,
            "examples": examples_for(sponsors, I_TOWN, label),
        })
    return pages


def lead_paragraph(page):
    """A distinct opening paragraph per page (no duplicate boilerplate)."""
    label, count = page["label"], page["count"]
    n = f"{count:,}"
    if page["kind"] == "industry":
        return (f"{n} employers in {label.lower()} hold a Home Office licence "
                f"to sponsor workers in the UK. A licence does not mean they "
                f"are hiring today. It means they can sponsor your visa if "
                f"they do hire you.")
    return (f"{n} employers in {label} hold a licence to sponsor work visas. "
            f"If you need sponsorship, these are the ones who can offer it. "
            f"Any other employer in {label} cannot, no matter how good your "
            f"application.")


def render_page(page, updated=""):
    """Render one landing page to a complete HTML document."""
    label = page["label"]
    where = f"in {label}" if page["kind"] == "town" else f"in {label.lower()}"
    title = f"Companies that sponsor UK work visas {where}"
    esc = html.escape
    url = f"{SITE}/{page['slug']}/"
    app = "../?" + filter_query(page["kind"], label)
    desc = (f"{page['count']:,} UK employers {where} can sponsor a work visa. "
            f"Search the full list, updated every day from the official "
            f"GOV.UK register.")

    rows = []
    for r in page["examples"]:
        location = ", ".join(p for p in (r[I_TOWN], r[I_COUNTY]) if p)
        routes = ", ".join(r[I_ROUTES])
        rows.append(
            f"      <tr><td>{esc(str(r[I_NAME]))}</td>"
            f"<td>{esc(location)}</td><td>{esc(routes)}</td></tr>"
        )
    table = "\n".join(rows)
    more = max(0, page["count"] - len(page["examples"]))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} | SponsorSignal</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(url)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;800&display=swap" rel="stylesheet">
<style>
{THEME_CSS}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Public Sans',system-ui,sans-serif;color:var(--ink);line-height:1.55;background:#fff}}
  .wrap{{max-width:960px;margin:0 auto;padding:0 20px}}
  header{{border-bottom:3px solid var(--ink);padding:14px 0}}
  .brand{{font-weight:800;font-size:1.1rem}}
  .brand a{{color:inherit;text-decoration:none}}
  .brand .dot{{color:var(--cobalt)}}
  h1{{font-size:clamp(1.5rem,4vw,2.2rem);font-weight:800;letter-spacing:-0.02em;margin:36px 0 12px;max-width:700px}}
  p.lead{{color:var(--ink-soft);max-width:640px}}
  .cta{{display:inline-block;margin:22px 0 8px;background:var(--cobalt);color:#fff;
       text-decoration:none;font-weight:600;padding:11px 22px;border-radius:8px}}
  h2{{font-size:1.15rem;margin:34px 0 10px}}
  table{{width:100%;border-collapse:collapse;font-size:.95rem}}
  th{{text-align:left;font-size:.82rem;color:var(--ink-soft);border-bottom:2px solid var(--ink);padding:8px 10px 6px}}
  td{{padding:10px;border-bottom:1px solid var(--line);vertical-align:top}}
  tr:hover td{{background:var(--paper-dim)}}
  .more{{margin-top:14px;color:var(--ink-soft);font-size:.9rem}}
  footer{{margin-top:48px;border-top:3px solid var(--ink);padding:22px 0 40px;
         font-size:.85rem;color:var(--ink-soft)}}
  a{{color:var(--cobalt)}}{HEADER_CSS}{THEME_TOGGLE_CSS}
</style>
{THEME_BOOT}
</head>
<body>
{site_header()}
<main class="wrap">
  <h1>{esc(title)}</h1>
  <p class="lead">{esc(lead_paragraph(page))}</p>
  <a class="cta" href="{esc(app)}">Search all {page['count']:,} &rarr;</a>

  <h2>Some of these employers</h2>
  <table>
    <thead><tr><th>Employer</th><th>Location</th><th>Visa routes</th></tr></thead>
    <tbody>
{table}
    </tbody>
  </table>
  <p class="more">Showing {len(page['examples'])} of {page['count']:,}.
     <a href="{esc(app)}">Search the full list</a>{f' to see the other {more:,}' if more else ''}.</p>
</main>
<footer><div class="wrap">
  <p>Source: GOV.UK Register of Licensed Sponsors (Workers){f", updated {esc(updated)}" if updated else ""}.
     SponsorSignal is an independent search tool built on open public data. It is
     not affiliated with the Home Office and is not immigration advice.</p>
  <p><a href="../">Back to search</a></p>
</div></footer>
<script data-goatcounter="{GOATCOUNTER}" async src="//gc.zgo.at/count.js"></script>
{THEME_SCRIPT}
</body>
</html>
"""


def render_browse_nav(pages):
    """The industry/city link block injected into the homepage footer."""
    esc = html.escape
    inds = [p for p in pages if p["kind"] == "industry"]
    towns = [p for p in pages if p["kind"] == "town"]
    out = []
    for heading, group in (("Browse by industry", inds), ("Browse by city", towns)):
        if not group:
            continue
        links = " ".join(
            f'<a href="{p["slug"]}/">{esc(p["label"])}</a>' for p in group
        )
        # class="links" scopes the gap between adjacent links. Without it the
        # rule also applied to links that sit inside a sentence and pushed the
        # following full stop away from the word.
        out.append(f'    <p class="links"><strong>{heading}:</strong> {links}</p>')
    return "\n".join(out)


def inject_browse_links(page_html, nav_html):
    """Replace whatever sits between the BROWSE-LINKS markers."""
    pattern = re.compile(
        re.escape(BROWSE_START) + r".*?" + re.escape(BROWSE_END), re.S
    )
    if not pattern.search(page_html):
        raise RuntimeError("BROWSE-LINKS markers not found in index.html")
    return pattern.sub(
        f"{BROWSE_START}\n{nav_html}\n    {BROWSE_END}", page_html
    )


def render_sitemap(pages):
    urls = [(f"{SITE}/", "daily", "1.0"),
            (f"{SITE}/changes/", "daily", "0.9"),
            (f"{SITE}/insights/", "weekly", "0.9"),
            (f"{SITE}/data-api/", "monthly", "0.7")]
    urls += [(f"{SITE}/{p['slug']}/", "weekly", "0.8") for p in pages]
    body = "\n".join(
        f"  <url>\n"
        f"    <loc>{loc}</loc>\n"
        f"    <changefreq>{freq}</changefreq>\n"
        f"    <priority>{pri}</priority>\n"
        f"  </url>"
        for loc, freq, pri in urls
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{body}\n</urlset>\n")


# Which slugs the last run generated. Without this a page that drops out of
# the top list stays live and indexed, unlinked and slowly going stale, which
# is worse than never having existed.
MANIFEST = "generated_pages.json"


def stale_slugs(previous, current):
    """Slugs generated last time that are not generated this time."""
    return sorted(set(previous) - set(current))


def read_manifest(data_dir):
    try:
        return json.loads((data_dir / MANIFEST).read_text(encoding="utf-8"))["slugs"]
    except Exception:
        return []


def remove_stale(root, slugs):
    """Delete pages we generated and no longer generate.

    Only removes a directory that contains exactly the index.html we wrote,
    so a hand-made directory, or one holding anything else, is never touched.
    """
    removed = []
    for slug in slugs:
        directory = root / slug
        page = directory / "index.html"
        if not page.exists():
            continue
        if {entry.name for entry in directory.iterdir()} != {"index.html"}:
            continue
        page.unlink()
        directory.rmdir()
        removed.append(slug)
    return removed


def write_all(root, sponsors, updated=""):
    """Generate every landing page, the sitemap, and the homepage nav."""
    pages = build_pages(sponsors)

    for page in pages:
        directory = root / page["slug"]
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(
            render_page(page, updated), encoding="utf-8"
        )

    (root / "sitemap.xml").write_text(render_sitemap(pages), encoding="utf-8")

    index = root / "index.html"
    index.write_text(
        inject_browse_links(index.read_text(encoding="utf-8"),
                            render_browse_nav(pages)),
        encoding="utf-8",
    )

    # Retire pages that dropped out of the top list, then record what this
    # run produced so the next one can do the same.
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    slugs = [p["slug"] for p in pages]
    gone = remove_stale(root, stale_slugs(read_manifest(data_dir), slugs))
    if gone:
        print("Retired landing pages no longer in the top list:", ", ".join(gone))
    (data_dir / MANIFEST).write_text(
        json.dumps({"slugs": sorted(slugs)}, indent=1), encoding="utf-8")

    return pages
