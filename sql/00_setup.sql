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

-- One typical (median) commercial price per hospital and procedure
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
GROUP BY ALL;

-- One cash (self-pay) price per hospital and procedure
CREATE OR REPLACE VIEW typical_cash AS
SELECT hospital_id, hospital, cpt, procedure, MEDIAN(cash_price) AS cash_price
FROM prices
WHERE cash_price IS NOT NULL
  AND (modifiers IS NULL OR modifiers = '')
GROUP BY ALL;
