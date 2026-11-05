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
    company.value:id::number as company_id,
    company.value:name::string as company_name,
    company.value:origin_country::string as origin_country,
    business_date,
    extracted_at,
    raw_response_id
from movie_detail_responses,
lateral flatten(input => response_json:production_companies) as company
where response_json:adult::boolean = false
