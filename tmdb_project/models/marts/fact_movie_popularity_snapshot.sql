with popular as (

    select
        movie_id,
        business_date,
        'popular' as source_list,
        null as time_window,
        page_number,
        overall_rank as ranking,
        extracted_at,
        raw_response_id
    from {{ ref('stg_tmdb_popular_movies') }}

),

trending as (

    select
        movie_id,
        business_date,
        'trending' as source_list,
        time_window,
        null as page_number,
        trending_rank as ranking,
        extracted_at,
        raw_response_id
    from {{ ref('stg_tmdb_trending_movies') }}

),

combined as (

    select * from popular
    union all
    select * from trending

)

select
    movie_id,
    business_date,
    source_list,
    time_window,
    page_number,
    ranking,
    extracted_at,
    raw_response_id

from combined