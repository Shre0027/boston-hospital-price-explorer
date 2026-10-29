-- Question: Across all procedures, which hospitals tend to be cheaper or more expensive
--           for commercial insurance?
-- Why it matters: one procedure can be a fluke; a consistent pattern across many procedures is a real finding.
-- Method: a simple price index. For each procedure, divide each hospital's typical commercial price by the
-- median across hospitals for that procedure (1.0 = typical; 1.5 = 50% above typical). Each hospital's index
-- is the median of these ratios. Only procedures listed by at least 8 hospitals count, and only hospitals
-- with at least 8 such procedures are ranked, so every hospital is compared on mostly the same set.

WITH per_procedure AS (
    SELECT
        hospital,
        cpt,
        median_price / MEDIAN(median_price) OVER (PARTITION BY cpt) AS vs_typical,
        COUNT(*) OVER (PARTITION BY cpt)                             AS hospitals_listing
    FROM typical_commercial
)
SELECT
    hospital,
    COUNT(*)                                          AS procedures_compared,
    ROUND(MEDIAN(vs_typical), 2)                      AS price_index,
    ROUND(MIN(vs_typical), 2)                         AS lowest_ratio,
    ROUND(MAX(vs_typical), 2)                         AS highest_ratio,
    COUNT(*) FILTER (WHERE vs_typical < 1)            AS procedures_below_typical
FROM per_procedure
WHERE hospitals_listing >= 8
GROUP BY hospital
HAVING COUNT(*) >= 8
ORDER BY price_index, hospital;
