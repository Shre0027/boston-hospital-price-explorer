"""
Build the dashboard website from the combined price table.

Reads:  data/combined/prices_clean.csv, data/processed/*_profile.json, data/quality/*.csv,
        config/hospitals.json, config/procedures.json, config/data_access.json
Writes: site/index.html    the scroll-driven story (from templates/story.html)
        site/explore.html  the full dashboard (from templates/dashboard.html)
        Both get the same small summary of the data embedded, so each page works as a single
        file with no server.

What goes into the summary:
  - per procedure and hospital: cash price, sticker price (gross charge), the typical commercial price
    (median and range across commercial plans; shown only with at least 3 plan prices), and the same
    for each major insurer
  - per hospital: a price index (same method as sql/05), CMS star rating, file facts and access findings
Only unflagged rows without billing modifiers are used for price comparisons
(see docs/decision-log.md for why).

Usage:
  python scripts/build_site.py
"""

import csv
import json
import math
import statistics
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Insurers offered in the dashboard's "who's paying" menu (commercial plans only)
MENU_INSURERS = [
    "Blue Cross Blue Shield", "Harvard Pilgrim", "Tufts Health Plan", "Aetna",
    "UnitedHealthcare", "Cigna", "Mass General Brigham Health Plan",
]
MIN_PLANS = 3          # a "typical" commercial price needs at least this many plan prices
MIN_HOSPITALS = 8      # price index: only procedures listed by at least this many hospitals
MIN_PROCEDURES = 8     # price index: only hospitals with at least this many such procedures


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


def avg_ranks(values):
    """Ranks starting at 1, with ties sharing their average rank."""
    order = sorted(values)
    return [(order.index(v) + 1 + order.index(v) + order.count(v)) / 2 for v in values]


def build_map(hospitals):
    """Project the Census town shapes and geocoded hospitals into SVG coordinates for the story's map.
    Returns None if data/geo hasn't been fetched yet (scripts/fetch_geo.py)."""
    tp, hp = ROOT / "data/geo/towns.json", ROOT / "data/geo/hospitals.json"
    if not (tp.exists() and hp.exists()):
        return None
    towns, pts = json.loads(tp.read_text())["towns"], json.loads(hp.read_text())
    lats = [pts[h["id"]]["lat"] for h in hospitals if h["id"] in pts]
    lons = [pts[h["id"]]["lon"] for h in hospitals if h["id"] in pts]
    pad = 0.035
    lon0, lon1, lat0, lat1 = min(lons) - pad * 1.3, max(lons) + pad * 1.3, min(lats) - pad, max(lats) + pad
    kx = math.cos(math.radians((lat0 + lat1) / 2))
    W = 1000
    scale = W / ((lon1 - lon0) * kx)
    Hh = round((lat1 - lat0) * scale)
    xy = lambda lon, lat: (round((lon - lon0) * kx * scale, 1), round((lat1 - lat) * scale, 1))

    def ring_path(ring):
        p = [xy(*c) for c in ring]
        return "M" + "L".join(f"{x:g},{y:g}" for x, y in p) + "Z"

    shapes, labels = [], []
    for t in towns:
        g = t["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"] if g["type"] == "MultiPolygon" else []
        d = "".join(ring_path(r) for poly in polys for r in poly)
        if d:
            shapes.append({"n": t["name"], "d": d})
    host_towns = {"Boston", "Cambridge", "Quincy", "Somerville", "Brookline"}   # hospital labels already name the other places
    for t in towns:
        if t["name"] in host_towns:
            x, y = xy(*t["label_at"])
            if 0 <= x <= W and 0 <= y <= Hh:
                labels.append({"n": t["name"].replace(" Town", ""), "x": x, "y": y})
    return {"w": W, "h": Hh, "towns": shapes, "labels": labels,
            "hosp": {k: xy(v["lon"], v["lat"]) for k, v in pts.items()},
            "km_per_unit": 1 / scale * 111.32}


def distances(hospitals):
    hp = ROOT / "data/geo/hospitals.json"
    if not hp.exists():
        return None
    pts = json.loads(hp.read_text())
    ids = [h["id"] for h in hospitals if h["id"] in pts]
    return {a: {b: round(km_between(pts[a], pts[b]), 2) for b in ids if b != a} for a in ids}


def km_between(a, b):
    """Great-circle distance in km between two {lat, lon} points."""
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    return 6371 * 2 * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))


