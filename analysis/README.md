# SQL analysis

Standard SQL run with DuckDB directly on `data/combined/prices_clean.csv` (11,465 published price rows). Shared views are defined in [`sql/00_setup.sql`](../sql/00_setup.sql). Re-run everything with `python scripts/run_sql.py`; full results are in [`analysis/results/`](results/).

Prices are amounts paid to the hospital, not a patient's out-of-pocket cost. "Typical commercial" = median across a hospital's listed commercial plans.

## 01. Hospital overview

**Question:** What did each hospital actually publish, and how much of it is usable for comparison?

**Why it matters:** before comparing prices, check that each hospital's data is complete enough to compare.

Query: [`sql/01_hospital_overview.sql`](../sql/01_hospital_overview.sql)

| hospital | price_rows | procedures_listed | insurer_plans_listed | commercial_rows | flagged_rows | pct_flagged |
|---|---|---|---|---|---|---|
| Tufts Medical Center | 4,210 | 16 | 193 | 1,625 | 199 | 4.7 |
| Boston Medical Center | 1,758 | 17 | 77 | 605 | 674 | 38.3 |
| Cambridge Health Alliance | 1,597 | 17 | 73 | 672 | 231 | 14.5 |
| Boston Medical Center Brighton | 855 | 15 | 55 | 281 | 368 | 43 |
| Massachusetts General Hospital | 580 | 16 | 30 | 380 | 10 | 1.7 |
| Brigham and Women's Hospital | 549 | 16 | 30 | 361 | 30 | 5.5 |
| Salem Hospital | 310 | 16 | 23 | 226 | 17 | 5.5 |
| Newton-Wellesley Hospital | 256 | 15 | 22 | 201 | 1 | 0.4 |
| Brigham and Women's Faulkner Hospital | 250 | 15 | 26 | 186 | 27 | 10.8 |
| South Shore Hospital | 236 | 18 | 16 | 205 | 0 | 0 |
| Winchester Hospital | 150 | 18 | 14 | 116 | 0 | 0 |
| New England Baptist Hospital | 125 | 18 | 7 | 95 | 0 | 0 |
| Beth Israel Deaconess Medical Center | 121 | 18 | 15 | 89 | 1 | 0.8 |
| Lahey Hospital & Medical Center | 114 | 18 | 17 | 82 | 0 | 0 |
| Mount Auburn Hospital | 111 | 18 | 7 | 88 | 0 | 0 |
| Beth Israel Deaconess Hospital–Milton | 92 | 18 | 7 | 75 | 0 | 0 |
| Beth Israel Deaconess Hospital–Needham | 81 | 18 | 14 | 58 | 0 | 0 |
| Massachusetts Eye and Ear | 70 | 9 | 19 | 56 | 2 | 2.9 |

## 02. Price gap by procedure

**Question:** For each procedure, how far apart are the cheapest and most expensive hospitals for patients with commercial insurance?

**Why it matters:** a large gap means choosing a hospital can save a lot of money for the same service.

Query: [`sql/02_price_gap_by_procedure.sql`](../sql/02_price_gap_by_procedure.sql)

