"""
Fetch map data for the story's map step.

1. Hospital locations: each hospital's street address from CMS Hospital General Information
   (data/quality/ma_hospital_general_information.csv, matched by CMS Certification Number),
   geocoded with the US Census Bureau Geocoder (free, no key).
2. Town boundaries: US Census Bureau cartographic boundary file for Massachusetts county
   subdivisions (towns and cities, 1:500k, already clipped to the shoreline), cut to the
   Greater Boston area and simplified.

Writes: data/geo/hospitals.json, data/geo/towns.json, data/geo/source.json

Runs on GitHub Actions (.github/workflows/geo.yml), because it needs internet access.
Needs: pip install pyshp shapely

Usage:
  python scripts/fetch_geo.py
"""

import csv
import io
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import shapefile                      # pyshp
from shapely.geometry import box, mapping, shape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/geo"
GEOCODER = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
NOMINATIM = "https://nominatim.openstreetmap.org/search"   # fallback only; light use per its usage policy
TOWNS_URL = "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_25_cousub_500k.zip"
BBOX = (-71.36, 42.12, -70.82, 42.57)   # lon/lat box around the 18 hospitals, with margin
SIMPLIFY = 0.0012                        # degrees (about 100 m); keeps the file small


def get(url, data=None, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "boston-hospital-price-explorer"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:                       # network hiccup: retry, then give up loudly
            print(f"::warning::{url[:80]}... attempt {i + 1} failed: {e}")
            time.sleep(3 * (i + 1))
    raise SystemExit(f"::error::Could not fetch {url}")


def clean_street(street):
    """'736 CAMBRIDGE STREET, NEVINS BUILDING' -> '736 CAMBRIDGE STREET'; '41 & 45 MALL ROAD' -> '41 MALL ROAD'."""
    street = street.split(",")[0].strip()
    return re.sub(r"^(\d+)\s*&\s*\d+\s+", r"\1 ", street)


SUFFIX = {"STREET": "ST", "AVENUE": "AVE", "ROAD": "RD", "PLACE": "PL", "DRIVE": "DR", "BOULEVARD": "BLVD", "LANE": "LN"}


def street_key(street):
    """Street name without the house number, with suffixes abbreviated: '41 MALL ROAD' -> 'MALL RD'."""
    words = re.sub(r"[^A-Z0-9 ]", " ", street.upper()).split()
    words = [SUFFIX.get(w, w) for w in words if not w.isdigit()]
    return " ".join(words)


def census(address, street):
    """Census Geocoder matches whose street name equals the one asked for (it can fuzzy-match a different street)."""
    q = urllib.parse.urlencode({"address": address, "benchmark": "Public_AR_Current", "format": "json"})
    matches = json.loads(get(f"{GEOCODER}?{q}")).get("result", {}).get("addressMatches", [])
    want = street_key(street)
    good = [m for m in matches if street_key(m["matchedAddress"].split(",")[0]) == want]
    for m in matches:
        if m not in good:
            print(f"::warning::Rejected Census match '{m['matchedAddress']}' for '{address}' (different street)")
    return good


def nominatim(street, city, zipcode):
    q = urllib.parse.urlencode({"street": street, "city": city, "state": "MA", "postalcode": zipcode, "country": "USA", "format": "json", "limit": 3})
    res = json.loads(get(f"{NOMINATIM}?{q}"))
    want = street_key(street)
    for m in res:
        name = m.get("display_name", "").upper()
        if street_key(name.split(",")[1] if name.split(",")[0].strip().isdigit() else name.split(",")[0]) == want or want in street_key(name):
            return m
    return None


def geocode_hospitals():
    hospitals = json.loads((ROOT / "config/hospitals.json").read_text())
    by_ccn = {h["ccn"]: h for h in hospitals}
    rows = {}
    with open(ROOT / "data/quality/ma_hospital_general_information.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Facility ID"] in by_ccn:
                rows[r["Facility ID"]] = r
    out = {}
    for ccn, h in by_ccn.items():
        r = rows.get(ccn)
        if not r:
            raise SystemExit(f"::error::No CMS address for {h['id']} (CCN {ccn})")
        street = clean_street(r["Address"])
        address = f"{street}, {r['City/Town']}, {r['State']} {r['ZIP Code']}"
        matches = census(address, street) or census(f"{street}, {r['ZIP Code']}", street)
        if matches:
            m = matches[0]
            lat, lon, matched, src = m["coordinates"]["y"], m["coordinates"]["x"], m["matchedAddress"], "US Census Geocoder"
        else:
            time.sleep(1.1)
            m = nominatim(street, r["City/Town"], r["ZIP Code"])
            if not m:
                raise SystemExit(f"::error::No geocoder found {address} on the right street")
            lat, lon, matched, src = float(m["lat"]), float(m["lon"]), m["display_name"], "OpenStreetMap Nominatim"
        out[h["id"]] = {"lat": round(lat, 5), "lon": round(lon, 5), "cms_address": f"{r['Address']}, {r['City/Town']}",
                        "matched_address": matched, "geocoder": src}
        print(f"::notice::{h['id']}: {address} -> {matched} [{src}] ({out[h['id']]['lat']}, {out[h['id']]['lon']})")
        time.sleep(0.5)
    return out


def fetch_towns():
    z = zipfile.ZipFile(io.BytesIO(get(TOWNS_URL)))
    name = lambda ext: next(n for n in z.namelist() if n.endswith(ext))
    sf = shapefile.Reader(shp=io.BytesIO(z.read(name(".shp"))), dbf=io.BytesIO(z.read(name(".dbf"))),
                          shx=io.BytesIO(z.read(name(".shx"))))
    fields = [f[0] for f in sf.fields[1:]]
    clip = box(*BBOX)
    towns = []
    for rec, shp in zip(sf.records(), sf.shapes()):
        props = dict(zip(fields, rec))
        g = shape(shp.__geo_interface__)
        if not g.intersects(clip):
            continue
        g = g.intersection(clip).simplify(SIMPLIFY, preserve_topology=True)
        if g.is_empty:
            continue
        geo = json.loads(json.dumps(mapping(g)), parse_float=lambda x: round(float(x), 4))
        c = g.representative_point()
        towns.append({"name": props.get("NAME"), "geometry": geo, "label_at": [round(c.x, 4), round(c.y, 4)], "area": g.area})
    print(f"::notice::Kept {len(towns)} towns inside the map area")
    return towns


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hospitals = geocode_hospitals()
    towns = fetch_towns()
    (OUT / "hospitals.json").write_text(json.dumps(hospitals, indent=1))
    (OUT / "towns.json").write_text(json.dumps({"bbox": BBOX, "towns": towns}, separators=(",", ":")))
    (OUT / "source.json").write_text(json.dumps({
        "fetched_on": time.strftime("%Y-%m-%d", time.gmtime()),
        "hospital_addresses": "CMS Hospital General Information (data/quality), matched by CMS Certification Number",
        "geocoder": GEOCODER + " (benchmark Public_AR_Current); a match is accepted only if its street name equals the CMS address's. Fallback: " + NOMINATIM,
        "towns": TOWNS_URL, "bbox": BBOX, "simplify_degrees": SIMPLIFY,
        "note": "Cambridge Health Alliance's file covers three campuses; the map shows the CMS-listed main address (Cambridge Hospital).",
    }, indent=1))
    print("::notice::Wrote data/geo/hospitals.json, towns.json, source.json")


if __name__ == "__main__":
    main()
