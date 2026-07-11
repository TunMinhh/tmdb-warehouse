with movie_detail_responses as (

    select
        raw_response_id,
        response_json,
        business_date,
        extracted_at
    from {{ ref('stg_tmdb_api_responses') }}
    where endpoint_name = 'movie_detail'

)

-- A movie might have many genre, so I will have a separate staging for it
-- So it won't be repeated or left in JSON structure in marts
select
    response_json:id::number as movie_id,
    genre.value:id::number as genre_id,
    genre.value:name::string as genre_name,
    business_date,
    extracted_at,
    raw_response_id
from movie_detail_responses,
lateral flatten(input => response_json:genres) as genre