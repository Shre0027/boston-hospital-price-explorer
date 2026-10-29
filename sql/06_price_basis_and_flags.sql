-- Question: How was each comparison price chosen, and how many rows were set aside, by hospital?
-- Why it matters: shows how much of each hospital's data is directly usable versus needing
-- caution, which is itself a measure of how "transparent" the published data really is.

SELECT
    hospital,
    COALESCE(NULLIF(price_basis, ''), '(no usable price)') AS price_basis,
    COALESCE(NULLIF(flag, ''), '(not flagged)')            AS flag,
    COUNT(*)                                               AS price_rows
FROM prices
GROUP BY ALL
ORDER BY hospital, price_rows DESC;
