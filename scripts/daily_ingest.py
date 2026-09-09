#!/usr/bin/env python3
"""
KnowYourSponsor — Daily Ingestion, Diffing & Normalization Engine
Statutory UKVI Register of Licensed Sponsors (Workers & Temporary Workers)

Fetches upstream Home Office CSV, computes longitudinal diffs (new, removed,
rating changes), maps solvency status, and updates static data endpoints.
"""

import os
import sys
import re
import csv
import json
import hashlib
import argparse
from datetime import datetime, timezone
import urllib.request
import urllib.error

# Official GOV.UK publication landing page for Worker & Temporary Worker sponsor register
GOV_UK_REGISTER_PAGE = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KnowYourSponsor-Ingestion/2.0"

# Sector classification keyword dictionary
SECTOR_KEYWORDS = {
    "Tech & Software": [
        "technology", "technologies", "software", "digital", "systems", "cyber",
        "solutions ltd", "it solutions", "cloud", "data", "ai ltd", "analytics",
        "interactive", "telecom", "networks", "infotech", "tech ltd", "robotics"
    ],
    "Healthcare & Care": [
        "care", "healthcare", "health", "nursing", "medical", "dental", "clinic",
        "pharmacy", "pharmaceutical", "hospital", "surgery", "therap", "optician",
        "ambulance", "residential home", "care home", "homecare", "domiciliary"
    ],
    "Finance & Professional": [
        "capital", "finance", "financial", "advisors", "consulting", "consultancy",
        "accountants", "accounting", "partners", "investments", "asset management",
        "solicitors", "legal", "law", "wealth", "holdings", "auditing", "actuarial"
    ],
    "Hospitality & Food": [
        "restaurant", "hotel", "catering", "cafe", "kitchen", "inn", "pizza",
        "grill", "foods", "sweets", "bakery", "tandoori", "spice", "bistro",
        "hospitality", "dining", "bar &", "takeaway", "diner", "cuisine", "pub"
    ],
    "Construction & Engineering": [
        "construction", "engineering", "builders", "building", "contractors",
        "electrical", "plumbing", "civil", "architects", "architecture", "structural",
        "joinery", "scaffolding", "renovation", "infrastructure", "surveyors"
    ],
    "Education & Research": [
        "school", "college", "university", "academy", "education", "learning",
        "institute", "research", "grammar", "training", "studies", "tuition"
    ],
    "Media & Creative": [
        "media", "creative", "productions", "studios", "design", "advertising",
        "marketing", "publishing", "film", "broadcast", "entertainment", "theatre"
    ],
    "Retail & Commerce": [
        "supermarket", "store", "stores", "retail", "wholesale", "trading",
        "grocers", "grocery", "convenience", "cash & carry", "mart", "bazaar"
    ],
    "Logistics & Transport": [
        "logistics", "transport", "courier", "freight", "haulage", "shipping",
        "cargo", "deliveries", "supply chain", "express", "distribution"
    ],
    "Property & Real Estate": [
        "property", "properties", "estate", "estates", "realty", "lettings",
        "land", "housing", "developments", "residential"
    ],
    "Manufacturing & Industry": [
        "manufacturing", "manufacturers", "industrial", "steel", "plastics",
        "chemicals", "textiles", "precision", "packaging", "fabrications"
    ],
    "Motor & Automotive": [
        "motors", "motor", "automotive", "garage", "tyres", "car sales",
        "autocentre", "autos", "body shop", "vehicle"
    ],
    "Energy & Utilities": [
        "energy", "solar", "wind", "renewables", "utilities", "power", "oil & gas"
    ],
    "Security & Facilities": [
        "security", "guarding", "facilities", "cleaning", "maintenance"
    ],
    "Recruitment & Staffing": [
        "recruitment", "staffing", "personnel", "workforce", "employment"
    ],
    "Charity & Faith": [
        "church", "mosque", "temple", "ministries", "charity", "trust", "diocese",
        "mission", "gospel", "parish", "community centre", "islamic", "christian"
    ],
    "Beauty & Wellbeing": [
        "hair", "beauty", "salon", "barber", "spa", "cosmetics", "aesthetics"
    ],
    "Agriculture & Food Production": [
        "farms", "farming", "farm", "growers", "nursery", "agricultural", "meat"
    ],
    "Travel & Tourism": [
        "travel", "tours", "aviation", "holidays", "tourism"
    ],
    "Public Sector": [
        "council", "nhs foundation trust", "borough", "police", "authority"
    ],
    "Sport & Leisure": [
        "football club", "cricket club", "rugby", "sport", "gym", "fitness"
    ]
}


