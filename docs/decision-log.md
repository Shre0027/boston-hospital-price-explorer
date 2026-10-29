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

**Early example (knee MRI, CPT 73721, insurer-negotiated price):** Harvard Pilgrim's rate is $230.56 at MGH and $673.24 at BIDMC.

**Added along the way:**
- A discovery workflow that reads each hospital system's `cms-hpt.txt` and saves every location and file link to `data/discovery.json`.
- JSON support (BIDMC and the rest of Beth Israel Lahey Health publish JSON). JSON rows are flattened into the same column layout as the CSV files, checked against CMS's sample data: the JSON and CSV versions of the same sample produce identical rows.
- Name matching that ignores apostrophe style (`Women’s` vs `Women's`).

**Mistake and fix:** Deleting local test output also deleted committed results, and the next commit removed the MGH and Brigham files from the repo. They were restored from git history, and test runs now write to a separate folder (`PRICES_OUT_DIR`) so this can't happen again.

---

## 2026-10-29: Run data collection on GitHub Actions

**Decision:** Download and filter the large price files on GitHub Actions.

**Why:** Files can exceed 1 GB. GitHub Actions can download a file, keep only the selected procedures, and save a small result, with no local machine needed. It can also re-run on a schedule so the data stays current.
