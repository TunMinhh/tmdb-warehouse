with movies as (

    select *
    from {{ ref('stg_tmdb_movies') }}

)

select
    movie_id,
    title,
    original_title,
    release_date,
    release_year,
    original_language,
    runtime,
    status

from movies
qualify row_number() over (
    partition by movie_id
    order by extracted_at desc
) = 1