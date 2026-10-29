"""
Find the download links for the official Medicare rate files on cms.gov (run on GitHub Actions).

Looks at:
  - OPPS quarterly Addendum B (outpatient payment rates by HCPCS code)
  - Clinical Laboratory Fee Schedule (lab test rates)
  - IPPS final rule tables (hospital wage index by CMS Certification Number)
and saves every file link it finds to data/investigations/medicare_links.json.

Usage:
  python scripts/find_medicare_files.py
"""

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "opps_addendum_b_oct_2026": "https://www.cms.gov/medicare/payment/prospective-payment-systems/hospital-outpatient-pps/quarterly-addenda-updates/october-2026-addendum-b",
    "opps_addendum_b_jul_2026": "https://www.cms.gov/medicare/payment/prospective-payment-systems/hospital-outpatient-pps/quarterly-addenda-updates/july-2026-addendum-b",
    "clfs_files": "https://www.cms.gov/medicare/payment/fee-schedules/clinical-laboratory-fee-schedule-clfs/files",
    "ipps_fy2026_final": "https://www.cms.gov/medicare/payment/prospective-payment-systems/acute-inpatient-pps/fy-2026-ipps-final-rule-home-page",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (boston-hospital-price-explorer)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.geturl(), r.read().decode("utf-8", "replace")


def main():
    out = {}
    for key, url in PAGES.items():
        try:
            final, html = fetch(url)
        except Exception as e:
            print(f"::warning::{key}: {e}")
            out[key] = {"url": url, "error": str(e)}
            continue
        links = []
        for href, text in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
            text = re.sub(r"<[^>]+>|\s+", " ", text).strip()
            full = urllib.parse.urljoin(final, href)
            if re.search(r"\.(zip|xlsx?|csv|txt)(\?|$)", full, re.I) or re.search(r"table|addendum|clab|wage", text + full, re.I):
                links.append({"text": text[:140], "href": full})
        out[key] = {"url": final, "links": links}
        print(f"::notice::{key}: {len(links)} candidate links")
        for l in links[:15]:
            print(f"::notice::  {l['text'][:70]} -> {l['href']}")
    path = ROOT / "data/investigations/medicare_links.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
