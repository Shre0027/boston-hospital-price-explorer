"""Demo: pull monthly US import value and duties (Census international trade API) for a few countries,
and smartphone imports (HS 851713) by country. Writes tariff_demo/*.csv."""
import csv, json, os, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path
OUT = Path(__file__).parent
BASE = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
COUNTRIES = {"5700": "China", "5520": "Vietnam", "5330": "India", "2010": "Mexico", "1220": "Canada", "4280": "Germany", "5490": "Thailand", "5800": "Taiwan"}

KEY = os.environ.get("CENSUS_API_KEY", "").strip()   # free key, stored as a GitHub Actions secret; never printed

def get(params):
    if not KEY:
        raise SystemExit("::error::CENSUS_API_KEY secret is not set")
    url = BASE + "?" + urllib.parse.urlencode({**params, "key": KEY}, safe=",+:")
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "tariff-demo"}), timeout=120) as r:
                body = r.read().decode()
            if not body.strip():
                return []
            try:
                return json.loads(body)
            except ValueError:
                print(f"::warning::Not JSON ({len(body)} chars): {body[:400]!r}")
                time.sleep(3 * (i + 1))
        except urllib.error.HTTPError as e:
            print(f"::warning::HTTP {e.code}: {e.read().decode()[:400]!r} for {url.split('&key=')[0][:160]}"); time.sleep(3 * (i + 1))
        except Exception as e:
            print(f"::warning::{e} for {url.split('&key=')[0][:160]}"); time.sleep(5 * (i + 1))
    raise SystemExit(f"::error::failed {url.split('&key=')[0]}")

def main():
    # Save the official variable list first, so field names can be checked
    with urllib.request.urlopen(BASE + "/variables.json", timeout=60) as r:
        v = json.loads(r.read().decode())["variables"]
    (OUT / "variables.txt").write_text("\n".join(f"{k}: {v[k].get('label','')}" for k in sorted(v)))
    print("::notice::Variables: " + ", ".join(sorted(k for k in v if k.endswith("_MO") or k.startswith(("CTY", "COMM", "I_COMM", "time"))))[:900])
    rows = []
    for code, name in COUNTRIES.items():
        data = get({"get": "CTY_CODE,CTY_NAME,GEN_VAL_MO,CON_VAL_MO,CAL_DUT_MO,DUT_VAL_MO", "time": "from 2024-01", "COMM_LVL": "HS2", "CTY_CODE": code})
        hdr, body = data[0], data[1:]
        agg = {}
        for r in body:
            d = dict(zip(hdr, r)); t = d["time"]
            a = agg.setdefault(t, [0.0, 0.0, 0.0, 0.0])
            for k, f in enumerate(["GEN_VAL_MO", "CON_VAL_MO", "CAL_DUT_MO", "DUT_VAL_MO"]):
                a[k] += float(d.get(f) or 0)
        for t, a in sorted(agg.items()):
            rows.append({"month": t, "country": name, "general_imports": a[0], "consumption_imports": a[1], "calculated_duty": a[2], "dutiable_value": a[3]})
        print(f"::notice::{name}: {len(agg)} months, latest {max(agg)}")
    with open(OUT / "country_month.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    # all countries combined (world): no CTY_CODE filter, HS2 level, summed
    data = get({"get": "CTY_CODE,GEN_VAL_MO,CON_VAL_MO,CAL_DUT_MO", "time": "from 2024-01", "COMM_LVL": "HS2"})
    hdr, body = data[0], data[1:]
    agg = {}
    for r in body:
        d = dict(zip(hdr, r))
        if d["CTY_CODE"] in ("-", "", "0000") or not d["CTY_CODE"].isdigit() or len(d["CTY_CODE"]) != 4 or d["CTY_CODE"].startswith(("0", "00")):
            continue  # skip totals and regional groupings (codes starting 0)
        a = agg.setdefault(d["time"], [0.0, 0.0, 0.0])
        for k, fld in enumerate(["GEN_VAL_MO", "CON_VAL_MO", "CAL_DUT_MO"]):
            a[k] += float(d.get(fld) or 0)
    with open(OUT / "world_month.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["month", "general_imports", "consumption_imports", "calculated_duty"])
        for t, a in sorted(agg.items()): w.writerow([t, *a])
    print(f"::notice::World: {len(agg)} months")
    # smartphones HS 851713 by country
    data = get({"get": "CTY_CODE,CTY_NAME,GEN_VAL_MO,CAL_DUT_MO", "time": "from 2024-01", "COMM_LVL": "HS6", "I_COMMODITY": "851713"})
    hdr, body = data[0], data[1:]
    with open(OUT / "smartphones.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["month", "cty_code", "country", "general_imports", "calculated_duty"])
        for r in body:
            d = dict(zip(hdr, r))
            if d["CTY_CODE"].isdigit() and len(d["CTY_CODE"]) == 4 and not d["CTY_CODE"].startswith("0"):
                w.writerow([d["time"], d["CTY_CODE"], d["CTY_NAME"], d["GEN_VAL_MO"], d["CAL_DUT_MO"]])
    print(f"::notice::Smartphones: {len(body)} rows")

if __name__ == "__main__":
    main()
