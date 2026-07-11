with movies as (

    select *
    from {{ ref('stg_tmdb_movies') }}

)

select
    movie_id,
    release_year,
    runtime,

    popularity,
    vote_average,
    vote_count,

    budget,
    revenue,
    revenue - budget as profit,

    case
        when budget > 0 then revenue / budget
        else null
    end as roi,

    case
        when vote_count >= 100 then true
        else false
    end as has_enough_votes,

    extracted_at

from movies
qualify row_number() over (
    partition by movie_id
    order by extracted_at desc
) = 1