| procedure | hospitals_listing | lowest_hospital | lowest_price | highest_hospital | highest_price | times_more |
|---|---|---|---|---|---|---|
| Complete blood count (CBC) | 17 | Tufts Medical Center | 10 | Massachusetts General Hospital | 90 | 9.4 |
| Comprehensive metabolic panel | 17 | Tufts Medical Center | 14 | Massachusetts General Hospital | 125 | 9.1 |
| Cholesterol (lipid) panel | 17 | Tufts Medical Center | 18 | Massachusetts General Hospital | 116 | 6.6 |
| Doctor office visit (established patient) | 15 | South Shore Hospital | 36 | Massachusetts General Hospital | 216 | 6 |
| Chest X-ray (2 views) | 17 | Beth Israel Deaconess Hospital–Milton | 71 | Cambridge Health Alliance | 364 | 5.1 |
| MRI brain (no contrast) | 18 | South Shore Hospital | 338 | Massachusetts General Hospital | 1,614 | 4.8 |
| ER visit (serious) | 13 | Lahey Hospital & Medical Center | 467 | Massachusetts General Hospital | 2,008 | 4.3 |
| MRI knee (no contrast) | 17 | South Shore Hospital | 338 | Newton-Wellesley Hospital | 1,439 | 4.3 |
| MRI lower back (no contrast) | 17 | South Shore Hospital | 338 | Brigham and Women's Hospital | 1,365 | 4 |
| ECG (electrocardiogram, hospital tracing) | 18 | South Shore Hospital | 64 | Massachusetts General Hospital | 234 | 3.7 |
| Abdominal ultrasound (complete) | 17 | South Shore Hospital | 129 | Massachusetts General Hospital | 423 | 3.3 |
| Cataract surgery | 8 | Boston Medical Center | 1,436 | Beth Israel Deaconess Medical Center | 4,806 | 3.3 |
| ER visit (moderate) | 12 | Lahey Hospital & Medical Center | 283 | Cambridge Health Alliance | 890 | 3.1 |
| CT abdomen and pelvis (with contrast) | 16 | South Shore Hospital | 483 | Boston Medical Center | 1,360 | 2.8 |
| Screening mammogram | 16 | New England Baptist Hospital | 173 | Massachusetts General Hospital | 472 | 2.7 |
| Knee arthroscopy (meniscus) | 9 | Boston Medical Center | 2,503 | Beth Israel Deaconess Medical Center | 6,576 | 2.6 |
| Gallbladder removal, laparoscopic (hospital stay) | 9 | Beth Israel Deaconess Hospital–Milton | 10,101 | Lahey Hospital & Medical Center | 24,186 | 2.4 |
| Colonoscopy (diagnostic) | 17 | Tufts Medical Center | 905 | Massachusetts General Hospital | 1,975 | 2.2 |

## 03. Cash vs insured

**Question:** How much more does a patient without insurance pay (cash price) than what commercial insurers typically pay, at the same hospital for the same procedure?

**Why it matters:** shows whether uninsured patients are charged more than insured ones.

Query: [`sql/03_cash_vs_insured.sql`](../sql/03_cash_vs_insured.sql)

| hospital | procedure | cash_price | typical_insurer_price | cash_times_insurer |
|---|---|---|---|---|
| New England Baptist Hospital | Comprehensive metabolic panel | 414 | 16 | 25.7 |
| Beth Israel Deaconess Medical Center | Comprehensive metabolic panel | 658 | 26 | 25.5 |
| Beth Israel Deaconess Hospital–Needham | Comprehensive metabolic panel | 376 | 21 | 18.2 |
| Cambridge Health Alliance | Comprehensive metabolic panel | 320 | 28 | 11.5 |
| South Shore Hospital | CT abdomen and pelvis (with contrast) | 4,123 | 483 | 8.5 |
| New England Baptist Hospital | Cholesterol (lipid) panel | 156 | 20 | 7.6 |
| South Shore Hospital | Doctor office visit (established patient) | 274 | 36 | 7.6 |
| South Shore Hospital | MRI lower back (no contrast) | 2,476 | 338 | 7.3 |
| New England Baptist Hospital | MRI knee (no contrast) | 2,772 | 390 | 7.1 |
| Mount Auburn Hospital | MRI knee (no contrast) | 4,222 | 611 | 6.9 |
| Beth Israel Deaconess Medical Center | Abdominal ultrasound (complete) | 1,333 | 199 | 6.7 |
| New England Baptist Hospital | Complete blood count (CBC) | 76 | 12 | 6.6 |
| New England Baptist Hospital | MRI brain (no contrast) | 2,485 | 390 | 6.4 |
| South Shore Hospital | Cholesterol (lipid) panel | 166 | 26 | 6.3 |
| Winchester Hospital | Abdominal ultrasound (complete) | 1,214 | 192 | 6.3 |

