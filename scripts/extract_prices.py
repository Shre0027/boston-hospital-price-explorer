"""
Extract prices for selected procedures from a hospital's price transparency file.

What it does, step by step:
  1. Downloads the hospital's machine-readable file (MRF) from the URL in config/hospitals.json
     (or reads a local file passed with --local-file, which is handy for testing).
  2. Opens the CSV inside (zipped or not) and finds the real column-header row.
     CMS-format CSVs put hospital info in rows 1-2 and the column names in row 3.
  3. Reads the file one row at a time (files can be over 1 GB, so we never load it all into memory)
     and keeps only rows whose billing code matches a procedure in config/procedures.json.
  4. Writes two outputs to data/processed/:
       <id>_prices.csv    the matching rows, all original columns kept
       <id>_profile.json  a short report on the file: format, size, rows, codes found and missing

Usage:
  python scripts/extract_prices.py --hospital mgh
  python scripts/extract_prices.py --hospital test --local-file path/to/file.csv
"""

import argparse
import csv
import gzip
import io
import json
import os
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"

# Some price files have extremely long cells (legal text, notes)
csv.field_size_limit(sys.maxsize)

# Matches CMS code columns like "code | 1", "code|2"
CODE_COL = re.compile(r"^code\s*\|\s*\d+$", re.IGNORECASE)

# Some hospital sites reject requests that don't look like a browser
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) price-transparency-research"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def body_stream(resp):
    """
    Some servers compress what they send (Content-Encoding: gzip), even for files that are
    already zipped. Browsers undo this automatically; urllib does not, so we do it here.
    """
    if resp.headers.get("Content-Encoding", "").lower() == "gzip":
        return gzip.GzipFile(fileobj=resp)
    return resp


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return body_stream(resp).read().decode("utf-8", errors="replace")


def resolve_mrf_url(hospital):
    """
    CMS requires each hospital website to have a cms-hpt.txt file at its root listing
    each location's current price-file link (mrf-url). Reading it means we always get
    the current link, even if the hospital moves its file.
    Falls back to the mrf_url saved in config if the txt file can't be used.
    """
    txt_url = hospital.get("hpt_txt")
    location = hospital.get("location_name", hospital["name"])
    if txt_url:
        try:
            current = {}
            text = fetch_text(txt_url)
            if "location-name" not in text.lower():
                raise ValueError("response isn't a cms-hpt.txt file (the site may have redirected to a web page)")
            for line in text.splitlines():
                key, _, value = line.partition(":")
                key, value = key.strip().lower(), value.strip()
                if key == "location-name":
                    current = {"location-name": value}
                elif key:
                    current[key] = value
                if current.get("location-name", "").lower() == location.lower() and current.get("mrf-url"):
                    print(f"Found current file link in {txt_url}")
                    return current["mrf-url"]
            print(f"::warning::'{location}' not found in {txt_url}; using the saved link instead")
        except Exception as e:
            print(f"::warning::Couldn't read {txt_url} ({e}); using the saved link instead")
    return hospital["mrf_url"]