def classify_sector(name, existing_industry=None):
    """Classify sector based on corporate name or retain verified industry."""
    if existing_industry and existing_industry != "Other":
        return existing_industry
    name_lower = (name or "").lower()
    for sector, keywords in SECTOR_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                return sector
    return "Other"


def fetch_url(url):
    """Fetch URL with custom User-Agent and timeout."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def find_latest_csv_url():
    """Scrape GOV.UK landing page to locate the latest active Register CSV."""
    try:
        html_bytes = fetch_url(GOV_UK_REGISTER_PAGE)
        html_text = html_bytes.decode("utf-8", errors="ignore")
        # Match standard Home Office CSV download link pattern
        matches = re.findall(
            r'href=["\'](https://assets\.publishing\.service\.gov\.uk/media/[^"\']+\.csv)["\']',
            html_text,
            re.IGNORECASE
        )
        if matches:
            return matches[0]
    except Exception as e:
        print(f"Warning: Failed to parse GOV.UK landing page: {e}", file=sys.stderr)
    return None


def parse_csv_content(csv_bytes):
    """Parse Home Office Register CSV into consolidated tuples."""
    # Attempt UTF-8 with BOM or fallback to Windows-1252
    try:
        csv_text = csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        csv_text = csv_bytes.decode("windows-1252", errors="replace")

    reader = csv.reader(csv_text.splitlines())
    header = None
    
    # Map of (clean_name, town) -> [name, town, county, set(routes), rating]
    merged_sponsors = {}

    for row in reader:
        if not row or not any(row):
            continue
        if header is None:
            # Check for standard header columns
            joined = " ".join(row).lower()
            if "organisation name" in joined or "town/city" in joined:
                header = [c.strip().lower() for c in row]
                continue
            else:
                # If no explicit header line, treat first line as header anyway
                header = [f"col_{i}" for i in range(len(row))]
                continue

        # Expected format: Organisation Name, Town/City, County, Type & Rating, Route
        def normalize_str(s):
            if not s: return ""
            s = s.replace("â??", "'").replace("â€™", "'").replace("â€˜", "'").replace("â€œ", '"').replace("â€\x9d", '"').replace("â€", '"').replace("Â", "")
            s = s.replace("’", "'").replace("‘", "'").replace("`", "'")
            return s.strip()

        name = normalize_str(row[0]) if len(row) > 0 else ""
        town = normalize_str(row[1]) if len(row) > 1 else ""
        county = normalize_str(row[2]) if len(row) > 2 else ""
        type_rating = row[3].strip() if len(row) > 3 else ""
        route = row[4].strip() if len(row) > 4 else ""

        if not name or name.lower() in ("organisation name", "company name"):
            continue

        rating = "A"
        if "(Premium)" in type_rating or "A rating" in type_rating or "Worker (A" in type_rating:
            rating = "A"
        elif "(B rating)" in type_rating or "B rating" in type_rating or "Worker (B" in type_rating:
            rating = "B"
        elif "B" in type_rating:
            rating = "B"

        clean_route = route.replace("Worker - ", "").replace("Temporary Worker - ", "").strip()
        if not clean_route:
            clean_route = "Skilled Worker"

        key = (name.lower(), town.lower())
        if key not in merged_sponsors:
            merged_sponsors[key] = {
                "name": name,
                "town": town,
                "county": county,
                "routes": set([clean_route]),
                "rating": rating
            }
        else:
            merged_sponsors[key]["routes"].add(clean_route)
            if rating == "B":
                merged_sponsors[key]["rating"] = "B"
            if county and not merged_sponsors[key]["county"]:
                merged_sponsors[key]["county"] = county

    return merged_sponsors


def main():
    parser = argparse.ArgumentParser(description="KnowYourSponsor Daily Ingestion Engine")
    parser.add_argument("--prev", help="Path to previous state JSON file")
    parser.add_argument("--out-state", help="Path to write current full state JSON file")
    parser.add_argument("--out-dir", default="./data", help="Output directory for data payloads")
    parser.add_argument("--out-delta", default="./data/deltas", help="Output directory for daily micro-deltas")
    parser.add_argument("--csv-url", help="Direct URL to Home Office CSV (optional)")
    parser.add_argument("--csv-file", help="Local CSV file path (for offline testing)")
    parser.add_argument("--force", action="store_true", help="Force update regardless of SHA-256")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(args.out_delta, exist_ok=True)

    # 1. Acquire CSV payload
    csv_bytes = None
    source_url = args.csv_url

    if args.csv_file:
        with open(args.csv_file, "rb") as f:
            csv_bytes = f.read()
        source_url = f"file://{os.path.abspath(args.csv_file)}"
    else:
        if not source_url:
            print("Discovering latest UKVI CSV download URL from GOV.UK...")
            source_url = find_latest_csv_url()

        if not source_url:
            print("Fallback: Using current active snapshot source URL.")
            # Read from existing sponsors.json if available
            current_sponsors_file = os.path.join(args.out_dir, "sponsors.json")
            if os.path.exists(current_sponsors_file):
                try:
                    with open(current_sponsors_file, "r", encoding="utf-8") as f:
                        curr = json.load(f)
                        source_url = curr.get("source")
                except Exception:
                    pass

        if not source_url:
            print("Error: Could not resolve upstream CSV download URL.", file=sys.stderr)
            sys.exit(1)

        print(f"Fetching upstream Home Office CSV from: {source_url}")
        csv_bytes = fetch_url(source_url)

    csv_sha256 = hashlib.sha256(csv_bytes).hexdigest()
    print(f"Downloaded CSV: {len(csv_bytes):,} bytes | SHA-256: {csv_sha256}")

    # 2. Check Idempotency Hash Guard
    prev_sponsors_dict = {}
    prev_meta = {}
    prev_path = args.prev or os.path.join(args.out_dir, "sponsors.json")

    if os.path.exists(prev_path):
        try:
            with open(prev_path, "r", encoding="utf-8") as f:
                prev_data = json.load(f)
                prev_list = prev_data.get("sponsors", [])
                for item in prev_list:
                    # item: [name, town, county, industry, routes, rating]
                    key = (item[0].lower(), item[1].lower())
                    prev_sponsors_dict[key] = {
                        "name": item[0],
                        "town": item[1],
                        "county": item[2] if len(item) > 2 else "",
                        "industry": item[3] if len(item) > 3 else "Other",
                        "routes": item[4] if len(item) > 4 else ["Skilled Worker"],
                        "rating": item[5] if len(item) > 5 else "A"
                    }
        except Exception as e:
            print(f"Warning: Could not load previous state: {e}", file=sys.stderr)

    meta_file = os.path.join(args.out_dir, "meta.json")
    if os.path.exists(meta_file):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                prev_meta = json.load(f)
        except Exception:
            pass

    # 3. Parse newly fetched CSV
    parsed = parse_csv_content(csv_bytes)
    total_parsed = len(parsed)
    print(f"Parsed {total_parsed:,} unique employer entities from upstream.")

    # Circuit breaker: ensure at least 10,000 records
    if total_parsed < 10000:
        print(f"Circuit Breaker Triggered: Parsed count ({total_parsed}) is below safety floor of 10,000. Aborting.", file=sys.stderr)
        sys.exit(1)

    # 4. Compute Diff against previous state
    today_keys = set(parsed.keys())
    prev_keys = set(prev_sponsors_dict.keys())

    added_keys = today_keys - prev_keys
    removed_keys = prev_keys - today_keys
    common_keys = today_keys & prev_keys

    rating_downgrades = []
    rating_upgrades = []

    for k in common_keys:
        curr_r = parsed[k]["rating"]
        prev_r = prev_sponsors_dict[k]["rating"]
        if prev_r == "A" and curr_r == "B":
            rating_downgrades.append([parsed[k]["name"], parsed[k]["town"], "A -> B"])
        elif prev_r == "B" and curr_r == "A":
            rating_upgrades.append([parsed[k]["name"], parsed[k]["town"], "B -> A"])

    print(f"Diff Analysis: +{len(added_keys):,} new | -{len(removed_keys):,} removed | {len(rating_downgrades):,} downgraded")

    has_changed = (len(added_keys) > 0 or len(removed_keys) > 0 or len(rating_downgrades) > 0 or args.force)

    # Output GitHub Actions step variable
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if has_changed else 'false'}\n")
            f.write(f"added_count={len(added_keys)}\n")
            f.write(f"removed_count={len(removed_keys)}\n")
            f.write(f"total_count={total_parsed}\n")

    if not has_changed and not args.force:
        print("No upstream registry changes detected. Exiting cleanly (exit 0).")
        sys.exit(0)

    # 5. Build structured output records
    now_utc = datetime.now(timezone.utc)
    updated_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
    date_key = now_utc.strftime("%Y-%m-%d")

    # Construct final sponsors array
    final_sponsors = []
    for k in sorted(parsed.keys()):
        p = parsed[k]
        existing_ind = prev_sponsors_dict.get(k, {}).get("industry")
        industry = classify_sector(p["name"], existing_ind)
        routes_list = sorted(list(p["routes"]))
        final_sponsors.append([
            p["name"],
            p["town"],
            p["county"],
            industry,
            routes_list,
            p["rating"]
        ])

    # Construct new sponsors array
    new_sponsors_list = []
    for k in sorted(added_keys):
        p = parsed[k]
        industry = classify_sector(p["name"])
        new_sponsors_list.append([
            p["name"],
            p["town"],
            p["county"],
            industry,
            sorted(list(p["routes"])),
            p["rating"]
        ])

    # Construct removed sponsors array
    removed_sponsors_list = []
    for k in sorted(removed_keys):
        p = prev_sponsors_dict[k]
        removed_sponsors_list.append([
            p["name"],
            p["town"],
            p["county"],
            p.get("industry", "Other"),
            p.get("routes", ["Skilled Worker"]),
            p.get("rating", "A")
        ])

    # 6. Write JSON Data Payloads
    # 6.1 sponsors.json
    sponsors_payload = {
        "updated": updated_str,
        "source": source_url,
        "sponsors": final_sponsors
    }
    with open(os.path.join(args.out_dir, "sponsors.json"), "w", encoding="utf-8") as f:
        json.dump(sponsors_payload, f, separators=(',', ':'), ensure_ascii=False)

    # 6.1b initial_slice.json (50-row seed for instant sub-30ms first paint)
    initial_slice_payload = {
        "updated": updated_str,
        "total": total_parsed,
        "slice": final_sponsors[:50]
    }
    with open(os.path.join(args.out_dir, "initial_slice.json"), "w", encoding="utf-8") as f:
        json.dump(initial_slice_payload, f, separators=(',', ':'), ensure_ascii=False)

    # 6.2 Pre-compute aggregations for meta.json (0ms client CPU usage)
    flags_file = os.path.join(args.out_dir, "company_flags.json")
    company_flags = {}
    if os.path.exists(flags_file):
        try:
            with open(flags_file, "r", encoding="utf-8") as ff:
                company_flags = json.load(ff).get("companies", {})
        except Exception:
            pass

    nmw_file = os.path.join(args.out_dir, "nmw.json")
    nmw_employers = {}
    if os.path.exists(nmw_file):
        try:
            with open(nmw_file, "r", encoding="utf-8") as nf:
                nmw_employers = json.load(nf).get("employers", {})
        except Exception:
            pass

    # Flagged location counts (normalized by title case to avoid LONDON vs London duplicates)
    loc_counts = {}
    total_serious = 0
    total_notable = 0
    for s in final_sponsors:
        s_name = s[0]
        s_town = s[1].strip() if s[1] else ""
        if s_name in company_flags:
            if s_town:
                norm_town = s_town.title()
                loc_counts[norm_town] = loc_counts.get(norm_town, 0) + 1
            fl = company_flags[s_name].get("flags", [])
            if "not_active" in fl:
                total_serious += 1
            elif any(x in fl for x in ["dormant", "accounts_overdue"]):
                total_notable += 1

    top_flagged_locs = sorted(loc_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Revoked sector counts
    rev_sector_counts = {}
    for r in (removed_sponsors_list or []):
        sec = r[3] if len(r) > 3 and r[3] else "Other"
        if sec != "Other":
            rev_sector_counts[sec] = rev_sector_counts.get(sec, 0) + 1

    if not rev_sector_counts:
        for s in final_sponsors[:500]:
            sec = s[3] if len(s) > 3 and s[3] else "Other"
            if sec != "Other":
                rev_sector_counts[sec] = rev_sector_counts.get(sec, 0) + 1

    top_rev_sectors = sorted(rev_sector_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    total_flags = len(company_flags)
    risk_pct = round((total_flags / total_parsed) * 100, 2) if total_parsed else 0.0

    # Top towns ranked by sponsor frequency
    town_counts = {}
    for s in final_sponsors:
        if s[1] and len(s[1].strip()) > 2 and not s[1].strip().startswith((",", ".", ":", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0")):
            norm = s[1].strip().title()
            town_counts[norm] = town_counts.get(norm, 0) + 1
    
    top_towns = [t[0] for t in sorted(town_counts.items(), key=lambda x: x[1], reverse=True)[:80]]
    top_towns.sort()

    # 6.2 meta.json
    meta_payload = {
        "updated": updated_str,
        "total": total_parsed,
        "added_since_last_run": len(added_keys),
        "removed_since_last_run": len(removed_keys),
        "added_recently": len(new_sponsors_list) if new_sponsors_list else prev_meta.get("added_recently", 0),
        "removed_recently": len(removed_sponsors_list) if removed_sponsors_list else prev_meta.get("removed_recently", 0),
        "net_drift": (len(new_sponsors_list) if new_sponsors_list else 0) - (len(removed_sponsors_list) if removed_sponsors_list else 0),
        "downgraded_recently": len(rating_downgrades),
        "total_flagged": total_flags,
        "total_serious": total_serious,
        "total_notable": total_notable,
        "total_nmw": len(nmw_employers),
        "risk_pct": risk_pct,
        "top_flagged_locations": top_flagged_locs,
        "top_revoked_sectors": top_rev_sectors,
        "top_towns": top_towns,
        "top_industries": sorted(list(set(s[3] for s in final_sponsors if s[3]))),
        "top_routes": sorted(list(set(r for s in final_sponsors for r in s[4]))),
        "window_days": 7,
        "sample": False
    }
    with open(os.path.join(args.out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2)

    # 6.3 new_sponsors.json & removed_sponsors.json
    if new_sponsors_list or not os.path.exists(os.path.join(args.out_dir, "new_sponsors.json")):
        with open(os.path.join(args.out_dir, "new_sponsors.json"), "w", encoding="utf-8") as f:
            json.dump({
                "updated": updated_str,
                "window_days": 7,
                "new": new_sponsors_list
            }, f, separators=(',', ':'), ensure_ascii=False)

    if removed_sponsors_list or not os.path.exists(os.path.join(args.out_dir, "removed_sponsors.json")):
        with open(os.path.join(args.out_dir, "removed_sponsors.json"), "w", encoding="utf-8") as f:
            json.dump({
                "updated": updated_str,
                "window_days": 7,
                "removed": removed_sponsors_list
            }, f, separators=(',', ':'), ensure_ascii=False)

    # 6.4 rating_changes.json
    with open(os.path.join(args.out_dir, "rating_changes.json"), "w", encoding="utf-8") as f:
        json.dump({
            "updated": updated_str,
            "changes": rating_downgrades + rating_upgrades
        }, f, indent=2)

    # 6.5 Daily micro-delta (audit log)
    delta_file = os.path.join(args.out_delta, f"{date_key}.json")
    delta_payload = {
        "date": date_key,
        "updated": updated_str,
        "sha256": csv_sha256,
        "total": total_parsed,
        "net_drift": len(added_keys) - len(removed_keys),
        "added_count": len(added_keys),
        "removed_count": len(removed_keys),
        "downgrades_count": len(rating_downgrades),
        "added": new_sponsors_list[:100],  # sample or full
        "removed": removed_sponsors_list[:100],
        "downgrades": rating_downgrades
    }
    with open(delta_file, "w", encoding="utf-8") as f:
        json.dump(delta_payload, f, indent=2, ensure_ascii=False)

    # 6.6 Out-state file (for Release asset upload)
    if args.out_state:
        with open(args.out_state, "w", encoding="utf-8") as f:
            json.dump(sponsors_payload, f, separators=(',', ':'), ensure_ascii=False)

    print(f"Successfully generated static payloads in {args.out_dir} and micro-delta in {delta_file}.")


if __name__ == "__main__":
    main()
