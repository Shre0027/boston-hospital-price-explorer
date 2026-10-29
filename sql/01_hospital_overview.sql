-- Question: What did each hospital actually publish, and how much of it is usable for comparison?
-- Why it matters: before comparing prices, check that each hospital's data is complete enough to compare.

SELECT
    hospital,
    COUNT(*)                                                         AS price_rows,
    COUNT(DISTINCT cpt)                                              AS procedures_listed,
    COUNT(DISTINCT payer_raw) FILTER (WHERE payer_raw IS NOT NULL)   AS insurer_plans_listed,
    COUNT(*) FILTER (WHERE market = 'Commercial')                    AS commercial_rows,
    COUNT(*) FILTER (WHERE flag IS NOT NULL AND flag <> '')          AS flagged_rows,
    ROUND(100.0 * COUNT(*) FILTER (WHERE flag IS NOT NULL AND flag <> '') / COUNT(*), 1) AS pct_flagged
FROM prices
GROUP BY hospital
ORDER BY price_rows DESC;
