-- 11. Commercial prices as a percent of Medicare, by hospital
-- Question: compared with what Medicare pays for the same service, how much do commercial insurers pay each hospital?
-- This is the yardstick used by national hospital price studies (e.g. RAND), so the result can be compared with them.
-- Method: each hospital's typical commercial price for a procedure / Medicare's rate for it; then the median
-- across that hospital's procedures. Only procedures with a Medicare rate (15 of 18); hospitals need at least 8.
WITH ratio AS (
    SELECT t.hospital_id, t.hospital, t.procedure, t.median_price / m.medicare_rate AS times_medicare
    FROM typical_commercial t
    JOIN medicare m USING (cpt)
    WHERE m.medicare_rate IS NOT NULL
)
SELECT
    hospital,
    COUNT(*)                                           AS procedures_compared,
    ROUND(100 * MEDIAN(times_medicare))                AS pct_of_medicare,
    ROUND(100 * MIN(times_medicare))                   AS lowest_pct,
    ROUND(100 * MAX(times_medicare))                   AS highest_pct,
    COUNT(*) FILTER (WHERE times_medicare < 1)         AS procedures_below_medicare
FROM ratio
GROUP BY hospital
HAVING COUNT(*) >= 8
ORDER BY pct_of_medicare, hospital;
