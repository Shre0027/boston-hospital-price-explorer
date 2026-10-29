# Requirements

> **How this was written:** the first version of the project was built quickly to test whether the data was usable at all. These requirements were then written up from the decisions in the [decision log](decision-log.md) and used as the checklist for every later change. Each requirement links to where it's met and how it was checked.

## 1. Problem and goal

**Problem:** US hospitals must publish their prices (CMS Hospital Price Transparency, 45 CFR Part 180), but the files are too large and inconsistent for patients or employers to use. People can't compare prices before getting care.

**Goal:** let a non-technical person compare what Greater Boston hospitals charge for common procedures, by who's paying, next to a quality signal, and show honestly where the published data falls short.

**Success measures:**
- A person can answer "where is this procedure cheapest for my insurance?" in under a minute, with no data skills.
- Every number shown can be traced back to a row in a hospital's official file.
- The data stays current without manual work.

## 2. Stakeholders

| Stakeholder | Need | Priority |
|---|---|---|
| Patients, especially uninsured or high-deductible | Compare prices before booking; understand what they might owe | Primary |
| Employers that self-insure | See which hospitals and contract types drive cost | Secondary |
| Regulators, policymakers, journalists | Evidence on whether files are actually usable | Secondary |
| Hiring managers (portfolio audience) | See the reasoning, not just the output | Secondary |

## 3. User stories and acceptance criteria

**US-1: Compare one procedure.** As a patient, I want to see one procedure's price at every hospital, so that I can pick a cheaper one.
- AC-1.1: Given a procedure and "who's paying" (cash, typical commercial, or a named insurer), the dashboard shows one value per hospital, sorted lowest to highest.
- AC-1.2: Hospitals with no comparable price say why ("Not listed", or "too few plan prices") instead of showing nothing.
- AC-1.3: A one-sentence summary states the lowest and highest price and how many times higher.

**US-2: Ask in plain English.** As a patient, I want to type a question like "knee MRI with Blue Cross", so that I don't have to learn the menus.
- AC-2.1: The search recognizes the procedure, insurer or cash, and an optional hospital, and shows what it understood.
- AC-2.2: Every number comes from the published data; the search never generates a price.
- AC-2.3: If no procedure is recognized, it says so and lists the procedures it knows.
- AC-2.4: An empty question shows an inline error and does nothing else.

