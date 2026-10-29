# Decision Log

A running record of the key decisions in this project: what was decided, why, and what was rejected. AI tools (Claude) are used to help build this project; this log records the reasoning and choices behind the work.

---

## 2026-10-29: Project choice

**Decision:** Build a Boston hospital price comparison tool using public CMS price transparency files.

**Why:**
- Solves a real problem: patients can't compare hospital prices before getting care, even though hospitals are legally required to publish them.
- Uses real, public, messy data instead of a pre-cleaned tutorial dataset.
- Healthcare is a major Boston industry and a target industry for this portfolio.

**Rejected:** A job-postings analysis tool. It was solid, but similar projects are common, and it had less real-world impact.

---

## 2026-10-29: Data availability check (before committing)

**Decision:** Confirmed price files are published before starting the build.

**Findings:**
- MGH, BMC and BIDMC/BILH hospitals publish machine-readable files with public download links.
- File quality varies widely. MGH's file is about 1.8 GB with millions of price rows, while some other files in the same region are a few MB.
- In one third-party snapshot, a hospital download link resolved to a tiny junk file instead of real data.

**Implication:** Data quality itself becomes one of the project's findings: can patients actually use what hospitals publish?

---

## 2026-10-29: Scope for Phase 1

**Decision:** Start with 5 hospitals and about 18 procedures, then expand.

**Hospitals:** Massachusetts General Hospital, Brigham and Women's, Boston Medical Center, Beth Israel Deaconess Medical Center, Tufts Medical Center.

**Why 5, not 30:** Every hospital formats its file differently (CSV vs JSON, different sizes and layouts). Building a working end-to-end pipeline on a small set first avoids weeks of fighting formats before seeing any result. Adding hospitals later should mostly mean adding a file link.

**Planned phases:**
1. 5 Boston hospitals, end to end
2. About 15 Greater Boston hospitals
3. (Optional) All Massachusetts hospitals

---

## 2026-10-29: Match procedures by billing code, not name

**Decision:** Compare procedures using CPT billing codes (for example, knee MRI = 73721) instead of description text.

**Why:** Hospitals describe the same service differently ("MRI knee" vs "MR LOWER EXT JOINT W/O"), but the billing code is the same everywhere. The code works as a common key across hospitals, like a join key in SQL.

**Next:** Confirm each code against the CMS shoppable services list.

---

## 2026-10-29: First real extraction (MGH) and what broke along the way

**Result:** MGH's file (version 3.0.0, last updated 2026-03-27) has 159,489 price rows. 535 matched our procedures. 14 of 18 procedures were found. Cataract surgery, knee arthroscopy, gallbladder removal and ECG were not found under the chosen codes; to investigate.

**Problems hit, and fixes:**
1. **The saved file link returned 404.** MGH's website was merged into Mass General Brigham's, and the old file address stopped working. *Fix:* read the link from the hospital's `cms-hpt.txt`, the discovery file CMS requires at every hospital's website root, so the pipeline follows future moves automatically.
2. **The old discovery file address now redirects to a regular web page.** `massgeneral.org/cms-hpt.txt` no longer works; the current one is `massgeneralbrigham.org/cms-hpt.txt`. A patient or researcher following MGH's old official address would hit a dead end. *Logged as a data-access finding.*
3. **The downloaded file looked corrupted.** The server compresses its response (gzip) on top of the zip file. Browsers undo this automatically; Python's basic downloader does not. *Fix:* detect the compression and undo it. Verified against a local test server before re-running.
4. **GitHub's run logs weren't readable from the build environment.** *Fix:* the script now writes its key results and errors as GitHub annotations, which show directly on the run's summary page.

**Lesson:** Build in clear error reporting first. The first two failed runs gave no useful detail; once the script showed exactly what the server returned, the real cause was found in one run.

---

## 2026-10-29: Four hospitals extracted; what the files reveal

| Hospital | File type | Last updated | Rows in file | Matching rows | Insurers listed | Procedures found |
|---|---|---|---|---|---|---|
| MGH | zipped CSV | 2026-03-27 | 159,489 | 535 | 30 | 14 of 18 |
| Brigham and Women's | zipped CSV | 2026-03-27 | 109,293 | 507 | 30 | 14 of 18 |
| BMC | zipped CSV | 2026-03-13 | 1,329,567 | 1,610 | 77 | 16 of 18 |
| BIDMC | JSON | 2026-04-01 | 90,199* | 96 | 6 | 18 of 18 |
| Tufts Medical Center | — | — | — | — | — | not accessible |

