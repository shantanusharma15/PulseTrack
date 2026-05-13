-- models/marts/mart_language_trends.sql
-- Language-level trend mart used for dashboard charts

with daily as (
    select * from {{ ref('int_language_daily') }}
),

with_growth as (
    select
        *,
        lag(total_stars) over (
            partition by language
            order by snapshot_date
        ) as prev_total_stars,

        lag(repo_count) over (
            partition by language
            order by snapshot_date
        ) as prev_repo_count
    from daily
)

select
    snapshot_date,
    language,
    repo_count,
    total_stars,
    avg_stars,
    max_stars,
    total_forks,
    avg_engagement,
    avg_repo_age_days,
    -- Growth metrics (null on first snapshot)
    total_stars - prev_total_stars              as stars_delta,
    repo_count  - prev_repo_count               as repo_count_delta,
    round(
        100.0 * (total_stars - prev_total_stars)
        / nullif(prev_total_stars, 0), 2
    )                                           as stars_growth_pct
from with_growth
order by snapshot_date desc, total_stars desc
