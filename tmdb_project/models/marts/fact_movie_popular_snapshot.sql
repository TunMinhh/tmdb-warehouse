select
    movie_id,
    business_date,
    page_number,
    overall_rank,
    extracted_at,
    raw_response_id

from {{ ref('stg_tmdb_popular_movies') }}