*For JSON files, "rows" means rows after flattening (service × setting × insurer plan).

**Findings to verify:**
- Both Mass General Brigham hospitals have no price under the chosen codes for cataract surgery, knee arthroscopy, gallbladder removal or ECG. BMC lists cataract surgery and knee arthroscopy, so the codes are valid; the gap is in what MGB publishes under them.
- BIDMC's file lists only 6 insurers (no Aetna, UnitedHealthcare or Tufts Health Plan). Either the file is incomplete or those prices are recorded in a form not yet handled. Needs checking before drawing conclusions.
- Tufts Medical Center's `cms-hpt.txt` returned HTTP 403 (Forbidden) to automated requests on every address tried. CMS requires these files to be accessible without barriers. Not worked around; next step is to check whether a person using a normal browser can reach it.

**Early example (knee MRI, CPT 73721, insurer-negotiated price):** Harvard Pilgrim's rate is $230.56 at MGH and $673.24 at BIDMC. **Corrected below:** the $230.56 is a formula-based case rate, not the full price.

**Added along the way:**
- A discovery workflow that reads each hospital system's `cms-hpt.txt` and saves every location and file link to `data/discovery.json`.
- JSON support (BIDMC and the rest of Beth Israel Lahey Health publish JSON). JSON rows are flattened into the same column layout as the CSV files, checked against CMS's sample data: the JSON and CSV versions of the same sample produce identical rows.
- Name matching that ignores apostrophe style (`Women’s` vs `Women's`).

**Mistake and fix:** Deleting local test output also deleted committed results, and the next commit removed the MGH and Brigham files from the repo. They were restored from git history, and test runs now write to a separate folder (`PRICES_OUT_DIR`) so this can't happen again.

---

## 2026-10-29: One combined table, and how a "comparison price" is chosen

**Decision:** `scripts/combine.py` merges all hospitals into `data/combined/prices_clean.csv` (2,748 rows) with consistent insurer names, a market tag, numeric prices, one comparison price per row, and flags for rows that shouldn't be compared directly.

**Insurer names:** grouped into brands patients recognize (e.g. "BCBS [6001]" and "BLUE CROSS BLUE SHIELD [110001]" → Blue Cross Blue Shield). Market (Commercial, Medicare, MassHealth / safety net, Military, Other public / workers comp) is decided mainly from the payer name. The plan name is used only for clear signals, because at Mass General Brigham the plan column is often a pricing label (e.g. "GENERIC COMMERCIAL" next to "HB MGH MEDICARE"). Pricing notes in brackets, like "(130% OF MEDICARE)", are ignored, since they describe how a price is calculated rather than who the customer is. Every insurer mapping was reviewed by hand after each change.

**Retired contracts:** BMC lists insurers with a "ZZZ" prefix (e.g. "ZZZUNITED"); these are tagged Inactive and excluded (254 rows).

**Correction:** An earlier comparison said Harvard Pilgrim pays $230.56 for a knee MRI at MGH versus $673.24 at BIDMC (about 3x). That was misleading. $230.56 is a "case rate" where the procedures on a claim are sorted and priced together, so it can be only part of the payment. MGB also reports the median amount actually paid for these rows: $627–$689 for Harvard Pilgrim plans.

**Comparison price rule:**
1. If the rate is set by a formula and the hospital reports a median amount actually paid → use the median.
2. Otherwise, if there's a negotiated dollar amount → use it.
3. Otherwise, if there's a median → use it.

**Flags (kept in the table, excluded from comparisons):**
- Insurer rate above the sticker price (148 rows, mostly BMC): likely a bundled rate covering more than the single line item.
- Rate set by a formula with no amount-paid figure (513 rows, all BMC): the listed amount may be only part of the payment.

**Verification:** Row counts match the per-hospital files exactly; 100 random rows traced back to the source with 0 mismatches.

**First results (commercial insurance, median across plans, unflagged rows, no modifiers):**
- MGH and Brigham share identical cash prices, consistent with one system-wide price list.
- Blood tests cost far more at the MGB hospitals: a complete blood count is about $87–90 there vs $14 at BMC and $19 at BIDMC; a metabolic panel is about $124–125 vs $19–26.
- A brain MRI (no contrast) is a median $1,614 at MGH vs $574 at BMC.
- Uninsured (cash) prices can far exceed insurer rates: BIDMC's cash price for a metabolic panel is $658, while its insurers pay $20–38.
- BMC has the lowest cash price for most procedures.

**Caveats:** Medians are across listed plans, not weighted by how many patients use each plan. These are amounts paid to the hospital, not a patient's out-of-pocket cost.

