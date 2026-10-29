# Boston Hospital Price Explorer

**What will this actually cost me?**

Since 2021, US hospitals have been legally required to publish their prices. But they publish them in huge, messy files that patients can't realistically use. The same MRI can cost very different amounts depending on the hospital and the insurer, and patients usually find out only when the bill arrives.

This project turns those public files into something a normal person can use.

## What it does
1. **Collects** official price files from 5 Boston hospitals
2. **Cleans** them and keeps about 18 common procedures, matched by billing code (CPT)
3. **Compares** prices across hospitals and insurers in a dashboard
4. **Answers plain-English questions** with AI, such as "How much is a knee MRI with Blue Cross?"
5. **Checks data quality**: can patients actually use what each hospital published?

## Hospitals (Phase 1)
Massachusetts General Hospital · Brigham and Women's · Boston Medical Center · Beth Israel Deaconess Medical Center · Tufts Medical Center

## Status
🚧 In progress: 4 of 5 hospitals extracted (MGH, Brigham, BMC, BIDMC); Tufts Medical Center blocks automated access

## Data source
Hospital machine-readable files published under the CMS Hospital Price Transparency rule (45 CFR Part 180).

*Prices shown are published standard charges, not personal cost estimates.*
