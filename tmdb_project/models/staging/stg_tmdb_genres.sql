with genre_responses as (

    select
        raw_response_id,
        response_json,
        business_date,
        extracted_at
    from {{ ref('stg_tmdb_api_responses') }}
    where endpoint_name = 'genre_movie_list'

)

select
    genre.value:id::number as genre_id,
    genre.value:name::string as genre_name,
    business_date,
    extracted_at,
    raw_response_id
from genre_responses,
lateral flatten(input => response_json:genres) as genre