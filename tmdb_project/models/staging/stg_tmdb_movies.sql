with movie_detail_responses as (

    select
        raw_response_id,
        response_json,
        business_date,
        extracted_at
    from {{ ref('stg_tmdb_api_responses') }}
    where endpoint_name = 'movie_detail'

)

select
    response_json:id::number as movie_id,
    response_json:title::string as title,
    response_json:original_title::string as original_title,
    try_to_date(response_json:release_date::string) as release_date,
    year(try_to_date(response_json:release_date::string)) as release_year,

    response_json:popularity::float as popularity,
    response_json:vote_average::float as vote_average,
    response_json:vote_count::number as vote_count,

    response_json:budget::number as budget,
    response_json:revenue::number as revenue,
    response_json:runtime::number as runtime,

    case
        when response_json:budget::number > 0
            then response_json:revenue::float / response_json:budget::float
        else null
    end as roi,

    response_json:status::string as status,
    response_json:original_language::string as original_language,
    
    business_date,
    extracted_at,
    raw_response_id

from movie_detail_responses
where response_json:adult::boolean = false