from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_DIR = "/opt/airflow/project"
DBT_DIR = f"{PROJECT_DIR}/tmdb_project"


default_args = {
    "owner": "tmdb_project",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="tmdb_discover_backfill",
    description="Manual TMDB discover backfill by release year, followed by dbt rebuild.",
    default_args=default_args,
    start_date=datetime(2026, 7, 1),
    schedule=None,
    catchup=False,
    params={
        "start_year": 2017,
        "end_year": 2026,
        "pages_per_year": 10,
    },
    tags=["tmdb", "backfill", "snowflake", "dbt"],
) as dag:
    backfill_discover = BashOperator(
        task_id="backfill_discover_movies",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m extract.jobs.backfill_discover "
            "--start-year {{ params.start_year }} "
            "--end-year {{ params.end_year }} "
            "--pages-per-year {{ params.pages_per_year }}"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run_staging_and_marts",
        bash_command=(
            f"cd {DBT_DIR} && "
            "dbt run --select staging marts"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test_staging_and_marts",
        bash_command=(
            f"cd {DBT_DIR} && "
            "dbt test --select staging marts"
        ),
    )

    backfill_discover >> dbt_run >> dbt_test