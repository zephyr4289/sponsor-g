#!/usr/bin/env python3
"""
KnowYourSponsor — Local Data Hydration Script
Downloads the latest sponsors.json and company_flags.json from production/release
if they are not present in the local working tree.
"""

import os
import sys
import urllib.request

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FILES = {
    "sponsors.json": "https://zephyr4289.github.io/sponsor-g/data/sponsors.json",
    "company_flags.json": "https://zephyr4289.github.io/sponsor-g/data/company_flags.json"
}

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    for filename, url in FILES.items():
        target_path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
            print(f"Downloading {filename} from {url}...")
            try:
                urllib.request.urlretrieve(url, target_path)
                size_mb = os.path.getsize(target_path) / (1024 * 1024)
                print(f"  -> Saved {target_path} ({size_mb:.2f} MB)")
            except Exception as e:
                print(f"  -> Error fetching {filename}: {e}", file=sys.stderr)
        else:
            size_mb = os.path.getsize(target_path) / (1024 * 1024)
            print(f"File {filename} already present locally ({size_mb:.2f} MB).")

if __name__ == "__main__":
    main()
