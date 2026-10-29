-- Question: Does the same insurer pay very different amounts for the same procedure
--           depending on the hospital?
-- Why it matters: if one insurer pays one hospital several times more than another for
-- the same service, that cost flows into everyone's premiums.

WITH per_hospital AS (
    SELECT insurer, procedure, hospital, MEDIAN(comparison_price) AS price
    FROM comparable
    WHERE insurer IN ('Blue Cross Blue Shield', 'Harvard Pilgrim', 'Tufts Health Plan',
                      'Aetna', 'UnitedHealthcare', 'Cigna')
    GROUP BY ALL
),
spread AS (
    SELECT
        insurer,
        procedure,
        COUNT(*)                     AS hospitals,
        MIN(price)                   AS lowest,
        MAX(price)                   AS highest,
        -- Several hospitals can tie (MGH and Brigham share one price list), so list every hospital at the low/high price
        STRING_AGG(hospital, ' / ' ORDER BY hospital) FILTER (WHERE price = lowest_price_in_group)  AS lowest_hospital,
        STRING_AGG(hospital, ' / ' ORDER BY hospital) FILTER (WHERE price = highest_price_in_group) AS highest_hospital
    FROM (
        SELECT *,
               MIN(price) OVER (PARTITION BY insurer, procedure) AS lowest_price_in_group,
               MAX(price) OVER (PARTITION BY insurer, procedure) AS highest_price_in_group
        FROM per_hospital
    )
    GROUP BY insurer, procedure
    HAVING COUNT(*) >= 3
)
SELECT
    insurer,
    procedure,
    hospitals,
    lowest_hospital,
    ROUND(lowest)                     AS lowest_price,
    highest_hospital,
    ROUND(highest)                    AS highest_price,
    ROUND(highest / lowest, 1)        AS times_more
FROM spread
ORDER BY times_more DESC, insurer, procedure
LIMIT 15;
