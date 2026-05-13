-- tests/assert_stars_non_negative.sql
-- Custom dbt test: no repo should have negative stars

SELECT repo_id, repo_name, stars
FROM {{ ref('stg_repos') }}
WHERE stars < 0
