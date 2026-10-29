-- Question: Summarized by star rating, how do prices compare, and how strong is the link?
-- Why it matters: turns query 09's list into one comparison, plus a rank correlation as a rough measure of
-- how consistently price rises with rating (1 = always rises, 0 = no link, -1 = always falls).
-- With fewer than 20 hospitals this is descriptive only, not proof of any cause.
-- Method: Spearman rank correlation = the ordinary (Pearson) correlation of the ranks, where tied values
-- share their average rank (many hospitals share the same star rating).

WITH per_procedure AS (
    SELECT hospital_id, cpt,
           median_price / MEDIAN(median_price) OVER (PARTITION BY cpt) AS vs_typical,
           COUNT(*) OVER (PARTITION BY cpt)                             AS hospitals_listing
    FROM typical_commercial
),
idx AS (
    SELECT hospital_id, MEDIAN(vs_typical) AS price_index
    FROM per_procedure
    WHERE hospitals_listing >= 8
    GROUP BY hospital_id
    HAVING COUNT(*) >= 8
),
rated AS (
    SELECT i.hospital_id, i.price_index, q.cms_stars
    FROM idx i
    JOIN quality q USING (hospital_id)
    WHERE q.cms_stars IS NOT NULL
),
ranked AS (
    SELECT *,
           RANK() OVER (ORDER BY price_index) + (COUNT(*) OVER (PARTITION BY price_index) - 1) / 2.0 AS price_rank,
           RANK() OVER (ORDER BY cms_stars)   + (COUNT(*) OVER (PARTITION BY cms_stars) - 1) / 2.0   AS stars_rank
    FROM rated
)
SELECT
    CAST(cms_stars AS VARCHAR) || ' stars'  AS group_name,
    COUNT(*)                               AS hospitals,
    ROUND(MIN(price_index), 2)             AS lowest_price_index,
    ROUND(MEDIAN(price_index), 2)          AS median_price_index,
    ROUND(MAX(price_index), 2)             AS highest_price_index,
    NULL::DOUBLE                           AS rank_correlation
FROM ranked
GROUP BY cms_stars
UNION ALL
SELECT
    'All rated hospitals',
    COUNT(*),
    ROUND(MIN(price_index), 2),
    ROUND(MEDIAN(price_index), 2),
    ROUND(MAX(price_index), 2),
    ROUND(CORR(price_rank, stars_rank), 2)
FROM ranked
ORDER BY group_name;
