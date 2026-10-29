"""
Combine each hospital's extracted prices into one clean, comparable table.

Each hospital names insurers differently and formats numbers differently, so this script:
  1. Groups insurer names into the brands a patient would recognize
     ("BCBS [6001]" and "BLUE CROSS BLUE SHIELD [110001]" -> "Blue Cross Blue Shield")
  2. Tags each insurer row with a market: Commercial, Medicare, MassHealth (Medicaid), or Military
  3. Turns money text ("4613.000", "$2,499.00") into numbers
  4. Picks one comparison price per row:
       - the negotiated dollar amount when the hospital gives one
       - otherwise the median amount actually paid (CMS added this field in 2026)
     and records which one was used in "price_basis"

Output: data/combined/prices_clean.csv

Usage:
  python scripts/combine.py
"""

import csv
import statistics
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "data" / "combined"

# Checked in order; the first match wins. Matched against the payer name; the plan name is only
# used when the payer name is generic (see GENERIC_PAYERS), because some hospitals use the plan
# column for pricing labels rather than the patient's actual plan.
INSURER_GROUPS = [
    ("Blue Cross Blue Shield", r"\bBCBS\b|BLUE CROSS|BLUE SHIELD|\bMEDEX\b"),
    ("Harvard Pilgrim", r"HARVARD PILGRIM|\bHPHC\b"),
    ("Tufts Health Plan", r"\bTUFTS\b"),
    ("Aetna", r"\bAETNA\b"),
    ("UnitedHealthcare", r"UNITED ?HEALTH|^UNITED\b|\bUNITED (PPO|HMO)|\bUHC\b|\bOPTUM\b|\bOXFORD\b|\bUMR\b|\bAARP\b"),
    ("Cigna", r"\bCIGNA\b"),
    ("Mass General Brigham Health Plan", r"\bMGB\b|MASS GEN(ERAL)? BRIGHAM"),
    ("Wellpoint / Unicare", r"WELLPOINT|UNICARE"),
    ("Fallon Health", r"\bFALLON\b"),
    ("Health New England", r"HEALTH NEW ENGLAND|HLTH NEW ENGLAND"),
    ("Humana", r"\bHUMANA\b"),
    ("Medicare (original)", r"^MEDICARE( \[\d+\])?$"),
    ("MassHealth", r"MASS ?HEALTH|^MEDICAID"),
]

# Payer names that don't say which insurer it is; for these, look at the plan name too
GENERIC_PAYERS = r"CENTERS OF EXCELLENCE|INTERNATIONAL COMMERCIAL"

# Market, decided from the payer name. Checked in order; the first match wins.
MARKETS = [
    # Not medical insurance for these procedures: dental and vision plans, and behavioral-health plans
    ("Dental / vision plan", r"DENTAL|EYEMED|VISION|SPECTERA"),
    ("Behavioral health plan", r"BEHAVIOR|BEACON|CARELON|MAGELLAN|\bBH\b|MBHP|COMPSYCH|CBHC"),
    ("Other public / workers comp", r"^WC\b|WORK COMP|CORRECTIONS|HRSA|\bMVA\b|\bDPH\b|OTHER GOV'?T"),
    # Payer names that could be commercial or Medicaid; left out rather than guessed
    ("Unclear (excluded)", r"^NEIGHBORHOOD HEALTH PLAN|RI NEIGHBORHOOD|CELTICARE|COVERAGE DISCOVERY|MODERN ASSISTANCE"),
    ("Medicare", r"MEDICARE REPLACEMENT|MEDICARE MANAGED"),
    ("MassHealth / safety net", r"MEDICAID REPLACEMENT"),
    ("Commercial", r"COMMERCIAL|CONNECTORCARE"),
    ("Military", r"TRICARE|CHAMPVA|MARTIN'?S POINT|VETERANS"),
    ("MassHealth / safety net", r"MEDICAID|MASS ?HEALTH|\bACO\b|\bMCO\b|\bMCD\b|\bHSN\b|SAFETY NET|WELLSENSE|\bCCA\b|COMMONWEALTH CARE|MOLINA|PUBLIC PLAN|COMMUNITY PLAN"),
    ("Medicare", r"MEDICARE|\bAARP\b|SENIOR|\bPACE\b|\bSCO\b|ELDER SERVICE|ADVANTAGE|WELLCARE|ETERNALHEALTH|UPHAMS CORNER|EVERCARE|SCAN HEALTH|\bMEDEX\b|DUAL ELIGIBLE"),
]

