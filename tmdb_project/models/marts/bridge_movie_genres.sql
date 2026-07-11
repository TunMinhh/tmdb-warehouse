select
    movie_id,
    genre_id

from {{ ref('stg_tmdb_movie_genres') }}
qualify row_number() over (
    partition by movie_id, genre_id
    order by extracted_at desc
) = 1