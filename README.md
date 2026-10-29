# Boston Hospital Price Explorer

**What will this actually cost me?**

👉 **[Open the live dashboard](https://shre0027.github.io/boston-hospital-price-explorer/)** · [SQL analysis](analysis/README.md) · [Decision log](docs/decision-log.md)

Since 2021, US hospitals have been legally required to publish their prices. But they publish them in huge, messy files that patients can't realistically use. The same MRI can cost very different amounts depending on the hospital and the insurer, and patients usually find out only when the bill arrives.

This project turns those public files into something a normal person can use.

## What it does
1. **Collects** official price files from 5 Boston hospitals
2. **Cleans** them and keeps about 18 common procedures, matched by billing code (CPT)
3. **Compares** prices across hospitals and insurers in a dashboard
4. **Answers plain-English questions** (keyword-based search, answers only from the data), such as "How much is a knee MRI with Blue Cross?"
5. **Checks data quality**: can patients actually use what each hospital published?

## Hospitals (Phase 1)
Massachusetts General Hospital · Brigham and Women's · Boston Medical Center · Beth Israel Deaconess Medical Center · Tufts Medical Center

## Status
✅ Phase 1 live: 5 hospitals, 18 procedures, 6,590 published prices, interactive dashboard.

Includes a plain-English price search ("knee MRI with Blue Cross") and refreshes automatically every month. Next: more Greater Boston hospitals.

## Data source
Hospital machine-readable files published under the CMS Hospital Price Transparency rule (45 CFR Part 180).

*Prices shown are published standard charges, not personal cost estimates.*

## How it works
| Step | Script | What it does |
|---|---|---|
| Find files | `scripts/discover.py` | Reads each hospital's official `cms-hpt.txt` to find its current price file |
| Extract | `scripts/extract_prices.py` | Downloads each file (CSV, zipped CSV or JSON, up to 1.7 GB) and keeps only the selected procedures |
| Combine | `scripts/combine.py` | Standardizes insurer names, numbers and markets; picks a fair comparison price; flags rows that can't be compared |
| Analyze (SQL) | `sql/*.sql`, `scripts/run_sql.py` | Eight documented SQL queries (CTEs, window functions) run with DuckDB; results in [`analysis/`](analysis/README.md) |
| Publish | `scripts/build_site.py` | Builds the dashboard in `site/`, published with GitHub Pages |

Downloads run on GitHub Actions (`.github/workflows/`), with an automatic monthly refresh (`refresh.yml`) that re-downloads, rebuilds and republishes. Every decision, finding and correction is in the [decision log](docs/decision-log.md).