## 04. Same insurer different hospitals

**Question:** Does the same insurer pay very different amounts for the same procedure depending on the hospital?

**Why it matters:** if one insurer pays one hospital several times more than another for the same service, that cost flows into everyone's premiums.

Query: [`sql/04_same_insurer_different_hospitals.sql`](../sql/04_same_insurer_different_hospitals.sql)

| insurer | procedure | hospitals | lowest_hospital | lowest_price | highest_hospital | highest_price | times_more |
|---|---|---|---|---|---|---|---|
| Cigna | Comprehensive metabolic panel | 15 | New England Baptist Hospital | 11 | Massachusetts Eye and Ear | 462 | 40.2 |
| Aetna | Comprehensive metabolic panel | 11 | Winchester Hospital | 11 | Massachusetts Eye and Ear | 305 | 28.9 |
| Cigna | Cholesterol (lipid) panel | 15 | New England Baptist Hospital | 14 | Massachusetts Eye and Ear | 226 | 16 |
| UnitedHealthcare | Comprehensive metabolic panel | 12 | Beth Israel Deaconess Hospital–Milton | 9 | Brigham and Women's Hospital | 140 | 15.8 |
| UnitedHealthcare | Complete blood count (CBC) | 12 | Beth Israel Deaconess Hospital–Milton | 7 | Brigham and Women's Hospital / Massachusetts General Hospital | 98 | 15.1 |
| Blue Cross Blue Shield | MRI knee (no contrast) | 11 | South Shore Hospital | 264 | Newton-Wellesley Hospital | 3,937 | 14.9 |
| UnitedHealthcare | Knee arthroscopy (meniscus) | 6 | Boston Medical Center | 695 | Winchester Hospital | 9,401 | 13.5 |
| UnitedHealthcare | Cataract surgery | 6 | Boston Medical Center | 695 | Winchester Hospital | 9,039 | 13 |
| Aetna | MRI brain (no contrast) | 11 | South Shore Hospital / Winchester Hospital | 286 | Massachusetts General Hospital | 3,634 | 12.7 |
| Aetna | Complete blood count (CBC) | 11 | Winchester Hospital | 8 | Massachusetts General Hospital | 93 | 12 |
| UnitedHealthcare | Cholesterol (lipid) panel | 12 | Beth Israel Deaconess Hospital–Milton | 11 | Massachusetts General Hospital | 130 | 11.6 |
| Aetna | Cholesterol (lipid) panel | 11 | Winchester Hospital | 13 | Massachusetts Eye and Ear | 150 | 11.2 |
| Cigna | Complete blood count (CBC) | 14 | New England Baptist Hospital | 8 | Brigham and Women's Hospital / Massachusetts General Hospital | 90 | 10.7 |
| Blue Cross Blue Shield | Doctor office visit (established patient) | 12 | Boston Medical Center Brighton | 35 | Tufts Medical Center | 361 | 10.4 |
| Aetna | MRI lower back (no contrast) | 11 | South Shore Hospital / Winchester Hospital | 286 | Brigham and Women's Hospital | 2,873 | 10 |

## 05. Overall hospital ranking

**Question:** Across all procedures, which hospitals tend to be cheaper or more expensive for commercial insurance?

**Why it matters:** one procedure can be a fluke; a consistent pattern across many procedures is a real finding.

**Method:** a simple price index. For each procedure, divide each hospital's typical commercial price by the median across hospitals for that procedure (1.0 = typical; 1.5 = 50% above typical). Each hospital's index is the median of these ratios. Only procedures listed by at least 8 hospitals count, and only hospitals with at least 8 such procedures are ranked, so every hospital is compared on mostly the same set.

Query: [`sql/05_overall_hospital_ranking.sql`](../sql/05_overall_hospital_ranking.sql)