**US-3: Estimate my own cost.** As an insured patient, I want to enter my deductible and coinsurance, so that I see roughly what I'd pay, not just what the hospital is paid.
- AC-3.1: Given the deductible left to meet and a coinsurance percentage, each hospital shows an estimated out-of-pocket cost using the selected price.
- AC-3.2: The estimate is labeled as an estimate, with what it leaves out (copays, out-of-pocket maximum, doctors' fees, plan rules).
- AC-3.3: Invalid inputs (negative, coinsurance over 100%) show an inline error and no estimate.

**US-4: See price next to quality.** As a patient or employer, I want to see each hospital's overall price level next to its CMS star rating, so that I can avoid paying more without getting more.
- AC-4.1: Each hospital with enough data shows a price level (1.0× = typical) grouped by CMS star rating.
- AC-4.2: The page states the strength of the price–rating link and that it isn't proof of cause.

**US-5: See every procedure at once.** As an employer, I want a grid of all procedures by hospital, filterable by health system, so that I can spot patterns.
- AC-5.1: Cells are shaded relative to the typical price for that procedure, with a legend.
- AC-5.2: Selecting a row opens that procedure in the single-procedure comparison.

**US-6: Know how usable each file is.** As a regulator or journalist, I want each hospital's file problems listed, so that I can see whether the rule works in practice.
- AC-6.1: For each hospital: whether the official link list worked, whether automated download worked, procedures found, commercial insurers listed, and share of rows set aside.
- AC-6.2: Problems are described factually, with the evidence (e.g. "HTTP 403").

**US-7: Trust the numbers.** As any user, I want comparisons to be fair, so that I'm not misled by quirks in the files.
- AC-7.1: Procedures are matched by billing code, not by name.
- AC-7.2: Rows that can't be compared fairly are flagged and excluded, never silently dropped (formula rates without an amount paid, rates above the sticker price, impossible values).
- AC-7.3: A "typical" price needs at least 3 plan prices.
- AC-7.4: Every method choice and correction is recorded in the decision log.

**US-8: Understand the findings without exploring.** As a first-time visitor (including a reviewer with a few minutes), I want the main findings shown in order, so that I understand them before I use the tools.
- AC-8.1: The front page walks through the findings in sequence, with one chart that updates at each step.
- AC-8.2: Every number in the story is computed from the same data as the dashboard, so it updates with the monthly refresh.
- AC-8.3: The dashboard is one click away from any point in the story.

## 4. Non-functional requirements

| Id | Requirement | Measure |
|---|---|---|
| NFR-1 Accuracy | Numbers match the source files | Row counts match per hospital; random rows traced to source with 0 mismatches |
| NFR-2 Reproducibility | Anyone can rerun the analysis and get the same result | One command per step; SQL results identical across repeated runs |
| NFR-3 Freshness | Data updates without manual work | Monthly scheduled refresh; failed hospitals keep their previous data |
| NFR-4 Scale | Handle files up to several GB | Files read row by row (streaming); largest so far 1.7 GB, 5.9M rows |
| NFR-5 Cost | Free to run and host | GitHub Actions and GitHub Pages only; no paid services or API keys |
| NFR-6 Safety | Never invent or overstate a price | No AI-generated numbers; out-of-pocket figures labeled as estimates |
| NFR-7 Access | Usable on a phone and readable in dark mode | Checked at 390 px wide and in dark mode; no horizontal page scroll |
| NFR-8 Respect for sites | Don't get around access controls | Blocked sites are not worked around; files are downloaded by hand instead, and the block is reported |
| NFR-9 Privacy | No personal data | Only published prices and public ratings; the estimator runs in the browser and stores nothing |
| NFR-10 Accessibility | Readable for people with low vision; usable without animation | No WCAG 2 A/AA violations in an automated scan (axe-core), light and dark mode; reduced-motion setting shows final values |

## 5. Out of scope

- Exact out-of-pocket cost for a specific person's plan (needs plan documents and claims data).
- Physician fees, which are billed separately from hospital facility charges.
- Quality measures beyond the CMS overall star rating.
- Children's, cancer, psychiatric and rehabilitation hospitals.

## 6. Traceability

| Requirement | Where it's met | How it was checked | Status |
|---|---|---|---|
| US-1 | Dashboard "Look up a price" (`templates/dashboard.html`) | Browser checks at desktop and phone width | Done |
| US-2 | Plain-English search (`templates/dashboard.html`) | 30 test questions, 30 understood; one answer matched an independent calculation | Done |
| US-3 | Out-of-pocket estimator (`templates/dashboard.html`) | Worked examples checked by hand; invalid inputs tested | Done |
| US-4 | "Do higher-rated hospitals cost more?" section; `sql/09`, `sql/10` | Dashboard index matches SQL for all 17 indexed hospitals; correlation matches an independent Python calculation | Done |
| US-5 | "Every procedure at a glance" grid (collapsed by default) | Browser checks; system filter and row selection | Done |
| US-6 | File-usability table; `config/data_access.json` | Each finding recorded with evidence in the decision log | Done |
| US-7 | `scripts/combine.py`, `sql/00_setup.sql` | Mapping of every insurer name reviewed by hand; flagged rows counted per hospital (`sql/06`) | Done |
| US-8 | Scroll-driven story (`templates/story.html`, published as `site/index.html`) | Every step tested on desktop and phone; story numbers checked against SQL results | Done |
| NFR-10 | Both pages | axe-core scan: 0 violations in light and dark mode (after raising text and button contrast) | Done |
| NFR-1 | `scripts/combine.py` | 180 random rows across 18 hospitals traced to source, 0 mismatches | Done |
| NFR-2 | `scripts/run_sql.py` | Four consecutive runs, identical output | Done |
| NFR-3 | `.github/workflows/refresh.yml` | Manual end-to-end run: all hospitals downloaded, rebuilt and republished | Done |
| NFR-4 | `scripts/extract_prices.py` | Tufts Medical Center file (1.7 GB, 5.9M rows) processed in 28.7 seconds with 21 MB peak memory (measured 2026-10-29) | Done |
| NFR-8 | Tufts Medicine handling in `config/hospitals.json` | Blocked file downloaded by hand; MelroseWakefield pending | Done |

## 7. Open issues

| Issue | Impact | Next step |
|---|---|---|
| MelroseWakefield Hospital not included | One in-scope hospital missing | Download its file by hand from Tufts Medicine's cost-estimate page |
| Beth Israel Lahey Health files list only 3–6 commercial insurers | Their typical prices rest on fewer plans | Recheck when the files update |
| Typical prices aren't weighted by how many patients use each plan | A rarely used plan counts as much as a common one | Would need enrollment data, which isn't public |
