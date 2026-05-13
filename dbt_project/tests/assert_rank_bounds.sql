-- tests/assert_rank_bounds.sql
-- Each language+snapshot combo should have ranks 1-20 only

SELECT *
FROM {{ ref('mart_top_repos') }}
WHERE rank_in_language < 1 OR rank_in_language > 20
