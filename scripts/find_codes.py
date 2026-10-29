"""
Investigation helper: which billing codes does a hospital use for a given service?

Scans a hospital's full price file (downloaded fresh, or a local copy) and reports, for each
code family, which codes appear, how many rows each has, and an example description.
Used to find out why some procedures were "not listed" under the codes in config/procedures.json.

Writes data/investigations/<hospital>_codes.json

Usage:
  python scripts/find_codes.py --hospital mgh
  python scripts/find_codes.py --hospital tmc --local-file path/to/file.zip
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_prices import (CODE_COL, RAW_DIR, ROOT, csv_source, download, is_json_file,  # noqa: E402
                            json_rows, JSON_COLUMNS, load_json, resolve_mrf_url)

# Code families to check: the code we used, plus close relatives that hospitals might use instead
FAMILIES = {
    "ECG": {"codes": ["93000", "93005", "93010"], "note": "93000 = complete (with doctor's interpretation); 93005 = tracing only (hospital part); 93010 = interpretation only"},
    "Cataract surgery": {"codes": ["66982", "66983", "66984", "66987", "66988", "66989", "66991"], "note": "66984 = standard cataract removal with lens implant"},
    "Knee arthroscopy": {"codes": ["29870", "29871", "29873", "29874", "29875", "29876", "29877", "29879", "29880", "29881", "29882", "29888"], "note": "29880/29881 = meniscectomy (both/one side)"},
    "Gallbladder removal": {"codes": ["47562", "47563", "47564", "47600", "47605", "417", "418", "419"], "note": "47562-47564 = laparoscopic (outpatient CPT); 417-419 = laparoscopic cholecystectomy inpatient stay (MS-DRG)"},
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hospital", required=True)
    parser.add_argument("--local-file")
    args = parser.parse_args()

    if args.local_file:
        path = Path(args.local_file)
    else:
        hospitals = {h["id"]: h for h in load_json(ROOT / "config" / "hospitals.json")}
        url = resolve_mrf_url(hospitals[args.hospital])
        path = RAW_DIR / Path(url.split("?")[0]).name
        download(url, path)

    if is_json_file(path):
        header, rows = JSON_COLUMNS, json_rows(path)
    else:
        _, header, rows, _, _ = csv_source(path)
    lower = [h.lower() for h in header]
    code_idx = [i for i, h in enumerate(lower) if CODE_COL.match(h)]
    desc_i = lower.index("description")

    lookup = {c: fam for fam, spec in FAMILIES.items() for c in spec["codes"]}
    counts = defaultdict(Counter)
    examples = {}
    for row in rows:
        for i in code_idx:
            if i < len(row):
                code = row[i].strip()
                if code in lookup:
                    ctype = row[i + 1].strip() if i + 1 < len(row) else ""
                    key = f"{code} ({ctype})" if ctype else code
                    counts[lookup[code]][key] += 1
                    examples.setdefault(key, row[desc_i][:80])

    result = {
        "hospital": args.hospital,
        "families": {
            fam: {
                "note": spec["note"],
                "codes_found": {k: {"rows": v, "example_description": examples[k]} for k, v in counts[fam].most_common()},
            }
            for fam, spec in FAMILIES.items()
        },
    }
    out = ROOT / "data" / "investigations" / f"{args.hospital}_codes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    for fam in FAMILIES:
        found = ", ".join(f"{k}:{v}" for k, v in counts[fam].most_common()) or "none"
        print(f"::notice::{args.hospital} {fam}: {found}")


if __name__ == "__main__":
    main()
