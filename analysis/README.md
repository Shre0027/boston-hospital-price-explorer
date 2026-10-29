# SQL analysis

Standard SQL run with DuckDB directly on `data/combined/prices_clean.csv` (6,590 published price rows). Shared views are defined in [`sql/00_setup.sql`](../sql/00_setup.sql). Re-run everything with `python scripts/run_sql.py`; full results are in [`analysis/results/`](results/).

Prices are amounts paid to the hospital, not a patient's out-of-pocket cost. "Typical commercial" = median across a hospital's listed commercial plans.

## 01. Hospital overview

**Question:** What did each hospital actually publish, and how much of it is usable for comparison?

**Why it matters:** before comparing prices, check that each hospital's data is complete enough to compare.

Query: [`sql/01_hospital_overview.sql`](../sql/01_hospital_overview.sql)

| hospital | price_rows | procedures_listed | insurer_plans_listed | commercial_rows | flagged_rows | pct_flagged |
|---|---|---|---|---|---|---|
| Tufts Medical Center | 3,842 | 14 | 170 | 1,580 | 146 | 3.8 |
| Boston Medical Center | 1,610 | 16 | 77 | 553 | 622 | 38.6 |
| Massachusetts General Hospital | 535 | 14 | 30 | 355 | 10 | 1.9 |
| Brigham and Women's Hospital | 507 | 14 | 30 | 337 | 29 | 5.7 |
| Beth Israel Deaconess Medical Center | 96 | 18 | 6 | 72 | 0 | 0 |

## 02. Price gap by procedure

**Question:** For each procedure, how far apart are the cheapest and most expensive hospitals for patients with commercial insurance?

**Why it matters:** a large gap means choosing a hospital can save a lot of money for the same service.

Query: [`sql/02_price_gap_by_procedure.sql`](../sql/02_price_gap_by_procedure.sql)

| procedure | hospitals_listing | lowest_hospital | lowest_price | highest_hospital | highest_price | times_more |
|---|---|---|---|---|---|---|
| Complete blood count (CBC) | 5 | Tufts Medical Center | 9 | Massachusetts General Hospital | 90 | 9.5 |
| Comprehensive metabolic panel | 5 | Tufts Medical Center | 14 | Massachusetts General Hospital | 125 | 9.1 |
| Cholesterol (lipid) panel | 5 | Tufts Medical Center | 18 | Massachusetts General Hospital | 116 | 6.6 |
| ER visit (moderate) | 5 | Boston Medical Center | 454 | Massachusetts General Hospital | 1,477 | 3.3 |
| ER visit (serious) | 5 | Tufts Medical Center | 630 | Massachusetts General Hospital | 2,008 | 3.2 |
| Chest X-ray (2 views) | 5 | Beth Israel Deaconess Medical Center | 110 | Brigham and Women's Hospital | 335 | 3 |
| Doctor office visit (established patient) | 5 | Boston Medical Center | 73 | Massachusetts General Hospital | 216 | 2.9 |
| MRI brain (no contrast) | 5 | Tufts Medical Center | 571 | Massachusetts General Hospital | 1,614 | 2.8 |
| MRI lower back (no contrast) | 5 | Tufts Medical Center | 571 | Brigham and Women's Hospital | 1,365 | 2.4 |
| Screening mammogram | 5 | Tufts Medical Center | 204 | Massachusetts General Hospital | 472 | 2.3 |
| Colonoscopy (diagnostic) | 5 | Tufts Medical Center | 905 | Massachusetts General Hospital | 1,975 | 2.2 |
| Abdominal ultrasound (complete) | 5 | Beth Israel Deaconess Medical Center | 199 | Massachusetts General Hospital | 423 | 2.1 |
| MRI knee (no contrast) | 5 | Tufts Medical Center | 571 | Massachusetts General Hospital | 1,046 | 1.8 |
| CT abdomen and pelvis (with contrast) | 5 | Tufts Medical Center | 755 | Boston Medical Center | 1,360 | 1.8 |

## 03. Cash vs insured

**Question:** How much more does a patient without insurance pay (cash price) than what commercial insurers typically pay, at the same hospital for the same procedure?

**Why it matters:** shows whether uninsured patients are charged more than insured ones.

Query: [`sql/03_cash_vs_insured.sql`](../sql/03_cash_vs_insured.sql)