def main():
    hospitals = load("config/hospitals.json")
    procedures = load("config/procedures.json")
    access = load("config/data_access.json")

    cash = defaultdict(list)
    gross = defaultdict(list)
    commercial = defaultdict(list)
    by_insurer = defaultdict(list)
    rows_total = defaultdict(int)
    rows_flagged = defaultdict(int)
    insurers_listed = defaultdict(set)
    insurer_names = set()
    # Every published dollar price, for the story's background (log10 position 0–999, times 10, plus category)
    cats = sorted({p["category"] for p in procedures})
    cat_of = {p["cpt"]: cats.index(p["category"]) for p in procedures}
    dots = []
    # Each hospital's own line-item wording for the story's receipt (brain MRI)
    receipt_cpt = "70551"
    receipt_desc = {}

    with open(ROOT / "data/combined/prices_clean.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            hid = r["hospital_id"]
            rows_total[hid] += 1
            if r["payer_raw"]:
                insurer_names.add(r["payer_raw"])
            if r["cpt"] == receipt_cpt and r["hospital_description"]:
                receipt_desc.setdefault(hid, r["hospital_description"])
            v = next((float(r[k]) for k in ("comparison_price", "cash_price", "gross_charge") if r[k]), None)
            if v and v > 0 and r["cpt"] in cat_of:
                q = round((math.log10(v) + 2) / 7 * 999)        # $0.01 → 0, $100,000 → 999
                dots.append(max(0, min(999, q)) * 10 + cat_of[r["cpt"]])
            if r["flag"]:
                rows_flagged[hid] += 1
            if r["market"] == "Commercial" and r["insurer"] not in ("", "Other") and r["cpt"] != "419":
                insurers_listed[hid].add(r["insurer"])
            if r["modifiers"]:
                continue
            key = (r["cpt"], hid)
            if r["cash_price"]:
                cash[key].append(float(r["cash_price"]))
            if r["gross_charge"]:
                gross[key].append(float(r["gross_charge"]))
            if r["market"] == "Commercial" and r["comparison_price"] and not r["flag"]:
                price = float(r["comparison_price"])
                commercial[key].append(price)
                if r["insurer"] in MENU_INSURERS:
                    by_insurer[key + (r["insurer"],)].append(price)

    prices = {}
    for p in procedures:
        prices[p["cpt"]] = {}
        for h in hospitals:
            key = (p["cpt"], h["id"])
            typical = summarize(commercial[key])
            prices[p["cpt"]][h["id"]] = {
                "cash": round(statistics.median(cash[key]), 2) if cash[key] else None,
                "gross": round(statistics.median(gross[key]), 2) if gross[key] else None,
                "commercial": typical if typical and typical["n"] >= MIN_PLANS else None,
                "few_plans": typical["n"] if typical and typical["n"] < MIN_PLANS else None,
                "insurers": {i: s for i in MENU_INSURERS if (s := summarize(by_insurer[key + (i,)]))},
            }

    # Price index (same method as sql/05): each hospital's typical price / the median across hospitals,
    # per procedure; a hospital's index is the median of those ratios.
    ratios = defaultdict(list)
    for p in procedures:
        listed = {h["id"]: prices[p["cpt"]][h["id"]]["commercial"]["median"]
                  for h in hospitals if prices[p["cpt"]][h["id"]]["commercial"]}
        if len(listed) < MIN_HOSPITALS:
            continue
        mid = statistics.median(listed.values())
        for hid, v in listed.items():
            ratios[hid].append(v / mid)
    price_index = {hid: round(statistics.median(v), 2) for hid, v in ratios.items() if len(v) >= MIN_PROCEDURES}

    stars = {}
    qpath = ROOT / "data/quality/ma_hospital_general_information.csv"
    qsource = {}
    if qpath.exists():
        by_ccn = {r["Facility ID"]: r for r in csv.DictReader(open(qpath, encoding="utf-8"))}
        for h in hospitals:
            r = by_ccn.get(h.get("ccn", ""))
            stars[h["id"]] = int(r["Hospital overall rating"]) if r and r["Hospital overall rating"].isdigit() else None
        qsource = load("data/quality/source.json")

    rated = [(price_index[h], stars[h]) for h in price_index if stars.get(h)]
    rank_corr = None
    if len(rated) >= 5:
        rank_corr = round(statistics.correlation(avg_ranks([x for x, _ in rated]), avg_ranks([y for _, y in rated])), 2)

    hospital_info = []
    for h in hospitals:
        profile = load(f"data/processed/{h['id']}_profile.json")
        a = access["hospitals"].get(h["id"], {})
        hospital_info.append({
            "id": h["id"],
            "name": h["name"],
            "short": h.get("short", h["name"]),
            "system": h.get("system", ""),
            "last_updated": profile["hospital_metadata"].get("last_updated_on", ""),
            "rows_in_file": profile["total_data_rows"],
            "procedures_found": len(procedures) - len(profile["procedures_missing"]),
            "file_type": profile.get("file_type", "csv"),
            "collected": profile.get("collected", "downloaded automatically"),
            "insurers_listed": len(insurers_listed[h["id"]]),
            "pct_set_aside": round(100 * rows_flagged[h["id"]] / rows_total[h["id"]]) if rows_total[h["id"]] else 0,
            "price_index": price_index.get(h["id"]),
            "stars": stars.get(h["id"]),
            "link_list": a.get("link_list"),
            "download": a.get("download"),
            "notes": a.get("notes", []),
        })

    data = {
        "built_on": time.strftime("%Y-%m-%d", time.gmtime()),
        "access_checked_on": access["checked_on"],
        "quality_as_of": qsource.get("catalog_modified"),
        "hospitals": hospital_info,
        "procedures": procedures,
        "insurers": MENU_INSURERS,
        "prices": prices,
        "rank_correlation": rank_corr,
        "rated_hospitals": len(rated),
        "min_plans": MIN_PLANS,
        "total_prices": sum(rows_total.values()),
        "insurer_names": len(insurer_names),
        "map": build_map(hospitals),
        "distances_km": distances(hospitals),
        "dots": dots,
        "receipt": {"cpt": receipt_cpt, "desc": receipt_desc},
        "dot_categories": cats,
        "sql_queries": len([q for q in (ROOT / "sql").glob("[0-9][0-9]_*.sql") if not q.name.startswith("00_")]),
    }

    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    for src, out in (("story.html", "index.html"), ("dashboard.html", "explore.html")):
        template = (ROOT / "templates" / src).read_text(encoding="utf-8")
        assert "/*__DATA__*/null" in template, f"{src} has no data placeholder"
        html = template.replace("/*__DATA__*/null", payload)
        (ROOT / "site" / out).write_text(html, encoding="utf-8")
        print(f"Wrote site/{out} ({len(html) / 1000:.0f} KB)")
    print(f"Data {len(payload) / 1000:.0f} KB; {len(price_index)} hospitals indexed, rank correlation {rank_corr}")


if __name__ == "__main__":
    main()
