select
    movie_id,
    person_id

from {{ ref('stg_tmdb_movie_directors') }}
qualify row_number() over (
    partition by movie_id, person_id
    order by extracted_at desc
) = 1
