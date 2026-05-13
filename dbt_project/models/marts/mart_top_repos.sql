-- models/marts/mart_top_repos.sql
-- Final mart: top 20 repos per language per snapshot date

with ranked as (
    select
        *,
        row_number() over (
            partition by snapshot_date, language
            order by stars desc
        ) as rank_in_language
    from {{ ref('stg_repos') }}
)

select
    snapshot_date,
    language,
    rank_in_language,
    repo_id,
    repo_name,
    description,
    stars,
    forks,
    open_issues,
    engagement_score,
    repo_age_days,
    license,
    url
from ranked
where rank_in_language <= 20
order by snapshot_date desc, language, rank_in_language
