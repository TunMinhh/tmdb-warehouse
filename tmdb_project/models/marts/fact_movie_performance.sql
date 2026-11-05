with movies as (

    select *
    from {{ ref('stg_tmdb_movies') }}
    qualify row_number() over (
        partition by movie_id
        order by extracted_at desc
    ) = 1

),

-- Where each movie ranked by current popularity within its release year.
discover_ranks as (

    select
        movie_id,
        discover_year,
        overall_rank as popularity_rank
    from {{ ref('stg_tmdb_discover_movies') }}
    where sort_by = 'popularity.desc'
    qualify row_number() over (
        partition by movie_id, discover_year
        order by business_date desc, overall_rank
    ) = 1

),

-- TMDB uses 0 or tiny values for unknown financials, so treat them as missing.
cleaned as (

    select
        movies.movie_id,
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

        movies.extracted_at,
        discover_ranks.popularity_rank

    from movies
    left join discover_ranks
        on movies.movie_id = discover_ranks.movie_id
        and movies.release_year = discover_ranks.discover_year

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

    popularity_rank,

    case
        when popularity_rank <= {{ var('analysis_max_rank') }} / 2 then 'Top 50'
        when popularity_rank <= {{ var('analysis_max_rank') }} then '51-100'
        else 'Outside sample'
    end as popularity_band,

    case
        when popularity_rank <= {{ var('analysis_max_rank') }} / 2 then 1
        when popularity_rank <= {{ var('analysis_max_rank') }} then 2
        else 3
    end as popularity_band_order,

    case
        when vote_count < 100 then null
        when vote_average < 6 then 'Below 6'
        when vote_average < 7 then '6 to 6.9'
        else '7 and above'
    end as rating_band,

    case
        when vote_count < 100 then null
        when vote_average < 6 then 1
        when vote_average < 7 then 2
        else 3
    end as rating_band_order,

    case
        when vote_count >= 100 then true
        else false
    end as has_enough_votes,

    has_reliable_financials,

    coalesce(
        status = 'Released'
        and release_year between {{ var('analysis_start_year') }} and {{ var('analysis_end_year') }}
        and has_reliable_financials
        and popularity_rank <= {{ var('analysis_max_rank') }},
        false
    ) as is_analysis_ready,

    extracted_at

from metrics
