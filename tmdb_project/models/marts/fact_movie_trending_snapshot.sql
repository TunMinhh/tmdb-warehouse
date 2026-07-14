select
    movie_id,
    business_date,
    time_window,
    trending_rank,
    extracted_at,
    raw_response_id

from {{ ref('stg_tmdb_trending_movies') }}