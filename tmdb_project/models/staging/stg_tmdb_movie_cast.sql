with credit_responses as (
    select
        raw_response_id,
        request_params,
        response_json,
        business_date,
        extracted_at
    from {{ ref('stg_tmdb_api_responses') }}
    where endpoint_name = 'movie_credits'
)

-- There's also crew info (Director and such...) but i will only take cast infos 

select
    request_params:movie_id::number as movie_id,
    cast_member.value:id::number as person_id,
    cast_member.value:credit_id::string as credit_id,
    cast_member.value:cast_id::number as cast_id,
    cast_member.value:name::string as actor_name,
    cast_member.value:character::string as character_name,
    cast_member.value:order::number as cast_order, --I think this is used for importance level
    cast_member.value:popularity::float as actor_popularity,
    cast_member.value:gender::number as gender_code, --1 for women 2 for men
    business_date,
    extracted_at,
    raw_response_id
from credit_responses,
lateral flatten(input => response_json:cast) as cast_member