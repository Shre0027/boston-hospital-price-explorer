# Case study: Can Boston patients actually compare hospital prices?

> **Status: draft for review.** Numbers come from [`analysis/README.md`](../analysis/README.md) (SQL queries in [`sql/`](../sql/)); method details and every correction are in the [decision log](decision-log.md). Live dashboard: https://shre0027.github.io/boston-hospital-price-explorer/

## Summary

Since 2021, every US hospital has had to publish its prices in a machine-readable file. I collected these files from five Boston hospitals, standardized 6,590 published prices for 18 common procedures, and asked two questions: **do prices differ enough to matter, and can a patient actually use this data?**

- **Prices differ a lot.** For patients with commercial insurance, the same blood test costs about **9× more** at the most expensive hospital than the cheapest, and a brain MRI about **2.8× more**.
- **The pattern is consistent, and it's explainable.** Tufts Medical Center is the cheapest for 10 of 14 comparable procedures; MGH and Brigham are typically **2.3–2.9×** the cheapest. What insurers pay tracks two things together: how high a hospital's sticker prices are, and whether insurer contracts are tied to those sticker prices.
- **"Transparency" is uneven in practice.** One hospital blocked automated access to its file, one hospital's official link was broken, one file listed only 6 insurers, and at one hospital 39% of price rows couldn't be compared reliably.

## 1. The problem

Patients usually learn what a hospital service costs only when the bill arrives. Federal rules (CMS Hospital Price Transparency, 45 CFR Part 180) have required hospitals since January 2021 to publish all their prices, including what each insurer pays, and the rules were tightened again in 2026. But the files are built for machines: one Boston hospital's file has **5.9 million rows** (1.7 GB). The data is public, yet in practice no patient can read it.

## 2. Who cares, and what they need to know

| Stakeholder | Their question | What this project gives them |
|---|---|---|
| Patients (especially uninsured or high-deductible) | "Where can I get this done for less?" | Side-by-side prices and a plain-English search |
| Employers that self-insure their staff | "Are we overpaying for routine care?" | Which hospitals and contract types cost more for the same service |
| Insurers | "How do our rates compare across hospitals?" | Same-insurer price spreads across hospitals |
| Regulators and policymakers | "Is the transparency rule working?" | Evidence on how usable each hospital's file really is |

## 3. Scope and approach

- **Hospitals (5):** Massachusetts General Hospital, Brigham and Women's, Boston Medical Center, Beth Israel Deaconess Medical Center, Tufts Medical Center.
- **Procedures (18):** common services patients can plan ahead for (imaging, labs, colonoscopy, ER and office visits, a few surgeries), matched by **billing code (CPT)**, because each hospital names services differently.
- **Pipeline:** find each file through the hospital's official `cms-hpt.txt`; download and filter it (CSV, zipped CSV or JSON); standardize 282 different insurer names into recognizable brands and markets; choose one fair comparison price per row; analyze with SQL; publish a dashboard. It refreshes automatically every month.
- **Fair comparison rules:** commercial insurance only; when a rate comes from a formula, use the hospital-reported median amount actually paid; set aside rows where the listed figure may not be the real payment (and say how many).

**Definitions used below:** *sticker price* = the hospital's gross charge; *cash price* = its listed price for patients paying without insurance; *typical commercial price* = median across the commercial plans a hospital lists.

## 4. Findings

### Finding 1: The same procedure can cost several times more depending on the hospital

