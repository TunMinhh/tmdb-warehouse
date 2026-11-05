select
    movie_id,
    business_date,
    page_number,
    overall_rank,
    extracted_at,
    raw_response_id

from {{ ref('stg_tmdb_popular_movies') }}
-- The list can shift while paging, so a movie may appear on two pages of the same day.
qualify row_number() over (
    partition by movie_id, business_date
    order by overall_rank
) = 1
