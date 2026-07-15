# TMDB Movie Analytics Data Warehouse

End-to-end data engineering and analytics project using the TMDB API, Snowflake, dbt, and Airflow.

The project extracts movie data from TMDB, stores raw API responses as JSON in Snowflake, transforms the data into analytics-ready dimensional marts with dbt, and orchestrates the recurring pipeline with Airflow.

## Project Goals

This project is designed to answer movie analytics questions such as:

- Which movies are currently popular or trending?
- Which genres have the highest revenue, rating, and ROI?
- Are highly rated movies also high-revenue movies?
- Which actors appear most often in popular or high-performing movies?
- How different are trending movies from popular movies?

## Architecture

```text
TMDB API
   |
   v
Python extraction jobs
   |
   v
Snowflake RAW schema
raw TMDB API responses stored as VARIANT JSON
   |
   v
dbt staging views
parsed and cleaned API responses
   |
   v
dbt marts
dimensions, bridge tables, and fact tables
   |
   v
Power BI / Tableau / SQL analysis
```

## Tech Stack

- Python: API extraction and Snowflake loading
- TMDB API: movie, genre, trending, popular, discover, and credits data
- Snowflake: cloud data warehouse
- dbt: staging and mart transformations
- Airflow: orchestration, scheduling, retries, and task monitoring
- Docker Compose: local Airflow environment
- Power BI / Tableau: dashboard layer

## Repository Structure

```text
.
|-- dags/
|   |-- tmdb_analytics_pipeline.py
|   `-- tmdb_discover_backfill.py
|-- docker/
|   `-- airflow/Dockerfile
|-- extract/
|   |-- configs.py
|   |-- tmdb_client.py
|   |-- extract_movies.py
|   |-- load_snowflake.py
|   `-- jobs/
|       |-- daily_extract.py
|       |-- reference_extract.py
|       `-- backfill_discover.py
|-- tmdb_project/
|   |-- dbt_project.yml
|   |-- profiles/profiles.yml
|   `-- models/
|       |-- sources.yml
|       |-- staging/
|       `-- marts/
|-- docker-compose.yml
|-- requirements.txt
|-- .env.example
`-- DOCS.md
```\r
\r
## Data Sources

The pipeline uses these TMDB API endpoints:

- `/movie/popular`
- `/trending/movie/day`
- `/trending/movie/week`
- `/discover/movie`
- `/movie/{movie_id}`
- `/movie/{movie_id}/credits`
- `/genre/movie/list`

The raw API payloads are stored in Snowflake before any parsing or transformation. This keeps the ingestion layer flexible and auditable.

## Snowflake Raw Layer

Raw API responses are stored in:

```text
TMDB_DWH.RAW.RAW_TMDB_API_RESPONSES
```

The raw table stores:

- `source_endpoint`
- `endpoint_name`
- `request_params`
- `response_json`
- `business_date`
- `extracted_at`

`request_params` and `response_json` are Snowflake `VARIANT` columns, so nested JSON can be parsed later in dbt.


## Limitations

- The dataset is a TMDB sample, not a complete global movie industry dataset.
- TMDB popularity is a platform-specific metric.
- Historical discover backfills sorted by popularity use current TMDB popularity, not popularity at the original release date.
- Revenue and budget values depend on TMDB data availability and quality.


