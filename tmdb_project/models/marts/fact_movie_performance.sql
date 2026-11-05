with movies as (

    select *
    from {{ ref('stg_tmdb_movies') }}
    qualify row_number() over (
        partition by movie_id
        order by extracted_at desc
    ) = 1

),

-- TMDB uses 0 or tiny values for unknown financials, so treat them as missing.
cleaned as (

    select
        movie_id,
        release_date,
        release_year,
        month(release_date) as release_month,
        runtime,
        status,

        popularity,
        vote_average,
        vote_count,

        case when budget >= {{ var('min_reliable_amount') }} then budget end as budget,
        case when revenue >= {{ var('min_reliable_amount') }} then revenue end as revenue,

        extracted_at

    from movies

),

metrics as (

    select
        *,
        revenue - budget as profit,
        (revenue - budget) / budget::float as roi,
        revenue / budget::float as revenue_multiple,
        budget is not null and revenue is not null as has_reliable_financials
    from cleaned

)

select
    movie_id,
    release_date,
    release_year,
    release_month,
    runtime,

    popularity,
    vote_average,
    vote_count,

    budget,
    revenue,
    profit,
    roi,
    revenue_multiple,

    case
        when budget < 20000000 then 'Under $20M'
        when budget < 50000000 then '$20M-$50M'
        when budget < 100000000 then '$50M-$100M'
        when budget >= 100000000 then '$100M+'
    end as budget_tier,

    case
        when budget < 20000000 then 1
        when budget < 50000000 then 2
        when budget < 100000000 then 3
        when budget >= 100000000 then 4
    end as budget_tier_order,

    revenue_multiple >= {{ var('hit_revenue_multiple') }} as is_hit,

    case
        when vote_count >= 100 then true
        else false
    end as has_enough_votes,

    has_reliable_financials,

    coalesce(
        status = 'Released'
        and release_year between {{ var('analysis_start_year') }} and {{ var('analysis_end_year') }}
        and has_reliable_financials,
        false
    ) as is_analysis_ready,

    extracted_at

from metrics
