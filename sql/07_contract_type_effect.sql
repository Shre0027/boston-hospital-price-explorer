-- Question: Within the same hospital, are "percent of billed charges" contracts more expensive
--           than fixed "fee schedule" contracts?
-- Why it matters: under a percent-of-charges contract, the insurer pays a share of the hospital's own
-- sticker price, so a high sticker price flows straight into what is paid. If those contracts cost more
-- even inside the same hospital, contract design (not just the hospital) drives cost.
-- Method: compare within each hospital so that hospital differences don't get mixed in (MGH and Brigham
-- use percent-of-charges almost exclusively, so they can't show a within-hospital contrast).
-- For each hospital and procedure that has BOTH contract types, take the median price under each type,
-- then summarize the ratio (percent-of-charges / fee schedule) across procedures.

WITH by_type AS (
    SELECT
        hospital,
        procedure,
        MEDIAN(comparison_price) FILTER (WHERE LOWER(methodology) = 'percent of total billed charges') AS pct_of_charges,
        MEDIAN(comparison_price) FILTER (WHERE LOWER(methodology) = 'fee schedule')                    AS fee_schedule
    FROM comparable
    GROUP BY ALL
)
SELECT
    hospital,
    COUNT(*)                                      AS procedures_with_both,
    ROUND(MEDIAN(pct_of_charges / fee_schedule), 2) AS median_ratio_pct_vs_fee,
    ROUND(MIN(pct_of_charges / fee_schedule), 2)    AS lowest_ratio,
    ROUND(MAX(pct_of_charges / fee_schedule), 2)    AS highest_ratio,
    COUNT(*) FILTER (WHERE pct_of_charges > fee_schedule) AS procedures_where_pct_costs_more
FROM by_type
WHERE pct_of_charges IS NOT NULL AND fee_schedule IS NOT NULL
GROUP BY hospital
ORDER BY hospital;
