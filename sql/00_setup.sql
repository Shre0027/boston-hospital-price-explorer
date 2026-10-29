-- Setup: shared views used by every analysis query.
-- Run automatically before each query by scripts/run_sql.py.

-- Every published price row from all hospitals (one row per hospital x procedure x setting x insurer plan)
CREATE OR REPLACE VIEW prices AS
SELECT *
FROM read_csv('data/combined/prices_clean.csv', header = true, auto_detect = true);

-- Rows that can be compared fairly across hospitals:
--   commercial insurance only, a usable comparison price, not flagged, and no billing modifier
--   (see docs/decision-log.md for why flagged and modified rows are excluded)
CREATE OR REPLACE VIEW comparable AS
SELECT *
FROM prices
WHERE market = 'Commercial'
  AND comparison_price IS NOT NULL
  AND (flag IS NULL OR flag = '')
  AND (modifiers IS NULL OR modifiers = '');

-- One typical (median) commercial price per hospital and procedure.
-- Requires at least 3 plan prices, so a "typical" price never rests on just one or two plans.
CREATE OR REPLACE VIEW typical_commercial AS
SELECT
    hospital_id,
    hospital,
    cpt,
    procedure,
    category,
    MEDIAN(comparison_price) AS median_price,
    MIN(comparison_price)    AS min_price,
    MAX(comparison_price)    AS max_price,
    COUNT(*)                 AS plans
FROM comparable
GROUP BY ALL
HAVING COUNT(*) >= 3;

-- One cash (self-pay) price per hospital and procedure
CREATE OR REPLACE VIEW typical_cash AS
SELECT hospital_id, hospital, cpt, procedure, MEDIAN(cash_price) AS cash_price
FROM prices
WHERE cash_price IS NOT NULL
  AND (modifiers IS NULL OR modifiers = '')
GROUP BY ALL;

-- Hospital list from the project config (id, name, health system, CMS Certification Number)
CREATE OR REPLACE VIEW hospitals AS
SELECT id AS hospital_id, name AS hospital, short, system, ccn
FROM read_json('config/hospitals.json', format = 'array', columns = {
    id: 'VARCHAR', name: 'VARCHAR', short: 'VARCHAR', system: 'VARCHAR', ccn: 'VARCHAR'});

-- CMS overall star rating (1-5) per hospital, joined by CMS Certification Number.
-- Stars are NULL when CMS shows "Not Available" (e.g. too few measures reported).
CREATE OR REPLACE VIEW quality AS
SELECT
    h.hospital_id,
    h.hospital,
    TRY_CAST(q."Hospital overall rating" AS INTEGER) AS cms_stars,
    q."Hospital overall rating footnote"            AS stars_footnote
FROM hospitals h
LEFT JOIN read_csv('data/quality/ma_hospital_general_information.csv', header = true, all_varchar = true) q
  ON q."Facility ID" = h.ccn;

-- Medicare benchmark: what traditional Medicare pays these hospitals for each procedure (2026),
-- from CMS OPPS Addendum B (outpatient, wage-adjusted for the Boston area) and the Clinical Lab
-- Fee Schedule. Built by scripts/medicare_rates.py; procedures Medicare doesn't pay separately are NULL.
CREATE OR REPLACE VIEW medicare AS
SELECT cpt, medicare_system, status_indicator, TRY_CAST(medicare_rate AS DOUBLE) AS medicare_rate, why_not
FROM read_csv('data/medicare/rates.csv', header = true, all_varchar = true);
