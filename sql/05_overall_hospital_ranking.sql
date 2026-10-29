-- Question: Across all procedures, which hospital tends to be cheapest or most expensive
--           for commercial insurance?
-- Why it matters: one procedure can be a fluke; a consistent pattern across many procedures is a real finding.
-- Method: for each procedure, express each hospital's price relative to the cheapest hospital
-- (1.0 = cheapest), then take the median (robust to a few extreme gaps) and the average across procedures. Only procedures listed by at least 4 hospitals count,
-- so every hospital is compared on mostly the same set.

WITH relative AS (
    SELECT
        hospital,
        procedure,
        median_price / MIN(median_price) OVER (PARTITION BY cpt) AS times_cheapest,
        RANK()        OVER (PARTITION BY cpt ORDER BY median_price) AS price_rank,
        COUNT(*)      OVER (PARTITION BY cpt)                       AS hospitals_listing
    FROM typical_commercial
)
SELECT
    hospital,
    COUNT(*)                          AS procedures_compared,
    ROUND(MEDIAN(times_cheapest), 2)  AS median_times_cheapest,
    ROUND(AVG(times_cheapest), 2)     AS avg_times_cheapest,
    ROUND(AVG(price_rank), 1)         AS avg_rank_1_is_cheapest,
    COUNT(*) FILTER (WHERE price_rank = 1) AS times_cheapest_hospital
FROM relative
WHERE hospitals_listing >= 4
GROUP BY hospital
ORDER BY median_times_cheapest;