| hospital | procedures_compared | price_index | lowest_ratio | highest_ratio | procedures_below_typical |
|---|---|---|---|---|---|
| South Shore Hospital | 18 | 0.63 | 0.28 | 1.7 | 16 |
| New England Baptist Hospital | 17 | 0.71 | 0.51 | 0.98 | 17 |
| Beth Israel Deaconess Hospital–Milton | 17 | 0.73 | 0.5 | 0.87 | 17 |
| Winchester Hospital | 18 | 0.89 | 0.68 | 1.11 | 16 |
| Tufts Medical Center | 16 | 0.9 | 0.49 | 1.19 | 10 |
| Beth Israel Deaconess Hospital–Needham | 11 | 0.94 | 0.6 | 1.41 | 8 |
| Boston Medical Center | 17 | 1 | 0.42 | 2.41 | 8 |
| Boston Medical Center Brighton | 15 | 1 | 0.37 | 1.36 | 6 |
| Mount Auburn Hospital | 18 | 1 | 0.74 | 1.22 | 8 |
| Lahey Hospital & Medical Center | 18 | 1.04 | 0.63 | 1.65 | 4 |
| Brigham and Women's Faulkner Hospital | 12 | 1.1 | 0.92 | 2.85 | 5 |
| Beth Israel Deaconess Medical Center | 18 | 1.12 | 0.74 | 1.56 | 4 |
| Newton-Wellesley Hospital | 13 | 1.13 | 0.96 | 2.85 | 1 |
| Salem Hospital | 13 | 1.13 | 0.94 | 3.08 | 4 |
| Cambridge Health Alliance | 15 | 1.22 | 1 | 3.25 | 0 |
| Massachusetts General Hospital | 14 | 1.88 | 1.24 | 4.83 | 0 |
| Brigham and Women's Hospital | 15 | 1.89 | 1.2 | 4.83 | 0 |

## 06. Price basis and flags

**Question:** How was each comparison price chosen, and how many rows were set aside, by hospital?

**Why it matters:** shows how much of each hospital's data is directly usable versus needing caution, which is itself a measure of how "transparent" the published data really is.

Query: [`sql/06_price_basis_and_flags.sql`](../sql/06_price_basis_and_flags.sql)

| hospital | price_basis | flag | price_rows |
|---|---|---|---|
| Beth Israel Deaconess Hospital–Milton | negotiated dollar amount | (not flagged) | 69 |
| Beth Israel Deaconess Hospital–Milton | (no usable price) | (not flagged) | 22 |
| Beth Israel Deaconess Hospital–Milton | median amount paid (rate set by formula) | (not flagged) | 1 |
| Beth Israel Deaconess Hospital–Needham | negotiated dollar amount | (not flagged) | 48 |
| Beth Israel Deaconess Hospital–Needham | (no usable price) | (not flagged) | 31 |
| Beth Israel Deaconess Hospital–Needham | median amount paid (rate set by formula) | (not flagged) | 2 |
| Beth Israel Deaconess Medical Center | negotiated dollar amount | (not flagged) | 79 |
| Beth Israel Deaconess Medical Center | (no usable price) | (not flagged) | 36 |
| Beth Israel Deaconess Medical Center | median amount paid (rate set by formula) | (not flagged) | 5 |
| Beth Israel Deaconess Medical Center | median amount paid (rate set by formula) | implausibly low (under 10% of the typical price for this procedure; likely a data error) | 1 |
| Boston Medical Center | negotiated dollar amount | (not flagged) | 752 |
| Boston Medical Center | negotiated dollar amount | rate set by formula and no amount-paid figure given; listed amount may be only part of the payment | 547 |
| Boston Medical Center | median amount paid (rate set by formula) | (not flagged) | 332 |
| Boston Medical Center | negotiated dollar amount | insurer rate above sticker price (likely a bundled rate) | 109 |
| Boston Medical Center | median amount paid (rate set by formula) | insurer rate above sticker price (likely a bundled rate) | 18 |
| Boston Medical Center Brighton | negotiated dollar amount | (not flagged) | 391 |
| Boston Medical Center Brighton | negotiated dollar amount | rate set by formula and no amount-paid figure given; listed amount may be only part of the payment | 251 |
| Boston Medical Center Brighton | negotiated dollar amount | insurer rate above sticker price (likely a bundled rate) | 107 |
| Boston Medical Center Brighton | median amount paid (rate set by formula) | (not flagged) | 96 |
| Boston Medical Center Brighton | median amount paid (rate set by formula) | insurer rate above sticker price (likely a bundled rate) | 10 |

