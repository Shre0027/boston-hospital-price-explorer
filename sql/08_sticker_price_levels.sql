-- Question: How high is each hospital's own sticker price (gross charge), relative to the other hospitals?
-- Why it matters: query 07 showed that "percent of billed charges" contracts are expensive at some hospitals
-- and cheap at others. If that's because the percentage is applied to very different sticker prices,
-- hospitals with high sticker prices should be the ones where insurers pay the most.
-- Method: one sticker price per hospital and procedure (median across rows), expressed relative to the
-- lowest sticker price for that procedure; summarized by hospital over procedures listed by at least 4 hospitals.
-- The last column repeats each hospital's typical commercial price level (from query 05) for side-by-side reading.

WITH sticker AS (
    SELECT hospital, cpt, MEDIAN(gross_charge) AS gross
    FROM prices
    WHERE gross_charge IS NOT NULL AND (modifiers IS NULL OR modifiers = '')
    GROUP BY ALL
),
sticker_rel AS (
    SELECT hospital, cpt,
           gross / MIN(gross) OVER (PARTITION BY cpt) AS sticker_vs_lowest,
           COUNT(*) OVER (PARTITION BY cpt)           AS hospitals_listing
    FROM sticker
),
paid_rel AS (
    SELECT hospital, cpt,
           median_price / MIN(median_price) OVER (PARTITION BY cpt) AS paid_vs_lowest,
           COUNT(*) OVER (PARTITION BY cpt)                          AS hospitals_listing
    FROM typical_commercial
)
SELECT
    s.hospital,
    COUNT(*)                                    AS procedures_compared,
    ROUND(MEDIAN(s.sticker_vs_lowest), 2)       AS median_sticker_vs_lowest,
    ROUND(MEDIAN(p.paid_vs_lowest), 2)          AS median_insurer_paid_vs_lowest
FROM sticker_rel s
JOIN paid_rel p ON s.hospital = p.hospital AND s.cpt = p.cpt
WHERE s.hospitals_listing >= 4 AND p.hospitals_listing >= 4
GROUP BY s.hospital
ORDER BY median_sticker_vs_lowest;