def download(url, dest):
    """Download a file to disk in chunks. Some hospital sites reject requests without a browser-like User-Agent."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    start = time.time()
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as out:
        encoding = resp.headers.get("Content-Encoding") or "none"
        print(f"::notice::Server answered {resp.status}, type '{resp.headers.get('Content-Type')}', encoding '{encoding}'")
        body = body_stream(resp)
        while True:
            chunk = body.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    print(f"::notice::Downloaded {dest.stat().st_size / 1e6:.1f} MB in {time.time() - start:.0f}s")


def open_csv_text(path):
    """
    Return (text_stream, inner_name, inner_size_bytes) for the CSV.
    Handles a plain .csv or a .zip with one CSV inside.
    Skips macOS junk entries like '._file.csv' and '__MACOSX/' that some hospitals accidentally include.
    """
    if zipfile.is_zipfile(path):
        zf = zipfile.ZipFile(path)
        entries = [
            i for i in zf.infolist()
            if not i.is_dir()
            and not os.path.basename(i.filename).startswith("._")
            and not i.filename.startswith("__MACOSX")
        ]
        csv_entries = [i for i in entries if i.filename.lower().endswith(".csv")]
        if not csv_entries:
            names = [i.filename for i in zf.infolist()]
            raise ValueError(f"No CSV found inside zip. Contents: {names}")
        entry = max(csv_entries, key=lambda i: i.file_size)  # the real file is the big one
        raw = zf.open(entry)
        return io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""), entry.filename, entry.file_size
    if str(path).lower().endswith(".json"):
        raise NotImplementedError("JSON-format price files aren't supported yet (planned for a later step).")
    raw = open(path, "rb")
    return io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""), Path(path).name, Path(path).stat().st_size


def find_header(reader, max_rows=10):
    """
    CMS v2/v3 CSVs: row 1 = hospital info field names, row 2 = hospital info values, row 3 = column headers.
    Instead of assuming row 3, look for the first row that has a 'description' column.
    Returns (metadata_dict, header_row).
    """
    seen = []
    for _ in range(max_rows):
        row = next(reader, None)
        if row is None:
            break
        normalized = [c.strip().lower() for c in row]
        if "description" in normalized:
            metadata = {}
            if len(seen) >= 2:
                keys, values = seen[0], seen[1]
                for k, v in zip(keys, values):
                    k = k.strip()
                    if k and len(k) < 80:  # skip the very long legal attestation column name
                        metadata[k] = v.strip()
            return metadata, row
        seen.append(row)
    preview = " || ".join(",".join(r)[:120] for r in seen[:4])
    raise ValueError(f"Couldn't find a header row with a 'description' column. First rows: {preview}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hospital", required=True, help="Hospital id from config/hospitals.json")
    parser.add_argument("--local-file", help="Use a local file instead of downloading")
    args = parser.parse_args()

    procedures = load_json(ROOT / "config" / "procedures.json")
    wanted = {p["cpt"] for p in procedures}

    if args.local_file:
        path = Path(args.local_file)
        source_url = None
    else:
        hospitals = {h["id"]: h for h in load_json(ROOT / "config" / "hospitals.json")}
        if args.hospital not in hospitals:
            sys.exit(f"Unknown hospital id '{args.hospital}'. Options: {', '.join(hospitals)}")
        source_url = resolve_mrf_url(hospitals[args.hospital])
        path = RAW_DIR / Path(source_url.split("?")[0]).name
        print(f"Downloading {source_url}")
        download(source_url, path)

    downloaded_bytes = path.stat().st_size
    with open(path, "rb") as f:
        head = f.read(300)
    if head.lstrip().lower().startswith((b"<!doctype", b"<html")):
        snippet = head.decode("utf-8", errors="replace").replace("\n", " ")[:200]
        raise ValueError(f"Got a web page ({downloaded_bytes} bytes) instead of a price file. Starts with: {snippet}")
    text, inner_name, inner_size = open_csv_text(path)
    reader = csv.reader(text)
    metadata, header = find_header(reader)

    header_clean = [h.strip() for h in header]
    lower = [h.lower() for h in header_clean]
    code_idx = [i for i, h in enumerate(lower) if CODE_COL.match(h)]
    if not code_idx:
        raise ValueError(f"No 'code | N' columns found. First columns: {header_clean[:15]}")
    file_format = "tall" if "payer_name" in lower else "wide"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / f"{args.hospital}_prices.csv"
    total_rows = 0
    matched_rows = 0
    found = {}

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["matched_cpt"] + header_clean)
        for row in reader:
            total_rows += 1
            if total_rows % 1_000_000 == 0:
                print(f"  ...scanned {total_rows:,} rows, kept {matched_rows:,}")
            hit = None
            for i in code_idx:
                if i < len(row):
                    v = row[i].strip()
                    if v in wanted:
                        hit = v
                        break
            if hit:
                matched_rows += 1
                found[hit] = found.get(hit, 0) + 1
                writer.writerow([hit] + row)

    profile = {
        "hospital_id": args.hospital,
        "source_url": source_url,
        "downloaded_file": path.name,
        "downloaded_mb": round(downloaded_bytes / 1e6, 1),
        "csv_inside": inner_name,
        "csv_mb": round(inner_size / 1e6, 1),
        "hospital_metadata": metadata,
        "format": file_format,
        "column_count": len(header_clean),
        "code_columns": [header_clean[i] for i in code_idx],
        "total_data_rows": total_rows,
        "matched_rows": matched_rows,
        "procedures_found": {p["cpt"]: found.get(p["cpt"], 0) for p in procedures},
        "procedures_missing": [p["cpt"] for p in procedures if p["cpt"] not in found],
        "first_columns": header_clean[:30],
        "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(OUT_DIR / f"{args.hospital}_profile.json", "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    print(f"::notice::Format: {file_format}, {len(header_clean)} columns")
    print(f"::notice::Scanned {total_rows:,} rows, kept {matched_rows:,}")
    print(f"::notice::Found {len(found)} of {len(wanted)} procedures. Missing: {profile['procedures_missing'] or 'none'}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # "::error::" makes GitHub show this message right on the run's summary page
        print(f"::error::{type(e).__name__}: {e}")
        raise
