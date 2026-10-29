"""
Build the dashboard website from the combined price table.

Reads:  data/combined/prices_clean.csv, data/processed/*_profile.json,
        config/hospitals.json, config/procedures.json, config/data_access.json
Writes: site/index.html  (site/template.html with a small summary of the data embedded,
        so the page works as a single file with no server)

What goes into the summary, per procedure and hospital:
  - cash price (no insurance) and sticker price (gross charge)
  - "commercial, typical": median and range of the comparison price across commercial plans
  - the same for each major insurer
Only unflagged rows without billing modifiers are used for price comparisons
(see docs/decision-log.md for why).

Usage:
  python scripts/build_site.py
"""

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Insurers offered in the dashboard's "who's paying" menu (commercial plans only)
MENU_INSURERS = [
    "Blue Cross Blue Shield", "Harvard Pilgrim", "Tufts Health Plan", "Aetna",
    "UnitedHealthcare", "Cigna", "Mass General Brigham Health Plan",
]

SHORT_NAMES = {"mgh": "MGH", "bwh": "Brigham", "bmc": "BMC", "bidmc": "BIDMC", "tmc": "Tufts MC"}


def load(path):
    with open(ROOT / path, encoding="utf-8") as f:
        return json.load(f)


def summarize(values):
    if not values:
        return None
    return {
        "median": round(statistics.median(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "n": len(values),
    }


def main():
    hospitals = load("config/hospitals.json")
    procedures = load("config/procedures.json")
    access = load("config/data_access.json")

    cash = defaultdict(list)
    gross = defaultdict(list)
    commercial = defaultdict(list)
    by_insurer = defaultdict(list)
    insurer_names = defaultdict(set)

    with open(ROOT / "data/combined/prices_clean.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["modifiers"]:
                continue
            key = (r["cpt"], r["hospital_id"])
            if r["cash_price"]:
                cash[key].append(float(r["cash_price"]))
            if r["gross_charge"]:
                gross[key].append(float(r["gross_charge"]))
            if r["market"] == "Commercial" and r["comparison_price"] and not r["flag"]:
                price = float(r["comparison_price"])
                commercial[key].append(price)
                insurer_names[r["hospital_id"]].add(r["insurer"])
                if r["insurer"] in MENU_INSURERS:
                    by_insurer[key + (r["insurer"],)].append(price)

    prices = {}
    for p in procedures:
        prices[p["cpt"]] = {}
        for h in hospitals:
            key = (p["cpt"], h["id"])
            entry = {
                "cash": round(statistics.median(cash[key]), 2) if cash[key] else None,
                "gross": round(statistics.median(gross[key]), 2) if gross[key] else None,
                "commercial": summarize(commercial[key]),
                "insurers": {i: s for i in MENU_INSURERS if (s := summarize(by_insurer[key + (i,)]))},
            }
            prices[p["cpt"]][h["id"]] = entry

    hospital_info = []
    for h in hospitals:
        profile = load(f"data/processed/{h['id']}_profile.json")
        hospital_info.append({
            "id": h["id"],
            "name": h["name"],
            "short": SHORT_NAMES.get(h["id"], h["name"]),
            "system": h.get("system", ""),
            "last_updated": profile["hospital_metadata"].get("last_updated_on", ""),
            "rows_in_file": profile["total_data_rows"],
            "matched_rows": profile["matched_rows"],
            "procedures_found": len(procedures) - len(profile["procedures_missing"]),
            "file_type": profile.get("file_type", "csv"),
            "collected": profile.get("collected", "downloaded automatically"),
            "source_url": profile.get("source_url"),
            "access": access["hospitals"].get(h["id"], []),
        })

    data = {
        "built_on": access["checked_on"],
        "hospitals": hospital_info,
        "procedures": procedures,
        "insurers": MENU_INSURERS,
        "prices": prices,
        "total_prices": sum(1 for _ in open(ROOT / "data/combined/prices_clean.csv", encoding="utf-8")) - 1,
    }

    template = (ROOT / "site/template.html").read_text(encoding="utf-8")
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html = template.replace("/*__DATA__*/null", payload)
    (ROOT / "site/index.html").write_text(html, encoding="utf-8")
    print(f"Wrote site/index.html ({len(html) / 1000:.0f} KB, data {len(payload) / 1000:.0f} KB)")


if __name__ == "__main__":
    main()