*Showing 20 of 71 rows; see the CSV for all.*

## 07. Contract type effect

**Question:** Within the same hospital, are "percent of billed charges" contracts more expensive than fixed "fee schedule" contracts?

**Why it matters:** under a percent-of-charges contract, the insurer pays a share of the hospital's own sticker price, so a high sticker price flows straight into what is paid. If those contracts cost more even inside the same hospital, contract design (not just the hospital) drives cost.

**Method:** compare within each hospital so that hospital differences don't get mixed in (MGH and Brigham use percent-of-charges almost exclusively, so they can't show a within-hospital contrast). For each hospital and procedure that has BOTH contract types, take the median price under each type, then summarize the ratio (percent-of-charges / fee schedule) across procedures.

Query: [`sql/07_contract_type_effect.sql`](../sql/07_contract_type_effect.sql)

| hospital | procedures_with_both | median_ratio_pct_vs_fee | lowest_ratio | highest_ratio | procedures_where_pct_costs_more |
|---|---|---|---|---|---|
| Boston Medical Center | 16 | 2.53 | 0.65 | 5.4 | 14 |
| Boston Medical Center Brighton | 15 | 1.43 | 0.75 | 2.28 | 13 |
| Cambridge Health Alliance | 15 | 3.26 | 0.82 | 15.52 | 14 |
| South Shore Hospital | 1 | 2.17 | 2.17 | 2.17 | 1 |
| Tufts Medical Center | 15 | 0.64 | 0.39 | 4.3 | 1 |

## 08. Sticker price levels

**Question:** How high is each hospital's own sticker price (gross charge), compared with what insurers pay it?

**Why it matters:** query 07 showed that "percent of billed charges" contracts are expensive at some hospitals and cheap at others. If that's because the percentage is applied to very different sticker prices, the sticker-price level and the insurer-price level should only partly line up.

**Method:** the same index as query 05, for sticker prices and insurer prices side by side (1.0 = typical across hospitals; median over procedures listed by at least 8 hospitals).

Query: [`sql/08_sticker_price_levels.sql`](../sql/08_sticker_price_levels.sql)

| hospital | procedures_compared | sticker_price_index | insurer_price_index |
|---|---|---|---|
| Boston Medical Center Brighton | 15 | 0.54 | 1 |
| Beth Israel Deaconess Hospital–Milton | 15 | 0.75 | 0.73 |
| Beth Israel Deaconess Hospital–Needham | 10 | 0.84 | 0.91 |
| Winchester Hospital | 16 | 0.87 | 0.89 |
| Tufts Medical Center | 15 | 0.89 | 0.88 |
| Cambridge Health Alliance | 15 | 0.93 | 1.22 |
| Mount Auburn Hospital | 15 | 0.98 | 0.99 |
| New England Baptist Hospital | 15 | 0.98 | 0.69 |
| Lahey Hospital & Medical Center | 16 | 1 | 1.02 |
| Salem Hospital | 13 | 1.02 | 1.13 |
| Beth Israel Deaconess Medical Center | 16 | 1.06 | 1.07 |
| Brigham and Women's Faulkner Hospital | 12 | 1.09 | 1.1 |
| Newton-Wellesley Hospital | 13 | 1.13 | 1.13 |
| South Shore Hospital | 15 | 1.17 | 0.6 |
| Boston Medical Center | 16 | 1.22 | 1 |
| Brigham and Women's Hospital | 15 | 1.38 | 1.89 |
| Massachusetts General Hospital | 14 | 1.38 | 1.88 |

