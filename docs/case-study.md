# Case study: Can Boston patients actually compare hospital prices?

> **Status: draft for review.** Numbers come from [`analysis/README.md`](../analysis/README.md) (SQL queries in [`sql/`](../sql/)); method details and every correction are in the [decision log](decision-log.md). Live dashboard: https://shre0027.github.io/boston-hospital-price-explorer/

## Summary

Since 2021, every US hospital has had to publish its prices in a machine-readable file. I collected these files from **18 Greater Boston hospitals**, standardized over 11,000 published prices for 18 common procedures, put them next to each hospital's CMS quality rating, and asked three questions: **do prices differ enough to matter, does higher price mean higher quality, and can anyone actually use this data?**

- **Prices differ a lot.** With commercial insurance, the same blood test costs about **9× more** at the most expensive hospital than the cheapest, and a brain MRI about **5× more**.
- **Two hospitals stand apart.** MGH and Brigham and Women's are about **1.9×** the typical price across procedures. Mass General Brigham's own community hospitals (Faulkner, Newton-Wellesley, Salem) are about **1.1×**.
- **Higher price only loosely tracks quality.** The seven 5-star hospitals range from **0.71×** the typical price (New England Baptist) to **1.89×** (Brigham). Across 17 rated hospitals, the rank correlation between price and rating is **0.42**: a loose link, not a rule.
- **"Transparency" is uneven in practice.** One system blocked automated downloads, one hospital's official link was broken, five files broke a standard JSON parser, one file contained impossible prices, and every Beth Israel Lahey Health hospital listed only 3–6 commercial insurers.

## 1. The problem

Patients usually learn what a hospital service costs only when the bill arrives. Federal rules (CMS Hospital Price Transparency, 45 CFR Part 180) have required hospitals since January 2021 to publish all their prices, including what each insurer pays, and the rules were tightened again in 2026. But the files are built for machines: one Boston hospital's file has **5.9 million rows** (1.7 GB). The data is public, yet in practice no patient can read it.

## 2. Who cares, and what they need to know

| Stakeholder | Their question | What this project gives them |
|---|---|---|
| Patients (especially uninsured or high-deductible) | "Where can I get this done for less, without giving up quality?" | Side-by-side prices, CMS ratings, and a plain-English search |
| Employers that self-insure their staff | "Are we overpaying for routine care?" | Hospital price levels, contract types, and same-insurer price spreads |
| Insurers | "How do our rates compare across hospitals?" | What each insurer pays the same service at different hospitals |
| Regulators and policymakers | "Is the transparency rule working?" | Evidence on how usable each hospital's file really is |

## 3. Scope and approach

- **Hospitals (18):** general acute-care hospitals within about 15 miles of downtown Boston, from Mass General Brigham (6), Beth Israel Lahey Health (7), BMC Health System (2), Tufts Medicine, Cambridge Health Alliance and South Shore Health, plus two specialty hospitals (Mass Eye and Ear, New England Baptist). Children's, cancer, psychiatric and rehabilitation hospitals are excluded. MelroseWakefield (Tufts Medicine) is not yet included because Tufts Medicine blocks automated downloads.
- **Procedures (18):** common services patients can plan ahead for (imaging, labs, colonoscopy, ER and office visits, a few surgeries), matched by **billing code**, because each hospital names services differently. Codes were chosen to match how hospitals actually bill: the hospital's part of an ECG (CPT 93005), and gallbladder removal as an inpatient stay (MS-DRG 419).
- **Pipeline:** find each file through the hospital's official `cms-hpt.txt`; download and filter it (CSV, zipped CSV or JSON); standardize 404 different insurer names into recognizable brands and markets; choose one fair comparison price per row; analyze with SQL; publish a dashboard. It refreshes automatically every month.
- **Fair comparison rules:** commercial insurance only; when a rate comes from a formula, use the hospital-reported median amount actually paid; set aside rates that may not be the real payment and impossible values; a hospital's "typical" price needs at least 3 plan prices.
- **Quality:** CMS overall star rating (1–5) from CMS Hospital General Information, matched by CMS Certification Number.

