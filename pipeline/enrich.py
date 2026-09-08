"""
Monthly job: join the sponsor register to Companies House.

Run separately from the daily refresh, because the Companies House snapshot is
monthly and about 470MB across seven files. Downloading that every day would
be rude to them and pointless for us.

Output is deliberately small. Only sponsors carrying at least one signal are
published, which is a few thousand of ~128,000, so the site can load the file
alongside the register without a second thought. Everything else about a
matched company is knowable from Companies House directly and does not need
mirroring here.

    python pipeline/enrich.py            # download and join
    python pipeline/enrich.py --local DIR  # reuse parts already downloaded

Stdlib only.
"""

import argparse
import csv
import io
import json
import sys
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import companies as ch

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

BASE = "https://download.companieshouse.gov.uk"
PARTS = 7
UA = {"User-Agent": "SponsorSignal/1.0 (public-data enrichment; contact via site)"}

# Refuse to publish a join that looks broken. The register barely moves month
# to month, so a sudden collapse in matches means the download or the naming
# changed, not that 20,000 companies vanished.
MIN_MATCH_RATE = 0.60


def snapshot_name(today=None):
    """Companies House publishes on the first of the month."""
    today = today or date.today()
    return f"{today.year:04d}-{today.month:02d}-01"


def part_urls(stamp):
    return [f"{BASE}/BasicCompanyData-{stamp}-part{n}_{PARTS}.zip"
            for n in range(1, PARTS + 1)]


def rows_from_zip(path_or_bytes):
    """Stream a Companies House zip as dicts, one row at a time.

    Its own header ships stray leading spaces on some columns, so the names
    are stripped before use.
    """
    z = zipfile.ZipFile(path_or_bytes)
    for member in z.namelist():
        if not member.lower().endswith(".csv"):
            continue
        with z.open(member) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8-sig", newline="")
            reader = csv.reader(text)
            try:
                header = [h.strip() for h in next(reader)]
            except StopIteration:
                continue
            for row in reader:
                yield dict(zip(header, row))


def download(url):
    print(f"  downloading {url.rsplit('/', 1)[-1]} ...", flush=True)
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=900) as response:
        return io.BytesIO(response.read())


def iter_all(stamp, local=None):
    """Every Companies House row, from local files if given, else the web."""
    if local:
        paths = sorted(Path(local).glob("*.zip"))
        if not paths:
            raise SystemExit(f"No .zip files in {local}")
        for path in paths:
            print(f"  reading {path.name} ...", flush=True)
            yield from rows_from_zip(path)
        return
    for url in part_urls(stamp):
        yield from rows_from_zip(download(url))


def summarise(matched, sponsors):
    """Counts for the site, and the numbers the guard checks."""
    counts = {}
    for record in matched.values():
        for flag in record["flags"]:
            counts[flag] = counts.get(flag, 0) + 1
    flagged = {p: r for p, r in matched.items() if r["flags"]}
    return {
        "sponsors": len(sponsors),
        "matched": len(matched),
        "match_rate": round(len(matched) / len(sponsors), 4) if sponsors else 0,
        "flagged": len(flagged),
        "flag_counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
    }


def build(sponsors, rows, today=None):
    """Join and reduce to what gets published. Pure apart from the clock."""
    today = today or date.today()
    index = ch.build_index(sponsors)
    matched = ch.join(rows, index, today)
    stats = summarise(matched, sponsors)

    # Keyed by the sponsor's name exactly as the register spells it.
    #
    # Not by row position, because positions shift every day as the register
    # changes and this file is monthly. And not by the normalised name,
    # because the site would then have to reimplement normalise_name() in
    # JavaScript, and two copies of that logic would drift apart. An exact
    # string lookup cannot drift. If the register renames a sponsor between
    # monthly runs the key simply misses, which shows no warning rather than
    # the wrong one.
    published = {}
    for position, record in matched.items():
        if not record["flags"]:
            continue
        key = str(sponsors[position][0])
        if key and key not in published:
            published[key] = {
                "number": record["number"],
                "status": record["status"],
                "incorporated": record["incorporated"],
                "accounts": record["accounts"],
                "flags": record["flags"],
            }
    return published, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", help="directory of already downloaded parts")
    parser.add_argument("--allow-low-match", action="store_true",
                        help="publish even if the match rate looks broken")
    args = parser.parse_args()

    sponsors_file = DATA / "sponsors.json"
    if not sponsors_file.exists():
        raise SystemExit("data/sponsors.json is missing. Run refresh.py first.")
    sponsors = json.loads(sponsors_file.read_text(encoding="utf-8"))["sponsors"]
    print(f"Sponsors on the register: {len(sponsors):,}")

    stamp = snapshot_name()
    print(f"Companies House snapshot: {stamp}")
    published, stats = build(sponsors, iter_all(stamp, args.local))

    print(f"Matched {stats['matched']:,} of {stats['sponsors']:,} "
          f"({stats['match_rate']:.0%})")
    print(f"Carrying at least one signal: {stats['flagged']:,}")
    for flag, count in stats["flag_counts"].items():
        print(f"    {flag:<34}{count:>7,}")

    if stats["match_rate"] < MIN_MATCH_RATE and not args.allow_low_match:
        raise SystemExit(
            f"\nRefusing to publish: matched only {stats['match_rate']:.0%}, "
            f"below the {MIN_MATCH_RATE:.0%} floor. The download or the "
            f"column names have probably changed. Re-run with "
            f"--allow-low-match only if you have checked why."
        )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (DATA / "company_flags.json").write_text(
        json.dumps({"updated": now, "snapshot": stamp,
                    "source": "Companies House Free Company Data Product",
                    "stats": stats, "companies": published},
                   separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8")
    size = (DATA / "company_flags.json").stat().st_size
    print(f"\nWrote data/company_flags.json ({size // 1024:,} KB)")


if __name__ == "__main__":
    main()