---

## 2026-10-29: Tufts Medical Center added (downloaded by hand)

**What happened:** Tufts Medicine's `cms-hpt.txt` and its price file both returned HTTP 403 (Forbidden) to automated requests from GitHub's servers. A person using a normal browser could find and download the file from the cost-estimate page (tuftsmedicine.org/get-care/cost-estimate, "Price transparency + chargemaster" section).

**Decision:** Not worked around. The file was downloaded by hand in a browser, the way a patient would get it, and processed with the same script. The profile records the source link and `"collected": "downloaded by hand in a browser"`, and `config/hospitals.json` notes the 403.

**Finding:** Tufts' file is published, but automated access, the "machine-readable" route the rule is meant to enable, was blocked for this project.

**Result:** 1.74 GB CSV (version updated 4/1/2026), 5,877,884 rows, 3,842 matching rows, 170 insurer plans, 14 of 18 procedures. Row count matches the source; 50 random rows traced back with 0 mismatches.

**Mapping fixes prompted by Tufts' insurer list** (every changed row was reviewed against the previous version):
- About 80 workers' comp insurers prefixed "WC" were tagged Commercial → now workers comp.
- "Medicare Replacement" / "Medicare Managed" plans from MassHealth-focused insurers (e.g. WellSense) were tagged MassHealth → now Medicare.
- "Tufts Health Public Plan" (MassHealth) was tagged Commercial → now MassHealth. ConnectorCare plans (subsidized private insurance) are tagged Commercial.

**Five-hospital results (commercial insurance, median across plans):**
- Tufts Medical Center is lowest or near-lowest for most procedures: e.g. colonoscopy $905 vs $1,975 at MGH, and a complete blood count $9 vs $90 at MGH.
- Brain MRI (no contrast) cash price: $3,858 at MGH and Brigham vs $1,142 at Tufts.

---

## 2026-10-29: Dashboard published, and a plain-English search instead of a live AI chatbot

**Dashboard:** `scripts/build_site.py` turns the combined table into a small summary embedded in `site/index.html`, published with GitHub Pages: https://shre0027.github.io/boston-hospital-price-explorer/. Checked in a headless browser at desktop and phone widths and in dark mode before publishing. Fixed along the way: unreadable white text on light cells in dark mode, lowercased procedure names, a "$X–$X" range shown when all plans had the same price, and the procedure column scrolling away on phones.

**Decision: plain-English search, not a live AI model.** A hosted AI model needs a secret API key, and a public static site can't keep a key secret: anyone could copy it and run up charges. The search instead uses keyword rules to recognize a procedure, who's paying, and optionally a hospital, and every number it shows is read from the published data, so it can't invent a price. It is described as a search, not as AI.

**Tricky cases handled:** "Mass General Brigham Health Plan" is an insurer, so it isn't read as the MGH or Brigham hospital; "at Tufts" means Tufts Medical Center while "with Tufts" means Tufts Health Plan; questions with no recognizable procedure get an honest "couldn't tell" with the list of procedures.

**Tested:** 16 realistic questions, 16 understood correctly. One answer (CBC at MGH with Aetna: $93, $70–$101 across 6 plans) matched an independent calculation from `prices_clean.csv` exactly.

---

## 2026-10-29: Automatic monthly refresh

**Decision:** `.github/workflows/refresh.yml` runs on the 1st of every month (and on demand). It re-downloads MGH, Brigham, BMC and BIDMC, rebuilds the combined table and the dashboard, saves the results, and republishes the site (by calling `pages.yml`). Tufts Medical Center is skipped because it blocks automated downloads; its hand-downloaded data stays in place.

**Safety fix found while planning this:** the extract script used to write results as it went, so a download that failed halfway could overwrite good data with a partial file. It now writes to temporary files and swaps them in only after a successful run, and refuses to save a run that matched zero procedures. Tested: a broken file left the old results untouched; a good file replaced them. In the refresh workflow, one hospital failing doesn't stop the others.

**Tested end to end:** a manual run downloaded all four hospitals, rebuilt and republished successfully. Prices were unchanged (the hospitals' files hadn't changed), only the extraction timestamps updated, and Tufts' rows were kept. The dashboard now shows when prices were last refreshed and when the access findings were checked.

---

## 2026-10-29: Run data collection on GitHub Actions

**Decision:** Download and filter the large price files on GitHub Actions.

**Why:** Files can exceed 1 GB. GitHub Actions can download a file, keep only the selected procedures, and save a small result, with no local machine needed. It can also re-run on a schedule so the data stays current.
