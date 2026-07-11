with discover_responses as (

    select
        raw_response_id,
        request_params,
        response_json,
        business_date,
        extracted_at
    from {{ ref('stg_tmdb_api_responses') }}
    where endpoint_name = 'discover_movie'

)

select
    movie.value:id::number as movie_id,
    request_params:primary_release_year::number as discover_year,
    request_params:sort_by::string as sort_by,
    request_params:page::number as page_number,
    ((request_params:page::number - 1) * 20) + movie.index + 1 as overall_rank,
    business_date,
    extracted_at,
    raw_response_id
from discover_responses,
lateral flatten(input => response_json:results) as movie
where movie.value:adult::boolean = false