select
    movie_id,
    person_id,
    credit_id,
    cast_id,
    character_name,
    cast_order,
    actor_popularity,

    case
        when cast_order <= 2 then true
        else false
    end as is_lead_actor,

    business_date,
    extracted_at

from {{ ref('stg_tmdb_movie_cast') }}
qualify row_number() over (
    partition by movie_id, person_id, credit_id
    order by extracted_at desc
) = 1