Typical commercial price, cheapest vs most expensive hospital ([query 02](../analysis/README.md#02-price-gap-by-procedure)):

| Procedure | Cheapest | Most expensive | Gap |
|---|---|---|---|
| Complete blood count | Tufts MC, $9 | MGH, $90 | 9.5× |
| Comprehensive metabolic panel | Tufts MC, $14 | MGH, $125 | 9.1× |
| MRI brain (no contrast) | Tufts MC, $571 | MGH, $1,614 | 2.8× |
| Colonoscopy (diagnostic) | Tufts MC, $905 | MGH, $1,975 | 2.2× |

The biggest relative gaps are in routine lab tests; the biggest dollar gaps are in imaging and procedures.

### Finding 2: It's a consistent pattern, not a few outliers

Across the 14 procedures listed by at least four hospitals ([query 05](../analysis/README.md#05-overall-hospital-ranking)), Tufts Medical Center was the cheapest for **10 of 14**. Using the median (so a few extreme lab gaps don't dominate), BIDMC and BMC were about **1.4×** the cheapest hospital, Brigham **2.3×** and MGH **2.9×**.

### Finding 3: The same insurer pays very different prices at different hospitals

([query 04](../analysis/README.md#04-same-insurer-different-hospitals))
- UnitedHealthcare: complete blood count **$7 at BMC vs $98 at Brigham** (14×).
- Blue Cross Blue Shield: cholesterol panel **$11 at Tufts MC vs $87 at MGH** (8×).
- It doesn't always favor the same hospital: Cigna pays **$673** for a lower-back MRI at MGH but **$3,429** at BMC (5×).

These costs feed into the premiums that employers and employees pay.

### Finding 4: Price tracks sticker-price level combined with contract type (a hypothesis that was only half right)

I expected insurer contracts paid as a **percent of the hospital's billed charges** to be more expensive than fixed **fee schedules**. Comparing within the same hospital ([query 07](../analysis/README.md#07-contract-type-effect)):
- At **BMC**, percent-of-charges contracts cost a median **2.7×** more than fee schedules (14 of 15 procedures).
- At **Tufts MC**, they were **cheaper** (0.64×, for 13 of 14 procedures).

The difference made sense once I compared sticker prices ([query 08](../analysis/README.md#08-sticker-price-levels)): Tufts has the **lowest** sticker prices of the five, so a percentage of them is cheap. BMC has the **highest** sticker prices but mostly fee-schedule contracts, so insurers pay comparatively little. MGH and Brigham have high sticker prices **and** tie contracts to them, and they are the most expensive.

**Takeaway:** what an insurer pays depends on the sticker price *and* on whether the contract is tied to it. This is a consistent pattern across five hospitals, not proof of cause.

### Finding 5: Uninsured patients can pay far more than insurers

([query 03](../analysis/README.md#03-cash-vs-insured)) At BIDMC, the cash price for a comprehensive metabolic panel is **$658**, while its insurers typically pay **$26** (25×). BIDMC's cash prices for MRIs are **4.6–5.1×** what insurers pay. At MGH, a lower-back MRI is **$3,281** cash vs **$967** typical commercial.

### Finding 6: The data is public, but not always usable

| Hospital | What happened |
|---|---|
| MGH | The old official link list redirected to a web page, and the file link it listed returned "not found"; the current list lives on the Mass General Brigham site |
| Tufts MC | The link list and the price file both **blocked automated downloads** (HTTP 403); a person could download it in a browser |
| BIDMC | The file lists only **6 insurers** (no Aetna, UnitedHealthcare or Tufts Health Plan) |
| BMC | **39%** of matched rows couldn't be compared reliably (formula-based rates with no amount actually paid, or rates above the sticker price) |
| MGH, Brigham, Tufts MC | No price under the standard codes for 4 of the 18 procedures (cataract surgery, knee arthroscopy, gallbladder removal, ECG) |

## 5. Recommendations

**Patients**
- For plannable outpatient services (lab work, imaging, screening), compare prices before booking. For these, the location can change the price several times over.
- If paying without insurance, ask for the cash price and about financial assistance before the service; listed cash prices can be many times what insurers pay.

**Employers that self-insure**
- Review where employees get routine labs and imaging; the same service can cost several times more at different Boston hospitals.
- When negotiating, pay attention to contracts paid as a percent of billed charges at hospitals with high sticker prices.

**Regulators and hospitals**
- Monitor whether files can be reached **automatically**, since the rule exists so that tools can read them; blocking automated downloads undercuts that.
- Check that official link lists stay current after website changes, and that files list all contracted insurers.

## 6. Limitations

- These are **prices paid to the hospital, not a patient's out-of-pocket cost**, which depends on deductibles, copays and plan design.
- Typical commercial prices are medians across listed plans, **not weighted** by how many patients use each plan.
- **Facility charges only**; physicians may bill separately. Some rates are bundled with other services, so a single billing code doesn't always capture the full cost of care (flagged rows were excluded).
- **Five hospitals and 18 procedures**: a starting sample, not all of Boston or Massachusetts.
- Findings are **associations**, not causes. BIDMC's file may be incomplete, which limits comparisons involving its insurers.
- Prices are as published in each hospital's file (updated March–April 2026), collected October 2026.

## 7. Next steps

1. Add about 15 more Greater Boston hospitals (most already discovered through their link lists).
2. Investigate why four procedures don't appear under standard codes at three hospitals.
3. Estimate out-of-pocket cost for common plan types (deductible and coinsurance) to make prices more meaningful for patients.
4. Share findings with a Massachusetts health-policy audience for feedback.
