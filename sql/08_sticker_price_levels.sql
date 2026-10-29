-- Question: How high is each hospital's own sticker price (gross charge), compared with what insurers pay it?
-- Why it matters: query 07 showed that "percent of billed charges" contracts are expensive at some hospitals
-- and cheap at others. If that's because the percentage is applied to very different sticker prices,
-- the sticker-price level and the insurer-price level should only partly line up.
-- Method: the same index as query 05, for sticker prices and insurer prices side by side
-- (1.0 = typical across hospitals; median over procedures listed by at least 8 hospitals).

WITH sticker AS (
    SELECT hospital, cpt, MEDIAN(gross_charge) AS gross
    FROM prices
    WHERE gross_charge IS NOT NULL AND (modifiers IS NULL OR modifiers = '')
    GROUP BY ALL
),
sticker_rel AS (
    SELECT hospital, cpt,
           gross / MEDIAN(gross) OVER (PARTITION BY cpt) AS sticker_vs_typical,
           COUNT(*) OVER (PARTITION BY cpt)              AS hospitals_listing
    FROM sticker
),
paid_rel AS (
    SELECT hospital, cpt,
           median_price / MEDIAN(median_price) OVER (PARTITION BY cpt) AS paid_vs_typical,
           COUNT(*) OVER (PARTITION BY cpt)                             AS hospitals_listing
    FROM typical_commercial
)
SELECT
    s.hospital,
    COUNT(*)                                  AS procedures_compared,
    ROUND(MEDIAN(s.sticker_vs_typical), 2)    AS sticker_price_index,
    ROUND(MEDIAN(p.paid_vs_typical), 2)       AS insurer_price_index
FROM sticker_rel s
JOIN paid_rel p ON s.hospital = p.hospital AND s.cpt = p.cpt
WHERE s.hospitals_listing >= 8 AND p.hospitals_listing >= 8
GROUP BY s.hospital
HAVING COUNT(*) >= 8
ORDER BY sticker_price_index, s.hospital;
