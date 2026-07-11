with trending_responses as (

    select
        raw_response_id,
        endpoint_name,
        request_params,
        response_json,
        business_date,
        extracted_at
    from {{ ref('stg_tmdb_api_responses') }}
    where endpoint_name in ('trending_movie_day', 'trending_movie_week')

)

select
    movie.value:id::number as movie_id,
    case
        when endpoint_name = 'trending_movie_day' then 'day'
        when endpoint_name = 'trending_movie_week' then 'week'
    end as time_window,

    movie.index + 1 as trending_rank,
    business_date,
    extracted_at,
    raw_response_id
from trending_responses,
lateral flatten(input => response_json:results) as movie