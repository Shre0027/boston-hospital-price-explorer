"""
Read hospitals' cms-hpt.txt files and save every location and price-file link found.

CMS requires each hospital website to publish a cms-hpt.txt file at its root
(for example https://www.example.org/cms-hpt.txt) listing each location's
price file (mrf-url). This script fetches those files for a list of websites
and writes what it finds to data/discovery.json, so we can pick the right
links for config/hospitals.json.

Usage:
  python scripts/discover.py bmc.org bidmc.org tuftsmedicalcenter.org
"""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_prices import USER_AGENT, body_stream  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, resp.geturl(), body_stream(resp).read().decode("utf-8", errors="replace")


def parse(text):
    locations, current = [], None
    for line in text.splitlines():
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "location-name":
            current = {"location-name": value}
            locations.append(current)
        elif key and current is not None:
            current[key] = value
    return locations


def main():
    results = []
    for site in sys.argv[1:]:
        site = site.strip().removeprefix("https://").removeprefix("http://").strip("/")
        for host in (f"www.{site}", site) if not site.startswith("www.") else (site,):
            url = f"https://{host}/cms-hpt.txt"
            entry = {"site": site, "url": url}
            try:
                status, final_url, text = fetch(url)
                entry.update(status=status, final_url=final_url)
                locs = parse(text)
                if locs:
                    entry["locations"] = locs
                    print(f"::notice::{url}: {len(locs)} locations")
                    results.append(entry)
                    break
                entry["problem"] = "not a cms-hpt.txt file: " + text[:150].replace("\n", " ")
            except (urllib.error.URLError, OSError, ValueError) as e:
                entry["problem"] = f"{type(e).__name__}: {e}"
            print(f"::warning::{url}: {entry['problem'][:200]}")
            results.append(entry)

    out = ROOT / "data" / "discovery.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "results": results}, indent=2))


if __name__ == "__main__":
    main()
