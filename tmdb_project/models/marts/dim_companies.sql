select
    company_id,
    company_name,
    origin_country

from {{ ref('stg_tmdb_movie_companies') }}
qualify row_number() over (
    partition by company_id
    order by extracted_at desc, company_name
) = 1
