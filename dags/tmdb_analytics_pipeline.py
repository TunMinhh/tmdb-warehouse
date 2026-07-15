from __future__ import annotations

from datetime import datetime, timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_DIR = "/opt/airflow/project"
DBT_DIR = f"{PROJECT_DIR}/tmdb_project"
LOCAL_TZ = pendulum.timezone("Asia/Ho_Chi_Minh")


default_args = {
    "owner": "tmdb_project",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="tmdb_analytics_pipeline",
    description="Daily TMDB popular/trending extract followed by dbt run and tests.",
    default_args=default_args,
    start_date=datetime(2026, 7, 1, tzinfo=LOCAL_TZ),
    schedule="0 23 * * *",
    catchup=False,
    tags=["tmdb", "daily", "snowflake", "dbt"],
) as dag:
    extract_daily = BashOperator(
        task_id="extract_popular_and_trending",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m extract.jobs.daily_extract --popular-pages 10"
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

    extract_daily >> dbt_run >> dbt_test