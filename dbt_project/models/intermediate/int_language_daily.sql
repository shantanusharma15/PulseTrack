-- models/intermediate/int_language_daily.sql
-- Aggregates repo metrics by language and snapshot date

with stg as (
    select * from {{ ref('stg_repos') }}
)

select
    snapshot_date,
    language,
    count(*)                        as repo_count,
    sum(stars)                      as total_stars,
    avg(stars)                      as avg_stars,
    max(stars)                      as max_stars,
    sum(forks)                      as total_forks,
    avg(forks)                      as avg_forks,
    sum(open_issues)                as total_open_issues,
    avg(engagement_score)           as avg_engagement,
    avg(repo_age_days)              as avg_repo_age_days
from stg
group by 1, 2
