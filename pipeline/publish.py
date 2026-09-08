"""
Decides what leaves the private repo and reaches the public site.

Why this is a module and not a shell script: the boundary between "free
product" and "the thing we sell" is a product decision, and it should be
written down somewhere a test can check it. A `cp -r` in a workflow is a
decision nobody can see.

The split it serves:

    sponsorsignal-core   private. pipeline, full change history, the join.
    sponsorsignal        public.  the served site plus the free-tier data.

The rule for what is public:

- Anything the site fetches at runtime has to be, or the site breaks.
- The current register is public data already, and giving it away is what
  earns the traffic and the trust.
- Per-employer company warnings stay public. They protect somebody about to
  move country for a job, and gating that would be indefensible.
- The full dated change history does not. GOV.UK publishes only today's
  register, so the accumulated series is the one thing a competitor cannot
  download, and we were publishing it as an open file.
- The newsletter body is not a site asset. It is the product being sold.

Anything not named in either list is reported rather than guessed at, so a
new file added next year cannot silently end up on either side.
"""

import shutil
from pathlib import Path

# Fetched by the site at runtime, or deliberately given away.
PUBLIC_DATA = {
    "sponsors.json": "the register itself. The free product.",
    "meta.json": "counts and the update time. Fetched by the site.",
    "new_sponsors.json": "last 7 days of additions. Fetched by the site.",
    "removed_sponsors.json": "last 7 days of removals. Fetched by the site.",
    "company_flags.json": "per-employer company warnings. Kept public on "
                          "purpose: it protects people.",
    "regional_changes.json": "last 7 days by region. The free hook, and "
                             "already documented for outside use.",
}

# Never published. Each line is a reason, not a preference.
INTERNAL_DATA = {
    "changes.json": "the full dated history. This is the moat: it cannot be "
                    "rebuilt from GOV.UK, only accumulated day by day.",
    "digest.md": "the newsletter body. That is the product, not a site file.",
    "generated_pages.json": "build bookkeeping. Useless to anyone else.",
}

# Site files that are published as-is. Directories are copied whole.
PUBLIC_ROOT = [
    "index.html", "robots.txt", "sitemap.xml", "feed.xml",
    "manifest.json", "sw.js", "favicon.png", "og-image.png",
    "icons", "changes", "insights", "data-api",
]

# Generated landing pages are discovered rather than listed, because which
# cities and industries make the top list changes with the data.
LANDING_MARKER = "index.html"


def landing_dirs(root, known=PUBLIC_ROOT):
    """Generated landing-page directories, e.g. london/, tech-software/."""
    skip = set(known) | {"data", "pipeline", ".git", ".github", ".claude",
                         "launch", "outreach", "__pycache__"}
    out = []
    for entry in sorted(Path(root).iterdir()):
        if not entry.is_dir() or entry.name in skip or entry.name.startswith("."):
            continue
        if (entry / LANDING_MARKER).exists():
            out.append(entry.name)
    return out


def plan(data_dir):
    """Sort what is in data/ into publish, withhold, and unrecognised.

    The third bucket is the point. A file nobody classified is a decision
    waiting to be made by accident.
    """
    present = sorted(p.name for p in Path(data_dir).iterdir() if p.is_file())
    publish = [n for n in present if n in PUBLIC_DATA]
    withhold = [n for n in present if n in INTERNAL_DATA]
    unknown = [n for n in present
               if n not in PUBLIC_DATA and n not in INTERNAL_DATA]
    return publish, withhold, unknown


def public_files(root):
    """Every path that belongs in the public repo, relative to `root`."""
    root = Path(root)
    out = []
    for name in PUBLIC_ROOT + landing_dirs(root):
        if (root / name).exists():
            out.append(name)
    publish, _, _ = plan(root / "data")
    out += [f"data/{name}" for name in publish]
    return out


def stage(root, dest):
    """Copy exactly the public paths into `dest`, and nothing else.

    Building a staging directory rather than deleting from a checkout means
    the boundary is expressed as "what goes in" instead of "what to strip
    out". Forgetting to add something breaks the site loudly; forgetting to
    strip something leaks it silently.
    """
    root, dest = Path(root), Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in public_files(root):
        source = root / name
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
            copied += [str(Path(name) / f.relative_to(source)).replace("\\", "/")
                       for f in sorted(source.rglob("*")) if f.is_file()]
        else:
            shutil.copy2(source, target)
            copied.append(name)
    return sorted(copied)


def audit(staged):
    """Anything in a staging list that must never have got there.

    A second, independent check. stage() decides what to copy; this asks
    whether the result is safe, so a bug in the first does not go unnoticed.
    """
    forbidden = []
    for path in staged:
        first = path.split("/")[0]
        if first in ("pipeline", "outreach", "internal", ".github", ".claude"):
            forbidden.append(path)
        elif path.startswith("data/") and Path(path).name in INTERNAL_DATA:
            forbidden.append(path)
    return forbidden


def describe():
    """A human-readable account of the boundary, for the commit or the docs."""
    lines = ["Published to the public site:"]
    for name, why in sorted(PUBLIC_DATA.items()):
        lines.append(f"  data/{name:<24} {why}")
    lines.append("")
    lines.append("Kept in the private repo:")
    for name, why in sorted(INTERNAL_DATA.items()):
        lines.append(f"  data/{name:<24} {why}")
    return "\n".join(lines)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    publish, withhold, unknown = plan(root / "data")
    print(describe())
    print()
    print(f"{len(public_files(root))} paths would be published, "
          f"{len(withhold)} withheld.")
    if unknown:
        raise SystemExit(
            "\nUnclassified files in data/: " + ", ".join(unknown) +
            "\nAdd each to PUBLIC_DATA or INTERNAL_DATA in pipeline/publish.py "
            "and say why. Refusing to guess."
        )