# Clear signals in the plan name that override a "Commercial" default
PLAN_MARKET_SIGNALS = [
    ("Military", r"\bTRICARE\b"),
    ("Medicare", r"MEDICARE REPLACEM|MEDICARE ADVANTAGE|^HB (MGH|BWH) MEDICARE$"),
    ("MassHealth / safety net", r"MEDICAID"),
]


def money(text):
    """'4613.000' -> 4613.0, '$2,499.00' -> 2499.0, '' or 'N/A' -> None"""
    if text is None:
        return None
    cleaned = re.sub(r"[$,\s]", "", str(text))
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return value if value >= 0 else None


def classify(payer, plan):
    """Return (insurer group, market) for one payer/plan pair."""
    payer_upper = payer.upper().strip()
    # Some hospitals mark retired insurer contracts with a "ZZZ" prefix (e.g. "ZZZUNITED [1008]")
    if payer_upper.startswith("ZZZ"):
        return "Inactive (retired contract)", "Inactive"
    # Drop pricing notes in brackets, e.g. "FALLON COMMERCIAL (130% OF MEDICARE)": they describe
    # how the price is calculated, not who the customer is
    plan_upper = re.sub(r"\(.*?(\)|$)", "", plan.upper()).strip()

    insurer_text = payer_upper
    if re.search(GENERIC_PAYERS, payer_upper):
        insurer_text = f"{payer_upper} {plan_upper}"
    group = "Other"
    for name, pattern in INSURER_GROUPS:
        if re.search(pattern, insurer_text):
            group = name
            break

    # Dental, vision and behavioral-health plans are never medical comparisons, whatever the insurer
    for name, pattern in MARKETS[:2]:
        if re.search(pattern, payer_upper):
            return group, name
    if group == "Medicare (original)":
        return group, "Medicare"
    if group == "MassHealth":
        return group, "MassHealth / safety net"
    for name, pattern in MARKETS:
        if re.search(pattern, payer_upper):
            return group, name
    for name, pattern in PLAN_MARKET_SIGNALS:
        if re.search(pattern, plan_upper):
            return group, name
    return group, "Commercial"


