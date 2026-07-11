-- Common cleaned layer for all raw TMDB API responses.
-- It keeps the latest response when the same endpoint/date/params is loaded more than once.

with source as (

    select
        raw_response_id,
        source_endpoint,
        endpoint_name,
        request_params,
        response_json,
        business_date,
        extracted_at
    from {{ source('tmdb_raw', 'raw_tmdb_api_responses') }}

),

deduplicated as (

    select *
    from source

    qualify row_number() over (
        partition by
            endpoint_name,
            business_date,
            to_json(request_params)
        order by extracted_at desc
    ) = 1

)

select
    raw_response_id,
    source_endpoint,
    endpoint_name,
    request_params,
    response_json,
    business_date,
    extracted_at
from deduplicated