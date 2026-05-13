-- models/staging/stg_repos.sql
-- Cleans and standardizes raw GitHub data

with source as (
    select * from raw_repos
),

cleaned as (
    select
        id                                          as repo_id,
        name                                        as repo_name,
        nullif(trim(description), '')               as description,
        lower(language)                             as language,
        stars,
        forks,
        open_issues,
        watchers,
        nullif(license, 'NOASSERTION')              as license,
        created_at::date                            as repo_created_date,
        updated_at::date                            as last_updated_date,
        pushed_at::date                             as last_pushed_date,
        url,
        snapshot_date,
        -- Derived
        stars + forks                               as engagement_score,
        datediff('day', created_at, snapshot_date)  as repo_age_days
    from source
    where id is not null
      and stars >= 0
)

select * from cleaned
