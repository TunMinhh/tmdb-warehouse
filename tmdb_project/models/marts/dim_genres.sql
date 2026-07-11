select
    genre_id,
    genre_name

from {{ ref('stg_tmdb_genres') }}
qualify row_number() over (
    partition by genre_id
    order by extracted_at desc
) = 1