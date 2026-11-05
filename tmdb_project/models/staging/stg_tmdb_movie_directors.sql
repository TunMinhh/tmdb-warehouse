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

select
    request_params:movie_id::number as movie_id,
    crew_member.value:id::number as person_id,
    crew_member.value:name::string as director_name,
    business_date,
    extracted_at,
    raw_response_id
from credit_responses,
lateral flatten(input => response_json:crew) as crew_member
where crew_member.value:job::string = 'Director'
