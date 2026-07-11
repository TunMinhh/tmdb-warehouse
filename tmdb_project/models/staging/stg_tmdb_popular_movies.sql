with popular_responses as (

    select
        raw_response_id,
        request_params,
        response_json,
        business_date,
        extracted_at
    from {{ ref('stg_tmdb_api_responses') }}
    where endpoint_name = 'movie_popular'

)

select
    movie.value:id::number as movie_id,
    request_params:page::number as page_number,
    ((request_params:page::number - 1) * 20) + movie.index + 1 as overall_rank,
    business_date,
    extracted_at,
    raw_response_id
from popular_responses,
lateral flatten(input => response_json:results) as movie