## 09. Price vs quality

**Question:** Do more expensive hospitals have higher CMS quality ratings?

**Why it matters:** a common defense of high prices is higher quality. If high-rated hospitals are also available at lower prices, patients and employers can pay less without choosing lower-rated care.

**Method:** each hospital's commercial price index (as in query 05) next to its CMS overall star rating (1-5, from CMS Hospital General Information). The star rating summarizes measures such as mortality, safety, readmissions and patient experience; it is not a measure of every service compared here.

Query: [`sql/09_price_vs_quality.sql`](../sql/09_price_vs_quality.sql)

| hospital | cms_stars | price_index | procedures_compared |
|---|---|---|---|
| New England Baptist Hospital | 5 | 0.71 | 17 |
| Beth Israel Deaconess Hospital–Needham | 5 | 0.94 | 11 |
| Brigham and Women's Faulkner Hospital | 5 | 1.1 | 12 |
| Salem Hospital | 5 | 1.13 | 13 |
| Newton-Wellesley Hospital | 5 | 1.13 | 13 |
| Massachusetts General Hospital | 5 | 1.88 | 14 |
| Brigham and Women's Hospital | 5 | 1.89 | 15 |
| Beth Israel Deaconess Hospital–Milton | 4 | 0.73 | 17 |
| Mount Auburn Hospital | 4 | 1 | 18 |
| Lahey Hospital & Medical Center | 4 | 1.04 | 18 |
| Winchester Hospital | 3 | 0.89 | 18 |
| Boston Medical Center | 3 | 1 | 17 |
| Boston Medical Center Brighton | 3 | 1 | 15 |
| Beth Israel Deaconess Medical Center | 3 | 1.12 | 18 |
| Cambridge Health Alliance | 3 | 1.22 | 15 |
| South Shore Hospital | 2 | 0.63 | 18 |
| Tufts Medical Center | 2 | 0.9 | 16 |

## 10. Quality summary

**Question:** Summarized by star rating, how do prices compare, and how strong is the link?

**Why it matters:** turns query 09's list into one comparison, plus a rank correlation as a rough measure of how consistently price rises with rating (1 = always rises, 0 = no link, -1 = always falls). With fewer than 20 hospitals this is descriptive only, not proof of any cause.

**Method:** Spearman rank correlation = the ordinary (Pearson) correlation of the ranks, where tied values share their average rank (many hospitals share the same star rating).

Query: [`sql/10_quality_summary.sql`](../sql/10_quality_summary.sql)

| group_name | hospitals | lowest_price_index | median_price_index | highest_price_index | rank_correlation |
|---|---|---|---|---|---|
| 2 stars | 2 | 0.63 | 0.76 | 0.9 |  |
| 3 stars | 5 | 0.89 | 1 | 1.22 |  |
| 4 stars | 3 | 0.73 | 1 | 1.04 |  |
| 5 stars | 7 | 0.71 | 1.13 | 1.89 |  |
| All rated hospitals | 17 | 0.63 | 1 | 1.89 | 0.42 |

## 11. Percent of medicare by hospital

**Question:** compared with what Medicare pays for the same service, how much do commercial insurers pay each hospital? This is the yardstick used by national hospital price studies (e.g. RAND), so the result can be compared with them.

**Method:** each hospital's typical commercial price for a procedure / Medicare's rate for it; then the median across that hospital's procedures. Only procedures with a Medicare rate (15 of 18); hospitals need at least 8.

Query: [`sql/11_percent_of_medicare_by_hospital.sql`](../sql/11_percent_of_medicare_by_hospital.sql)

