"""Demo data: US monthly imports and duties from the Census international trade API (imports/hs endpoint).

Writes:
  tariff_demo/country_month.csv  every country and country group, monthly from Jan 2024: general imports,
                                 imports for consumption, dutiable value and calculated duty
  tariff_demo/smartphones.csv    smartphone imports (HS 851713) by country, monthly
Notes learned from the API: requesting CTY_NAME together with COMM_LVL returns no content (HTTP 204),
so commodity queries leave names out; country totals come from a query without COMM_LVL.
The API key is read from the CENSUS_API_KEY Actions secret and never printed.
"""
import csv, json, os, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

OUT = Path(__file__).parent
BASE = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
KEY = os.environ.get("CENSUS_API_KEY", "").strip()


def get(params):
    if not KEY:
        raise SystemExit("::error::CENSUS_API_KEY secret is not set")
    q = urllib.parse.urlencode(params, safe=",+:")
    url = f"{BASE}?{q}&key={KEY}"
    shown = f"{BASE}?{q}"
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "tariff-demo"}), timeout=180) as r:
                body = r.read().decode()
                status = r.status
            if status == 204 or not body.strip():
                print(f"::warning::No content for {shown}")
                return []
            if body.lstrip().startswith("["):
                return json.loads(body)
            print(f"::warning::Not JSON for {shown}: {body[:150]!r}")
        except urllib.error.HTTPError as e:
            print(f"::warning::HTTP {e.code} for {shown}: {e.read().decode()[:150]!r}")
        except Exception as e:
            print(f"::warning::{e} for {shown}")
        time.sleep(5 * (i + 1))
    raise SystemExit(f"::error::Failed: {shown}")


def rows_of(data):
    if not data:
        return []
    hdr = data[0]
    return [dict(zip(hdr, r)) for r in data[1:]]


def main():
    rows = rows_of(get({"get": "CTY_CODE,CTY_NAME,GEN_VAL_MO,CON_VAL_MO,DUT_VAL_MO,CAL_DUT_MO", "time": "from 2024-01"}))
    if not rows:
        raise SystemExit("::error::No country data")
    with open(OUT / "country_month.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["month", "cty_code", "country", "general_imports", "consumption_imports", "dutiable_value", "calculated_duty"])
        for d in sorted(rows, key=lambda d: (d["time"], d["CTY_CODE"])):
            w.writerow([d["time"], d["CTY_CODE"], d["CTY_NAME"], d["GEN_VAL_MO"], d["CON_VAL_MO"], d["DUT_VAL_MO"], d["CAL_DUT_MO"]])
    months = sorted({d["time"] for d in rows})
    print(f"::notice::Country data: {len(rows)} rows, {len(months)} months, {months[0]} to {months[-1]}")
    names = {d["CTY_CODE"]: d["CTY_NAME"] for d in rows}

    ph = rows_of(get({"get": "CTY_CODE,GEN_VAL_MO,CAL_DUT_MO", "time": "from 2024-01", "COMM_LVL": "HS6", "I_COMMODITY": "851713"}))
    with open(OUT / "smartphones.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["month", "cty_code", "country", "general_imports", "calculated_duty"])
        for d in sorted(ph, key=lambda d: (d["time"], d["CTY_CODE"])):
            w.writerow([d["time"], d["CTY_CODE"], names.get(d["CTY_CODE"], ""), d["GEN_VAL_MO"], d["CAL_DUT_MO"]])
    print(f"::notice::Smartphones: {len(ph)} rows")


if __name__ == "__main__":
    main()
