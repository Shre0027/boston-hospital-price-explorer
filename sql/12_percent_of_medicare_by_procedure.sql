-- 12. Commercial prices as a percent of Medicare, by procedure
-- Question: which services are priced furthest above Medicare?
-- Method: for each procedure, every hospital's typical commercial price / Medicare's rate; median, lowest
-- and highest across hospitals. Lab tests are paid under a different Medicare fee schedule (CLFS) than
-- imaging, visits and procedures (OPPS), which is shown in the medicare_system column.
WITH ratio AS (
    SELECT t.procedure, t.category, m.medicare_system, m.medicare_rate, t.hospital, t.median_price / m.medicare_rate AS times_medicare
    FROM typical_commercial t
    JOIN medicare m USING (cpt)
    WHERE m.medicare_rate IS NOT NULL
)
SELECT
    procedure,
    medicare_system,
    ROUND(ANY_VALUE(medicare_rate), 2)                 AS medicare_rate,
    COUNT(*)                                           AS hospitals,
    ROUND(100 * MEDIAN(times_medicare))                AS median_pct_of_medicare,
    ROUND(100 * MIN(times_medicare))                   AS lowest_pct,
    ROUND(100 * MAX(times_medicare))                   AS highest_pct
FROM ratio
GROUP BY procedure, medicare_system
ORDER BY median_pct_of_medicare DESC, procedure;
