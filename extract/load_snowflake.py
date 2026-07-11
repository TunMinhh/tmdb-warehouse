import json

import snowflake.connector

from extract.configs import settings


REQUIRED_SNOWFLAKE_SETTINGS = {
    "SNOWFLAKE_ACCOUNT": settings.snowflake_account,
    "SNOWFLAKE_USER": settings.snowflake_user,
    "SNOWFLAKE_PASSWORD": settings.snowflake_password,
    "SNOWFLAKE_WAREHOUSE": settings.snowflake_warehouse,
    "SNOWFLAKE_DATABASE": settings.snowflake_database,
}


def validate_snowflake_settings() -> None:
    missing = [name for name, value in REQUIRED_SNOWFLAKE_SETTINGS.items() if not value]

    if missing:
        missing_names = ", ".join(missing)
        raise ValueError(f"Missing Snowflake settings: {missing_names}")


def raw_table_name() -> str:
    # Use a fully qualified name so Airflow/dbt sessions do not depend on current schema.
    return (
        f"{settings.snowflake_database}."
        f"{settings.snowflake_schema}."
        f"{settings.snowflake_raw_table}"
    )


def get_connection(include_schema: bool = True):
    validate_snowflake_settings()

    connection_args = {
        "account": settings.snowflake_account,
        "user": settings.snowflake_user,
        "password": settings.snowflake_password,
        "warehouse": settings.snowflake_warehouse,
        "database": settings.snowflake_database,
    }

    if include_schema:
        connection_args["schema"] = settings.snowflake_schema

    if settings.snowflake_role:
        connection_args["role"] = settings.snowflake_role

    return snowflake.connector.connect(**connection_args)


def ensure_raw_table() -> None:
    create_schema_sql = f"create schema if not exists {settings.snowflake_schema}"
    create_table_sql = f"""
    create table if not exists {raw_table_name()} (
        raw_response_id number autoincrement start 1 increment 1,
        source_endpoint string not null,
        endpoint_name string not null,
        request_params variant,
        response_json variant not null,
        business_date date not null,
        extracted_at timestamp_ntz not null default current_timestamp()
    )
    """

    with get_connection(include_schema=False) as conn:
        with conn.cursor() as cur:
            cur.execute(create_schema_sql)
            cur.execute(create_table_sql)


def insert_raw_api_response(
    conn,
    source_endpoint: str,
    endpoint_name: str,
    request_params: dict,
    response_json: dict,
    business_date: str,
) -> None:
    # Keep request/response JSON as VARIANT; dbt staging models can flatten it later.
    sql = f"""
    insert into {raw_table_name()} (
        source_endpoint,
        endpoint_name,
        request_params,
        response_json,
        business_date,
        extracted_at
    )
    select
        %s,
        %s,
        parse_json(%s),
        parse_json(%s),
        to_date(%s),
        current_timestamp()
    """

    params = (
        source_endpoint,
        endpoint_name,
        json.dumps(request_params or {}),
        json.dumps(response_json),
        business_date,
    )

    with conn.cursor() as cur:
        cur.execute(sql, params)