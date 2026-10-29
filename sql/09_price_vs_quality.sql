-- Question: Do more expensive hospitals have higher CMS quality ratings?
-- Why it matters: a common defense of high prices is higher quality. If high-rated hospitals are also
-- available at lower prices, patients and employers can pay less without choosing lower-rated care.
-- Method: each hospital's commercial price index (as in query 05) next to its CMS overall star rating
-- (1-5, from CMS Hospital General Information). The star rating summarizes measures such as mortality,
-- safety, readmissions and patient experience; it is not a measure of every service compared here.

WITH per_procedure AS (
    SELECT hospital_id, hospital, cpt,
           median_price / MEDIAN(median_price) OVER (PARTITION BY cpt) AS vs_typical,
           COUNT(*) OVER (PARTITION BY cpt)                             AS hospitals_listing
    FROM typical_commercial
),
idx AS (
    SELECT hospital_id, hospital, COUNT(*) AS procedures_compared, MEDIAN(vs_typical) AS price_index
    FROM per_procedure
    WHERE hospitals_listing >= 8
    GROUP BY ALL
    HAVING COUNT(*) >= 8
)
SELECT
    i.hospital,
    COALESCE(CAST(q.cms_stars AS VARCHAR), 'Not rated') AS cms_stars,
    ROUND(i.price_index, 2)                            AS price_index,
    i.procedures_compared
FROM idx i
LEFT JOIN quality q USING (hospital_id)
ORDER BY q.cms_stars DESC NULLS LAST, i.price_index, i.hospital;