**Definitions used below:** *sticker price* = the hospital's gross charge; *cash price* = its listed price for patients paying without insurance; *typical commercial price* = median across the commercial plans a hospital lists; *price level* = a hospital's typical price divided by the typical price across hospitals, median over procedures (1.0× = typical).

## 4. Findings

### Finding 1: The same procedure can cost several times more depending on the hospital

Typical commercial price, cheapest vs most expensive hospital ([query 02](../analysis/README.md#02-price-gap-by-procedure)):

| Procedure | Cheapest | Most expensive | Gap |
|---|---|---|---|
| Complete blood count | Tufts MC, $10 | MGH, $90 | 9.4× |
| Comprehensive metabolic panel | Tufts MC, $14 | MGH, $125 | 9.1× |
| MRI brain (no contrast) | South Shore, $338 | MGH, $1,614 | 4.8× |
| Colonoscopy (diagnostic) | Tufts MC, $905 | MGH, $1,975 | 2.2× |

The biggest relative gaps are in routine lab tests; the biggest dollar gaps are in imaging and hospital stays. For patients paying cash, a brain MRI is **$449** at BMC Brighton and **$3,858** at MGH and Brigham (8.6×).

### Finding 2: Price level is a hospital-wide pattern, and two hospitals stand apart

The price level ([query 05](../analysis/README.md#05-overall-hospital-ranking)) compares each hospital with the typical hospital on up to 18 procedures:

- **Lowest:** South Shore 0.63×, New England Baptist 0.71×, BID Milton 0.73×.
- **Around typical:** BMC, BMC Brighton and Mount Auburn 1.00×; Lahey 1.04×; BIDMC 1.12×.
- **Highest:** MGH 1.88× and Brigham and Women's 1.89×, above typical on every procedure compared.
- **Same system, different prices:** Mass General Brigham's community hospitals (Faulkner 1.10×, Newton-Wellesley 1.13×, Salem 1.13×) are far closer to typical than its two academic medical centers. Within Beth Israel Lahey Health, BIDMC (1.12×) is well above BID Milton (0.73×) and New England Baptist (0.71×).

### Finding 3: Higher-rated hospitals cost somewhat more, but top-rated care exists at low prices

Price level next to CMS star rating ([queries 09–10](../analysis/README.md#09-price-vs-quality)):

| CMS rating | Hospitals | Price level range | Median |
|---|---|---|---|
| 5 stars | 7 | 0.71× – 1.89× | 1.13× |
| 4 stars | 3 | 0.73× – 1.04× | 1.00× |
| 3 stars | 5 | 0.89× – 1.22× | 1.00× |
| 2 stars | 2 | 0.63× – 0.90× | 0.76× |

The rank correlation between price level and rating is **0.42** across 17 rated hospitals (1 would mean price always rises with rating). Two 5-star hospitals, New England Baptist (0.71×) and BID Needham (0.94×), are priced **below** typical. So a patient or employer can often choose top-rated care without paying top prices. With 17 hospitals this is descriptive, not proof of cause, and a star rating summarizes overall hospital quality, not each procedure.

### Finding 4: The same insurer pays very different prices at different hospitals

([query 04](../analysis/README.md#04-same-insurer-different-hospitals))
- UnitedHealthcare: complete blood count **$7 at BID Milton vs $98 at MGH and Brigham** (15×).
- Aetna: brain MRI **$286 at South Shore and Winchester vs $3,634 at MGH** (13×).

These costs feed into the premiums that employers and employees pay.

### Finding 5: Price depends on sticker-price level combined with contract type

I expected insurer contracts paid as a **percent of the hospital's billed charges** to be more expensive than fixed **fee schedules**. Comparing within the same hospital ([query 07](../analysis/README.md#07-contract-type-effect)):
- At **BMC**, percent-of-charges contracts cost a median **2.5×** more than fee schedules (14 of 16 procedures); at **Cambridge Health Alliance**, **3.3×** (14 of 15).
- At **Tufts MC**, they were **cheaper** (0.64×, for 14 of 15 procedures).

Sticker prices explain the difference ([query 08](../analysis/README.md#08-sticker-price-levels)). Tufts MC has below-typical sticker prices (0.89×), so a percentage of them is cheap. MGH and Brigham have the highest sticker prices (1.38×) and tie contracts to them, and their insurer prices are the highest (about 1.9×). South Shore shows the opposite case: above-typical sticker prices (1.17×) but the lowest insurer prices (0.60×), because its contracts aren't tied to its charges.

**Takeaway:** what an insurer pays depends on the sticker price *and* on whether the contract is tied to it. This is a consistent pattern, not proof of cause.

### Finding 6: Uninsured patients can pay far more than insurers

([query 03](../analysis/README.md#03-cash-vs-insured)) For a comprehensive metabolic panel, the cash price is **$414** at New England Baptist (insurers typically pay **$16**, 26×) and **$658** at BIDMC (insurers pay **$26**, about 25×). At South Shore, the cash price for a CT scan is **$4,123** vs **$483** typical commercial (8.5×). Lab tests and imaging show the widest gaps.

### Finding 7: The data is public, but not always usable

| What happened | Where |
|---|---|
| Automated downloads **blocked** (HTTP 403); a person could download the file in a browser | Tufts Medical Center (Tufts Medicine) |
| The old official link list redirected to a web page, and its file link returned "not found" | MGH |
| JSON files started with a byte-order mark, which the JSON standard says not to add; a standard parser rejected them | 4 Beth Israel Lahey Health hospitals and South Shore |
| Only **3–6 commercial insurers** listed (vs 8–11 at the Mass General Brigham, BMC, Tufts and Cambridge Health Alliance hospitals), so several "typical" prices rest on too few plans to show | All 7 Beth Israel Lahey Health hospitals |
| Impossible prices, such as **$0.03** for a blood count and about **$5** for a colonoscopy | Cambridge Health Alliance |
| About **40%** of matched rows couldn't be compared reliably (formula rates with no amount paid, or rates above the sticker price) | BMC (38%) and BMC Brighton (43%) |
| The gallbladder-removal stay priced for **Medicare plans only** | MGH, Brigham, Faulkner |

## 5. Recommendations

**Patients**
- For plannable outpatient services (lab work, imaging, screening), compare prices before booking; the location can change the price several times over.
- Use quality ratings together with price: several 4- and 5-star hospitals are priced at or below typical.
- If paying without insurance, ask for the cash price and about financial assistance before the service; listed cash prices can be many times what insurers pay.

**Employers that self-insure**
- Review where employees get routine labs and imaging; the same service can cost several times more within the same health system.
- When negotiating, pay attention to contracts paid as a percent of billed charges at hospitals with high sticker prices.

**Regulators and hospitals**
- Check that files can be reached **automatically**, since the rule exists so that tools can read them, and that they parse with standard tools.
- Check that official link lists stay current after website changes, that files list all contracted insurers, and that obviously impossible values are caught before publishing.

## 6. Limitations

- These are **prices paid to the hospital, not a patient's out-of-pocket cost**, which depends on deductibles, copays and plan design.
- Typical commercial prices are medians across listed plans, **not weighted** by how many patients use each plan. Beth Israel Lahey Health hospitals list fewer insurers, so their typical prices rest on fewer plans.
- **Facility charges only**; physicians may bill separately. Some rates are bundled with other services (flagged rows were excluded).
- CMS star ratings summarize overall hospital quality, not each procedure. Mass Eye and Ear has no rating and too few comparable procedures for a price level.
- **18 hospitals and 18 procedures** in one metro area. Findings are **associations**, not causes.
- Prices are as published in each hospital's file (updated March–April 2026), collected October 2026; CMS ratings as of July 2026.

## 7. Next steps

1. Add MelroseWakefield Hospital (Tufts Medicine) by downloading its file by hand, as was done for Tufts Medical Center.
2. Estimate out-of-pocket cost for common plan types (deductible and coinsurance) to make prices more meaningful for patients.
3. Track price changes month to month using the automatic refresh.
4. Share findings with a Massachusetts health-policy audience for feedback.