| hospital | procedure | cash_price | typical_insurer_price | cash_times_insurer |
|---|---|---|---|---|
| Beth Israel Deaconess Medical Center | Comprehensive metabolic panel | 658 | 26 | 25.5 |
| Beth Israel Deaconess Medical Center | ECG (electrocardiogram) | 593 | 64 | 9.2 |
| Beth Israel Deaconess Medical Center | Abdominal ultrasound (complete) | 1,333 | 199 | 6.7 |
| Beth Israel Deaconess Medical Center | MRI lower back (no contrast) | 3,237 | 638 | 5.1 |
| Beth Israel Deaconess Medical Center | MRI brain (no contrast) | 3,170 | 638 | 5 |
| Beth Israel Deaconess Medical Center | MRI knee (no contrast) | 2,921 | 638 | 4.6 |
| Boston Medical Center | Comprehensive metabolic panel | 78 | 19 | 4.2 |
| Beth Israel Deaconess Medical Center | Complete blood count (CBC) | 79 | 19 | 4.1 |
| Beth Israel Deaconess Medical Center | Cholesterol (lipid) panel | 125 | 33 | 3.8 |
| Boston Medical Center | MRI brain (no contrast) | 2,066 | 574 | 3.6 |
| Beth Israel Deaconess Medical Center | CT abdomen and pelvis (with contrast) | 3,721 | 1,068 | 3.5 |
| Massachusetts General Hospital | MRI lower back (no contrast) | 3,281 | 967 | 3.4 |
| Boston Medical Center | MRI knee (no contrast) | 2,076 | 628 | 3.3 |
| Boston Medical Center | MRI lower back (no contrast) | 1,815 | 574 | 3.2 |
| Beth Israel Deaconess Medical Center | Screening mammogram | 889 | 275 | 3.2 |

## 04. Same insurer different hospitals

**Question:** Does the same insurer pay very different amounts for the same procedure depending on the hospital?

**Why it matters:** if one insurer pays one hospital several times more than another for the same service, that cost flows into everyone's premiums.

Query: [`sql/04_same_insurer_different_hospitals.sql`](../sql/04_same_insurer_different_hospitals.sql)

| insurer | procedure | hospitals | lowest_hospital | lowest_price | highest_hospital | highest_price | times_more |
|---|---|---|---|---|---|---|---|
| UnitedHealthcare | Comprehensive metabolic panel | 4 | Boston Medical Center | 10 | Brigham and Women's Hospital | 140 | 14.7 |
| UnitedHealthcare | Complete blood count (CBC) | 4 | Boston Medical Center | 7 | Massachusetts General Hospital | 98 | 14.1 |
| UnitedHealthcare | Cholesterol (lipid) panel | 4 | Boston Medical Center | 12 | Massachusetts General Hospital | 130 | 10.8 |
| Blue Cross Blue Shield | Cholesterol (lipid) panel | 5 | Tufts Medical Center | 11 | Brigham and Women's Hospital | 87 | 8.2 |
| Cigna | Comprehensive metabolic panel | 5 | Boston Medical Center | 20 | Brigham and Women's Hospital | 129 | 6.3 |
| Cigna | Complete blood count (CBC) | 5 | Boston Medical Center | 15 | Brigham and Women's Hospital | 90 | 6.1 |
| UnitedHealthcare | Screening mammogram | 4 | Boston Medical Center | 109 | Tufts Medical Center | 582 | 5.4 |
| Aetna | Complete blood count (CBC) | 4 | Tufts Medical Center | 17 | Massachusetts General Hospital | 93 | 5.4 |
| Aetna | Comprehensive metabolic panel | 4 | Tufts Medical Center | 25 | Massachusetts General Hospital | 133 | 5.3 |
| Cigna | MRI lower back (no contrast) | 3 | Massachusetts General Hospital | 673 | Boston Medical Center | 3,429 | 5.1 |
| Cigna | Cholesterol (lipid) panel | 5 | Boston Medical Center | 26 | Brigham and Women's Hospital | 120 | 4.7 |
| Blue Cross Blue Shield | Comprehensive metabolic panel | 5 | Boston Medical Center | 21 | Massachusetts General Hospital | 93 | 4.5 |
| Blue Cross Blue Shield | Complete blood count (CBC) | 5 | Boston Medical Center | 15 | Massachusetts General Hospital | 65 | 4.2 |
| Cigna | MRI brain (no contrast) | 3 | Tufts Medical Center | 1,019 | Boston Medical Center | 3,902 | 3.8 |
| Aetna | Cholesterol (lipid) panel | 4 | Tufts Medical Center | 32 | Brigham and Women's Hospital | 116 | 3.6 |

## 05. Overall hospital ranking

**Question:** Across all procedures, which hospital tends to be cheapest or most expensive for commercial insurance?

**Why it matters:** one procedure can be a fluke; a consistent pattern across many procedures is a real finding.

**Method:** for each procedure, express each hospital's price relative to the cheapest hospital (1.0 = cheapest), then take the median (robust to a few extreme gaps) and the average across procedures. Only procedures listed by at least 4 hospitals count, so every hospital is compared on mostly the same set.

Query: [`sql/05_overall_hospital_ranking.sql`](../sql/05_overall_hospital_ranking.sql)

| hospital | procedures_compared | median_times_cheapest | avg_times_cheapest | avg_rank_1_is_cheapest | times_cheapest_hospital |
|---|---|---|---|---|---|
| Tufts Medical Center | 14 | 1 | 1.1 | 1.4 | 10 |
| Beth Israel Deaconess Medical Center | 14 | 1.36 | 1.43 | 2.4 | 2 |
| Boston Medical Center | 14 | 1.4 | 1.4 | 2.3 | 2 |
| Brigham and Women's Hospital | 14 | 2.27 | 3.49 | 4.1 | 0 |
| Massachusetts General Hospital | 14 | 2.89 | 3.73 | 4.8 | 0 |

