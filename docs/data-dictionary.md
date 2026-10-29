# Data dictionary

The project's main dataset is **`data/combined/prices_clean.csv`**, built by `scripts/combine.py` from each hospital's extracted rows in `data/processed/<hospital>_prices.csv`.

**Grain (what one row is):** one published price for one hospital × procedure × care setting × insurer plan. A hospital that lists 30 plans for a knee MRI has 30 rows for it. Rows with no insurer hold the hospital's gross (sticker) and cash prices.

**Size:** about 11,500 rows across 18 hospitals and 18 procedures (current counts: [`analysis/README.md`](../analysis/README.md), query 01).

**Source column names** below are the CMS template names (CSV "tall" format, v3.0.0). JSON files are flattened into the same names first (`scripts/extract_prices.py`).

## Who and what

| Column | Type | Meaning | Source | Example |
|---|---|---|---|---|
| `hospital_id` | text | Short project id for the hospital | `config/hospitals.json` | `mgh` |
| `hospital` | text | Hospital name | `config/hospitals.json` | Massachusetts General Hospital |
| `cpt` | text | Billing code the row was matched on (CPT, or MS-DRG for the gallbladder stay) | `code\|1`–`code\|4`, matched to `config/procedures.json` | `70551` |
| `procedure` | text | Plain-English procedure name used across all hospitals | `config/procedures.json` | MRI brain (no contrast) |
| `category` | text | Imaging, Lab test, Procedure or Visit | `config/procedures.json` | Imaging |
| `hospital_description` | text | The hospital's own name for the service, kept for checking matches | `description` | HC RADIOLOGIC EXAM CHEST 2 VIEWS |
| `setting` | text | `inpatient`, `outpatient` or `both` | `setting` | both |
| `modifiers` | text | Billing modifiers, if any (e.g. `52` = reduced service). Rows with modifiers are excluded from comparisons | `modifiers` | 52 |

## Who pays

| Column | Type | Meaning | Source | Example |
|---|---|---|---|---|
| `payer_raw` | text | Insurer name exactly as the hospital wrote it | `payer_name` | BLUE CROSS BLUE SHIELD [110001] |
| `plan_raw` | text | Plan name exactly as the hospital wrote it | `plan_name` | HB AMC BLUE CROSS PPO |
| `insurer` | text | Insurer brand a patient would recognize, or `Other`. Rules in `INSURER_GROUPS` in `combine.py` | derived from `payer_raw` (and `plan_raw` for generic payers) | Blue Cross Blue Shield |
| `market` | text | Commercial, Medicare, MassHealth / safety net, Military, Other public / workers comp, Dental / vision plan, Behavioral health plan, Unclear (excluded), or Inactive (retired contract). Only `Commercial` is used for insurer comparisons | derived, rules in `MARKETS` in `combine.py` | Commercial |

## Prices (US dollars unless noted)

| Column | Type | Meaning | Source | Example |
|---|---|---|---|---|
| `gross_charge` | number | Sticker price: the hospital's list price before any discount | `standard_charge\|gross` | 5144.00 |
| `cash_price` | number | Price for patients paying without insurance | `standard_charge\|discounted_cash` | 3858.00 |
| `negotiated_dollar` | number | The insurer's negotiated rate as a dollar amount, when given | `standard_charge\|negotiated_dollar` | 230.56 |
| `negotiated_percent` | number | Rate as a percent of billed charges, when given (percent, not dollars) | `standard_charge\|negotiated_percentage` | 31.38 |
| `negotiated_formula` | text | Description of a formula-based rate, cut to 300 characters | `standard_charge\|negotiated_algorithm` | Case rate ($230.56). The procedures on the claim are sorted… |
| `median_paid` | number | Median amount actually paid for this service under the contract (added to the CMS template in 2026) | `median_amount` | 657.10 |
| `p10_paid`, `p90_paid` | number | 10th and 90th percentile of amounts actually paid | `10th_percentile`, `90th_percentile` | |
| `min_negotiated`, `max_negotiated` | number | Lowest and highest negotiated rate the hospital lists for this service across all payers | `standard_charge\|min`, `standard_charge\|max` | |
| `methodology` | text | Contract type: fee schedule, percent of total billed charges, case rate, per diem, other | `standard_charge\|methodology` | fee schedule |

## Comparison fields (decided by this project)

| Column | Type | Meaning | Rule |
|---|---|---|---|
| `comparison_price` | number | The one price used to compare hospitals | 1) If the rate comes from a formula and `median_paid` exists, use `median_paid`. 2) Else use `negotiated_dollar`. 3) Else use `median_paid` |
| `price_basis` | text | Which rule above was used | `median amount paid (rate set by formula)`, `negotiated dollar amount` or `median amount paid` |
| `flag` | text | Why a row is kept but **left out of comparisons**; empty means usable | `insurer rate above sticker price (likely a bundled rate)`; `rate set by formula and no amount-paid figure given…`; `implausibly low (under 10% of the typical price for this procedure…)` |

## Rules applied downstream

These aren't columns, but they decide what the analysis and dashboard show:

- **Comparable row** (`sql/00_setup.sql`, view `comparable`): `market = 'Commercial'`, `comparison_price` present, no `flag`, no `modifiers`.
- **Typical commercial price** (view `typical_commercial`): median of comparable rows per hospital and procedure, shown only with **at least 3** plan prices.
- **Price level / index** (queries 05, 08–10 and the dashboard): each hospital's typical price ÷ the median across hospitals for that procedure, then the median across procedures; procedures listed by at least 8 hospitals, hospitals with at least 8 such procedures.

## Related files

| File | What it holds |
|---|---|
| `data/processed/<id>_profile.json` | Per-hospital file facts: size, rows scanned, procedures found and missing, file date, how it was collected |
| `data/quality/ma_hospital_general_information.csv` | CMS star ratings for Massachusetts hospitals, joined by CMS Certification Number (`ccn` in `config/hospitals.json`) |
| `data/discovery.json` | Every location and file link read from hospitals' `cms-hpt.txt` files |
| `data/investigations/<id>_codes.json` | Which related billing codes each hospital uses (used to choose the ECG and gallbladder codes) |
| `config/data_access.json` | Hand-recorded findings about each file's accessibility |
