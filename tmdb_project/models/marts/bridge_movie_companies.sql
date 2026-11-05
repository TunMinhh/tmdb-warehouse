select
    movie_id,
    company_id

from {{ ref('stg_tmdb_movie_companies') }}
qualify row_number() over (
    partition by movie_id, company_id
    order by extracted_at desc
) = 1