## 06. Price basis and flags

**Question:** How was each comparison price chosen, and how many rows were set aside, by hospital?

**Why it matters:** shows how much of each hospital's data is directly usable versus needing caution, which is itself a measure of how "transparent" the published data really is.

Query: [`sql/06_price_basis_and_flags.sql`](../sql/06_price_basis_and_flags.sql)

| hospital | price_basis | flag | price_rows |
|---|---|---|---|
| Beth Israel Deaconess Medical Center | negotiated dollar amount | (not flagged) | 80 |
| Beth Israel Deaconess Medical Center | (no usable price) | (not flagged) | 16 |
| Boston Medical Center | negotiated dollar amount | (not flagged) | 698 |
| Boston Medical Center | negotiated dollar amount | rate set by formula and no amount-paid figure given; listed amount may be only part of the payment | 513 |
| Boston Medical Center | median amount paid (rate set by formula) | (not flagged) | 290 |
| Boston Medical Center | negotiated dollar amount | insurer rate above sticker price (likely a bundled rate) | 97 |
| Boston Medical Center | median amount paid (rate set by formula) | insurer rate above sticker price (likely a bundled rate) | 12 |
| Brigham and Women's Hospital | negotiated dollar amount | (not flagged) | 286 |
| Brigham and Women's Hospital | median amount paid (rate set by formula) | (not flagged) | 192 |
| Brigham and Women's Hospital | median amount paid (rate set by formula) | insurer rate above sticker price (likely a bundled rate) | 29 |
| Massachusetts General Hospital | negotiated dollar amount | (not flagged) | 308 |
| Massachusetts General Hospital | median amount paid (rate set by formula) | (not flagged) | 217 |
| Massachusetts General Hospital | median amount paid (rate set by formula) | insurer rate above sticker price (likely a bundled rate) | 10 |
| Tufts Medical Center | negotiated dollar amount | (not flagged) | 3,627 |
| Tufts Medical Center | negotiated dollar amount | rate set by formula and no amount-paid figure given; listed amount may be only part of the payment | 125 |
| Tufts Medical Center | median amount paid (rate set by formula) | (not flagged) | 65 |
| Tufts Medical Center | negotiated dollar amount | insurer rate above sticker price (likely a bundled rate) | 19 |
| Tufts Medical Center | (no usable price) | (not flagged) | 4 |
| Tufts Medical Center | median amount paid (rate set by formula) | insurer rate above sticker price (likely a bundled rate) | 2 |

## 07. Contract type effect

**Question:** Within the same hospital, are "percent of billed charges" contracts more expensive than fixed "fee schedule" contracts?

**Why it matters:** under a percent-of-charges contract, the insurer pays a share of the hospital's own sticker price, so a high sticker price flows straight into what is paid. If those contracts cost more even inside the same hospital, contract design (not just the hospital) drives cost.

**Method:** compare within each hospital so that hospital differences don't get mixed in (MGH and Brigham use percent-of-charges almost exclusively, so they can't show a within-hospital contrast). For each hospital and procedure that has BOTH contract types, take the median price under each type, then summarize the ratio (percent-of-charges / fee schedule) across procedures.

Query: [`sql/07_contract_type_effect.sql`](../sql/07_contract_type_effect.sql)

| hospital | procedures_with_both | median_ratio_pct_vs_fee | lowest_ratio | highest_ratio | procedures_where_pct_costs_more |
|---|---|---|---|---|---|
| Boston Medical Center | 15 | 2.72 | 0.65 | 5.4 | 14 |
| Tufts Medical Center | 14 | 0.64 | 0.39 | 4.3 | 1 |

## 08. Sticker price levels

**Question:** How high is each hospital's own sticker price (gross charge), relative to the other hospitals?

**Why it matters:** query 07 showed that "percent of billed charges" contracts are expensive at some hospitals and cheap at others. If that's because the percentage is applied to very different sticker prices, hospitals with high sticker prices should be the ones where insurers pay the most.

**Method:** one sticker price per hospital and procedure (median across rows), expressed relative to the lowest sticker price for that procedure; summarized by hospital over procedures listed by at least 4 hospitals. The last column repeats each hospital's typical commercial price level (from query 05) for side-by-side reading.

Query: [`sql/08_sticker_price_levels.sql`](../sql/08_sticker_price_levels.sql)

| hospital | procedures_compared | median_sticker_vs_lowest | median_insurer_paid_vs_lowest |
|---|---|---|---|
| Tufts Medical Center | 14 | 1 | 1 |
| Beth Israel Deaconess Medical Center | 14 | 1.63 | 1.36 |
| Massachusetts General Hospital | 14 | 1.7 | 2.89 |
| Brigham and Women's Hospital | 14 | 1.7 | 2.27 |
| Boston Medical Center | 14 | 1.82 | 1.4 |
