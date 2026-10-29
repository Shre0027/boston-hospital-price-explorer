"""
Download CMS's hospital quality star ratings for Massachusetts.

Source: CMS Provider Data Catalog, "Hospital General Information" (dataset xubh-q36u), which includes
each hospital's CMS Certification Number (CCN) and its overall star rating (1-5, or "Not Available").

The current download link is read from the catalog's metadata API, so the script keeps working when
CMS publishes a new file. Falls back to a known file link if the API can't be reached.

Writes:
  data/quality/ma_hospital_general_information.csv   Massachusetts rows, selected columns
  data/quality/source.json                           where and when the data came from

Usage:
  python scripts/fetch_quality.py
"""

import csv
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_prices import USER_AGENT, body_stream  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "quality"
METASTORE = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/xubh-q36u"
FALLBACK = "https://data.cms.gov/provider-data/sites/default/files/resources/893c372430d9d71a1c52737d01239d47_1745467507/Hospital_General_Information.csv"
KEEP = ["Facility ID", "Facility Name", "Address", "City/Town", "State", "ZIP Code",
        "Hospital Type", "Hospital Ownership", "Emergency Services", "Hospital overall rating",
        "Hospital overall rating footnote"]


# A mirror of the same CMS dataset on HealthData.gov (HHS), used if data.cms.gov refuses the request
MIRROR = "https://healthdata.gov/api/views/n7m7-8qpq/rows.csv?accessType=DOWNLOAD"


def get(url, plain=False):
    # data.cms.gov is a public open-data API; "plain" sends a standard client header instead of our custom one
    headers = {"User-Agent": "python-urllib/3 (open-data research)" if plain else USER_AGENT, "Accept": "*/*"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return body_stream(resp).read()


def first_working(urls):
    """Try each (label, url, plain) in order; return (label, url, bytes) for the first that works."""
    errors = []
    for label, url, plain in urls:
        try:
            return label, url, get(url, plain)
        except Exception as e:
            errors.append(f"{label}: {e}")
            print(f"::warning::{label} failed ({e})")
    raise RuntimeError("All sources failed: " + "; ".join(errors))


def main():
    modified, url = None, FALLBACK
    try:
        meta = json.loads(first_working([("CMS catalog", METASTORE, False), ("CMS catalog (plain header)", METASTORE, True)])[2])
        modified = meta.get("modified")
        for d in meta.get("distribution", []):
            u = d.get("downloadURL") or d.get("data", {}).get("downloadURL")
            if u and u.lower().endswith(".csv"):
                url = u
                break
        print(f"::notice::CMS catalog: modified {modified}, file {url}")
    except Exception as e:
        print(f"::warning::Couldn't read the CMS catalog ({e}); using the fallback link")

    source, url, raw = first_working([
        ("CMS file", url, False), ("CMS file (plain header)", url, True), ("HealthData.gov mirror", MIRROR, True)])
    print(f"::notice::Downloaded from {source}")
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in KEEP if c not in reader.fieldnames]
    if missing:
        raise ValueError(f"Expected columns missing: {missing}. Columns: {reader.fieldnames}")
    rows = [{k: r[k] for k in KEEP} for r in reader if r["State"] == "MA"]
    if not rows:
        raise ValueError("No Massachusetts rows found")

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "ma_hospital_general_information.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KEEP)
        w.writeheader()
        w.writerows(rows)
    (OUT / "source.json").write_text(json.dumps({
        "dataset": "CMS Hospital General Information (xubh-q36u)",
        "catalog_modified": modified,
        "download_url": url,
        "source": source,
        "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "massachusetts_rows": len(rows),
    }, indent=2), encoding="utf-8")
    print(f"::notice::Saved {len(rows)} Massachusetts hospitals")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"::error::{type(e).__name__}: {e}")
        raise