| hospital | procedures_compared | pct_of_medicare | lowest_pct | highest_pct | procedures_below_medicare |
|---|---|---|---|---|---|
| Beth Israel Deaconess Hospital–Milton | 14 | 113 | 68 | 187 | 3 |
| South Shore Hospital | 15 | 118 | 68 | 232 | 5 |
| New England Baptist Hospital | 15 | 123 | 96 | 156 | 1 |
| Tufts Medical Center | 13 | 131 | 81 | 256 | 1 |
| Winchester Hospital | 15 | 154 | 100 | 220 | 0 |
| Mount Auburn Hospital | 15 | 159 | 106 | 249 | 0 |
| Boston Medical Center | 15 | 176 | 52 | 325 | 2 |
| Beth Israel Deaconess Hospital–Needham | 10 | 191 | 128 | 199 | 0 |
| Beth Israel Deaconess Medical Center | 15 | 194 | 106 | 255 | 0 |
| Brigham and Women's Faulkner Hospital | 11 | 202 | 166 | 710 | 0 |
| Salem Hospital | 11 | 206 | 159 | 752 | 0 |
| Boston Medical Center Brighton | 13 | 214 | 92 | 266 | 2 |
| Newton-Wellesley Hospital | 11 | 215 | 162 | 710 | 0 |
| Lahey Hospital & Medical Center | 15 | 225 | 86 | 275 | 2 |
| Cambridge Health Alliance | 13 | 263 | 143 | 349 | 0 |
| Brigham and Women's Hospital | 13 | 321 | 171 | 1,178 | 0 |
| Massachusetts General Hospital | 12 | 352 | 177 | 1,180 | 0 |

## 12. Percent of medicare by procedure

**Question:** which services are priced furthest above Medicare?

**Method:** for each procedure, every hospital's typical commercial price / Medicare's rate; median, lowest and highest across hospitals. Lab tests are paid under a different Medicare fee schedule (CLFS) than imaging, visits and procedures (OPPS), which is shown in the medicare_system column.

Query: [`sql/12_percent_of_medicare_by_procedure.sql`](../sql/12_percent_of_medicare_by_procedure.sql)

| procedure | medicare_system | medicare_rate | hospitals | median_pct_of_medicare | lowest_pct | highest_pct |
|---|---|---|---|---|---|---|
| Complete blood count (CBC) | CLFS | 7.77 | 17 | 249 | 123 | 1,155 |
| Cholesterol (lipid) panel | CLFS | 13.39 | 17 | 246 | 131 | 868 |
| Comprehensive metabolic panel | CLFS | 10.56 | 17 | 244 | 129 | 1,180 |
| MRI knee (no contrast) | OPPS | 286 | 17 | 220 | 118 | 503 |
| CT abdomen and pelvis (with contrast) | OPPS | 418 | 16 | 219 | 115 | 325 |
| Abdominal ultrasound (complete) | OPPS | 125 | 17 | 214 | 103 | 338 |
| MRI brain (no contrast) | OPPS | 286 | 18 | 200 | 118 | 565 |
| MRI lower back (no contrast) | OPPS | 286 | 17 | 198 | 118 | 477 |
| ECG (electrocardiogram, hospital tracing) | OPPS | 70.7 | 18 | 161 | 90 | 331 |
| Colonoscopy (diagnostic) | OPPS | 1,115 | 17 | 143 | 81 | 177 |
| ER visit (serious) | OPPS | 500 | 13 | 143 | 93 | 401 |
| ER visit (moderate) | OPPS | 327 | 12 | 137 | 86 | 272 |
| Cataract surgery | OPPS | 2,766 | 8 | 123 | 52 | 174 |
| Chest X-ray (2 views) | OPPS | 104 | 17 | 107 | 68 | 349 |
| Knee arthroscopy (meniscus) | OPPS | 3,921 | 9 | 107 | 64 | 168 |
