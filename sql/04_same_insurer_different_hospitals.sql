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
        ARG_MIN(hospital, price)     AS lowest_hospital,
        ARG_MAX(hospital, price)     AS highest_hospital
    FROM per_hospital
    GROUP BY ALL
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
ORDER BY times_more DESC
LIMIT 15;
