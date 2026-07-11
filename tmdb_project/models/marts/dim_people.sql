with people as (

    select
        person_id,
        actor_name,
        gender_code,
        extracted_at
    from {{ ref('stg_tmdb_movie_cast') }}

)

select
    person_id,
    actor_name,
    gender_code,

    case gender_code
        when 1 then 'Female'
        when 2 then 'Male'
        when 3 then 'Non-binary'
        else 'Unknown'
    end as gender

from people
qualify row_number() over (
    partition by person_id
    order by extracted_at desc, actor_name
) = 1