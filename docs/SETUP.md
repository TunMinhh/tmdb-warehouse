# Setup & How to Run

Step-by-step guide to run the TMDB analytics pipeline from a fresh clone to queryable marts in Snowflake.
For an overview of the project, see the [README](../README.md).

## Contents

- [Prerequisites](#prerequisites)
- [1. Clone the repository](#1-clone-the-repository)
- [2. Prepare Snowflake (one time)](#2-prepare-snowflake-one-time)
- [3. Configure environment variables](#3-configure-environment-variables)
- [4. Start Airflow](#4-start-airflow)
- [5. Check the Snowflake connection](#5-check-the-snowflake-connection)
- [6. Load reference data (genres)](#6-load-reference-data-genres)
- [7. Backfill historical movies](#7-backfill-historical-movies)
- [8. Enable the daily pipeline](#8-enable-the-daily-pipeline)
- [9. Verify the data](#9-verify-the-data)
- [Alternative: run without Docker](#alternative-run-without-docker)
- [Troubleshooting](#troubleshooting)

## Prerequisites

| Requirement | Notes |
|---|---|
| Docker + Docker Compose | On Windows, use Docker Desktop with WSL 2 integration |
| TMDB account | *Settings → API*. Use the **API Read Access Token** (the long `eyJ...` string), **not** the short API key. The client sends it as a `Bearer` token |
| Snowflake account | A free trial is enough |

## 1. Clone the repository

```bash
git clone <repo-url> tmdb_project
cd tmdb_project
```

## 2. Prepare Snowflake (one time)

Run the script below in a Snowsight worksheet. You only need to create the warehouse, database, role and user. The Python jobs create the `RAW` schema and raw table, and dbt creates the `ANALYTICS` schema.

```sql
use role ACCOUNTADMIN;

create warehouse if not exists TMDB_WH
  warehouse_size = XSMALL auto_suspend = 60 auto_resume = true;
create database if not exists TMDB_DWH;

create role if not exists TMDB_ROLE;
grant usage on warehouse TMDB_WH to role TMDB_ROLE;
grant usage, create schema on database TMDB_DWH to role TMDB_ROLE;

create user if not exists TMDB_USER
  password = '<strong-password>'
  default_role = TMDB_ROLE
  default_warehouse = TMDB_WH;
grant role TMDB_ROLE to user TMDB_USER;
grant role TMDB_ROLE to role SYSADMIN;
```

Then get your **account identifier**:

```sql
select current_organization_name() || '-' || current_account_name() as account_identifier;
```

Use the `ORGNAME-ACCOUNTNAME` format. Do not mix the organization name with the account locator. If you do, the connection fails with `404 Not Found ... login-request`.

## 3. Configure environment variables

```bash
cp .env.example .env
```

| Variable | Value |
|---|---|
| `TMDB_API_KEY` | TMDB API Read Access Token |
| `SNOWFLAKE_ACCOUNT` | `ORGNAME-ACCOUNTNAME` from step 2 |
| `SNOWFLAKE_USER` / `SNOWFLAKE_PASSWORD` | `TMDB_USER` and its password |
| `SNOWFLAKE_ROLE` | `TMDB_ROLE`. **Required** by the dbt profile |
| `SNOWFLAKE_WAREHOUSE` | `TMDB_WH` |
| `AIRFLOW_UID` | output of `id -u` (usually `1000` on Linux / WSL) |
| `AIRFLOW_POSTGRES_PASSWORD`, `AIRFLOW_ADMIN_PASSWORD` | any strong passwords |
| `AIRFLOW_WEBSERVER_SECRET_KEY` | output of `openssl rand -hex 32` |

Avoid trailing spaces after the values.

## 4. Start Airflow

Create the mounted folders first. Otherwise Docker creates them as `root` and Airflow cannot write to them.

```bash
mkdir -p logs/airflow plugins
docker compose build
docker compose up airflow-init      # wait until it exits with code 0
docker compose up -d
```

Open <http://localhost:8080> and log in as `admin` with `AIRFLOW_ADMIN_PASSWORD`. Both DAGs start **paused**.

> Docker reads `.env` only when a container is **created**. After changing `.env`, run `docker compose up -d --force-recreate`; a plain `restart` is not enough.

## 5. Check the Snowflake connection

```bash
docker compose exec airflow-scheduler bash -c \
  "cd /opt/airflow/project/tmdb_project && dbt debug"
```

The output must end with `All checks passed!`.

## 6. Load reference data (genres)

No DAG runs this job yet, so run it once by hand. It also creates the raw table.

```bash
docker compose exec airflow-scheduler bash -c \
  "cd /opt/airflow/project && python -m extract.jobs.reference_extract"
```

## 7. Backfill historical movies

In the Airflow UI, open **`tmdb_discover_backfill`** → ▶ → **Trigger DAG w/ config**. Start with a small run:

```json
{"start_year": 2024, "end_year": 2025, "pages_per_year": 2}
```

This config loads about 80 movies in a few minutes. The default (2017–2026, 10 pages per year) loads about 2,000 movies and can take over an hour.

The extract task prints a JSON summary **only when it finishes**. An empty log while it is running is normal.

## 8. Enable the daily pipeline

Unpause **`tmdb_analytics_pipeline`**. It runs every day at 23:00 (Asia/Ho_Chi_Minh). To load popular and trending data right away, trigger it manually once.

Airflow only runs while Docker is up. Because `catchup=False`, missed days are not backfilled.

## 9. Verify the data

```sql
use role TMDB_ROLE;
use warehouse TMDB_WH;

-- Raw responses per endpoint
select endpoint_name, business_date, count(*)
from TMDB_DWH.RAW.RAW_TMDB_API_RESPONSES
group by 1, 2 order by 2 desc, 1;

-- Row counts in the marts
select 'dim_movies' as model, count(*) from TMDB_DWH.ANALYTICS.DIM_MOVIES
union all select 'dim_genres', count(*) from TMDB_DWH.ANALYTICS.DIM_GENRES
union all select 'dim_people', count(*) from TMDB_DWH.ANALYTICS.DIM_PEOPLE
union all select 'fact_movie_performance', count(*) from TMDB_DWH.ANALYTICS.FACT_MOVIE_PERFORMANCE
union all select 'fact_movie_popular_snapshot', count(*) from TMDB_DWH.ANALYTICS.FACT_MOVIE_POPULAR_SNAPSHOT
union all select 'fact_movie_trending_snapshot', count(*) from TMDB_DWH.ANALYTICS.FACT_MOVIE_TRENDING_SNAPSHOT;

-- Example analysis: average rating by genre
select g.genre_name, count(*) as movies, round(avg(f.vote_average), 2) as avg_rating
from TMDB_DWH.ANALYTICS.FACT_MOVIE_PERFORMANCE f
join TMDB_DWH.ANALYTICS.BRIDGE_MOVIE_GENRES b using (movie_id)
join TMDB_DWH.ANALYTICS.DIM_GENRES g using (genre_id)
where f.has_enough_votes
group by 1
order by avg_rating desc;
```

`dim_genres` should contain 19 rows. Re-running a job does not create duplicates in the marts: raw is append-only, and dbt deduplicates in staging and in every mart.

## Alternative: run without Docker

This is useful for development and debugging.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# dbt does not read .env by itself: export the variables into the shell
set -a && source .env && set +a
export DBT_PROFILES_DIR=$PWD/tmdb_project/profiles

python -m extract.jobs.reference_extract
python -m extract.jobs.backfill_discover --start-year 2024 --end-year 2025 --pages-per-year 2
python -m extract.jobs.daily_extract --popular-pages 2

cd tmdb_project
dbt build --select staging marts
```

Every job accepts `--help`. Useful flags: `--skip-details`, `--skip-credits`, `--business-date YYYY-MM-DD`.

To browse model documentation and the lineage graph:

```bash
dbt docs generate && dbt docs serve --port 8081
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `401 Unauthorized` from TMDB | You used the short API key; use the API Read Access Token |
| `290404 (08001): 404 Not Found ... login-request` | Wrong `SNOWFLAKE_ACCOUNT` format (see step 2) |
| `Env var required but not provided: 'SNOWFLAKE_ROLE'` | Set `SNOWFLAKE_ROLE` in `.env` |
| dbt still connects to an old account | A profile in `~/.dbt/profiles.yml` takes priority. Set `DBT_PROFILES_DIR` or remove the old profile |
| Containers still use old credentials | `docker compose up -d --force-recreate` |
| `Permission denied` on `logs/` or `tmdb_project/target/` | `AIRFLOW_UID` differs from `id -u`, or the folders from step 4 were not created |
| `Object 'RAW_TMDB_API_RESPONSES' does not exist` | No extract job has run yet (steps 6–7) |
| `dim_genres` is empty | Step 6 was skipped |
| Extract task fails with `404` | A movie was removed from TMDB. Clear the task to retry |