def main():
    procedures = {p["cpt"]: p for p in json.load(open(ROOT / "config" / "procedures.json", encoding="utf-8"))}
    hospitals = {h["id"]: h for h in json.load(open(ROOT / "config" / "hospitals.json", encoding="utf-8"))}

    columns = [
        "hospital_id", "hospital", "cpt", "procedure", "category", "hospital_description", "setting", "modifiers",
        "payer_raw", "plan_raw", "insurer", "market",
        "gross_charge", "cash_price", "negotiated_dollar", "negotiated_percent", "negotiated_formula",
        "median_paid", "p10_paid", "p90_paid", "min_negotiated", "max_negotiated", "methodology",
        "comparison_price", "price_basis", "flag",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "prices_clean.csv"
    counts = {}

    with open(out_path, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=columns)
        writer.writeheader()
        all_rows = []
        for path in sorted(IN_DIR.glob("*_prices.csv")):
            hid = path.name.removesuffix("_prices.csv")
            if hid not in hospitals:
                continue
            n = 0
            with open(path, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    cpt = r["matched_cpt"]
                    proc = procedures.get(cpt, {})
                    payer = (r.get("payer_name") or "").strip()
                    plan = (r.get("plan_name") or "").strip()
                    insurer, market = classify(payer, plan) if payer else ("", "")
                    negotiated = money(r.get("standard_charge|negotiated_dollar"))
                    median = money(r.get("median_amount"))
                    formula = (r.get("standard_charge|negotiated_algorithm") or "").strip()
                    # When a rate comes from a formula (e.g. a "case rate" where procedures on the claim
                    # are sorted and priced together), the listed dollar amount can be just one piece of
                    # the payment. If the hospital reports the median amount actually paid, that's the
                    # more honest comparison.
                    if formula and median is not None:
                        comparison, basis = median, "median amount paid (rate set by formula)"
                    elif negotiated is not None:
                        comparison, basis = negotiated, "negotiated dollar amount"
                    elif median is not None:
                        comparison, basis = median, "median amount paid"
                    else:
                        comparison, basis = None, ""
                    gross = money(r.get("standard_charge|gross"))
                    # Insurer rates are often bundled (e.g. a surgery rate that includes supplies and
                    # anesthesia) while the sticker price covers one line item, so a rate above the
                    # sticker price is usually not an error. Flag it so it isn't compared naively.
                    flag = ""
                    if comparison is not None and gross and comparison > gross * 1.01:
                        flag = "insurer rate above sticker price (likely a bundled rate)"
                    elif formula and median is None and negotiated is not None:
                        flag = "rate set by formula and no amount-paid figure given; listed amount may be only part of the payment"
                    all_rows.append({
                        "hospital_id": hid,
                        "hospital": hospitals[hid]["name"],
                        "cpt": cpt,
                        "procedure": proc.get("name", ""),
                        "category": proc.get("category", ""),
                        "hospital_description": (r.get("description") or "").strip(),
                        "setting": (r.get("setting") or "").strip().lower(),
                        "modifiers": (r.get("modifiers") or "").strip(),
                        "payer_raw": payer,
                        "plan_raw": plan,
                        "insurer": insurer,
                        "market": market,
                        "gross_charge": gross,
                        "cash_price": money(r.get("standard_charge|discounted_cash")),
                        "negotiated_dollar": negotiated,
                        "negotiated_percent": money(r.get("standard_charge|negotiated_percentage")),
                        "negotiated_formula": (r.get("standard_charge|negotiated_algorithm") or "").strip()[:300],
                        "median_paid": median,
                        "p10_paid": money(r.get("10th_percentile")),
                        "p90_paid": money(r.get("90th_percentile")),
                        "min_negotiated": money(r.get("standard_charge|min")),
                        "max_negotiated": money(r.get("standard_charge|max")),
                        "methodology": (r.get("standard_charge|methodology") or "").strip(),
                        "comparison_price": comparison,
                        "price_basis": basis,
                        "flag": flag,
                    })
                    n += 1
            counts[hid] = n

        # Second pass: flag prices that are implausibly low for the procedure. Some files contain
        # rates like $0.03 for a blood count or $5 for a colonoscopy, which can't be real payments
        # (likely units or factors entered in the dollar column). The threshold is 10% of the
        # median commercial price for that procedure across all hospitals.
        typical = {}
        by_cpt = {}
        for r in all_rows:
            if r["market"] == "Commercial" and r["comparison_price"] is not None and not r["flag"] and not r["modifiers"]:
                by_cpt.setdefault(r["cpt"], []).append(r["comparison_price"])
        for cpt, values in by_cpt.items():
            typical[cpt] = statistics.median(values)
        low_flags = 0
        for r in all_rows:
            t = typical.get(r["cpt"])
            if t and r["comparison_price"] is not None and r["comparison_price"] < 0.10 * t and not r["flag"]:
                r["flag"] = "implausibly low (under 10% of the typical price for this procedure; likely a data error)"
                low_flags += 1
        writer.writerows(all_rows)

    total = sum(counts.values())
    print(f"Flagged {low_flags} implausibly low prices")
    print(f"Wrote {total:,} rows to {out_path.relative_to(ROOT)}: " + ", ".join(f"{k} {v:,}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
