-- Question: How much more does a patient without insurance pay (cash price) than what
--           commercial insurers typically pay, at the same hospital for the same procedure?
-- Why it matters: shows whether uninsured patients are charged more than insured ones.

SELECT
    c.hospital,
    c.procedure,
    ROUND(c.cash_price)                       AS cash_price,
    ROUND(t.median_price)                     AS typical_insurer_price,
    ROUND(c.cash_price / t.median_price, 1)   AS cash_times_insurer
FROM typical_cash c
JOIN typical_commercial t
  ON c.hospital_id = t.hospital_id
 AND c.cpt = t.cpt
WHERE t.median_price > 0
ORDER BY cash_times_insurer DESC, c.hospital, c.procedure
LIMIT 15;
