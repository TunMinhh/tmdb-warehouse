select
    person_id,
    director_name

from {{ ref('stg_tmdb_movie_directors') }}
qualify row_number() over (
    partition by person_id
    order by extracted_at desc, director_name
) = 1
