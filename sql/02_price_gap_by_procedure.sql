-- Question: For each procedure, how far apart are the cheapest and most expensive hospitals
--           for patients with commercial insurance?
-- Why it matters: a large gap means choosing a hospital can save a lot of money for the same service.

WITH ranked AS (
    SELECT
        procedure,
        hospital,
        median_price,
        ROW_NUMBER() OVER (PARTITION BY cpt ORDER BY median_price ASC, hospital)  AS rank_low,   -- ties broken by name so results repeat
        ROW_NUMBER() OVER (PARTITION BY cpt ORDER BY median_price DESC, hospital) AS rank_high,
        COUNT(*)     OVER (PARTITION BY cpt)                            AS hospitals_listing
    FROM typical_commercial
)
SELECT
    lo.procedure,
    lo.hospitals_listing,
    lo.hospital                                  AS lowest_hospital,
    ROUND(lo.median_price)                       AS lowest_price,
    hi.hospital                                  AS highest_hospital,
    ROUND(hi.median_price)                       AS highest_price,
    ROUND(hi.median_price / lo.median_price, 1)  AS times_more
FROM ranked lo
JOIN ranked hi
  ON lo.procedure = hi.procedure
 AND lo.rank_low = 1
 AND hi.rank_high = 1
WHERE lo.hospitals_listing >= 3          -- only compare when at least 3 hospitals list a price
ORDER BY times_more DESC, procedure;
