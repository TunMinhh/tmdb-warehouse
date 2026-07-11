import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    tmdb_api_key: str = os.getenv("TMDB_API_KEY", "")
    tmdb_language: str = os.getenv("TMDB_LANGUAGE", "en-US")

    snowflake_account: str = os.getenv("SNOWFLAKE_ACCOUNT", "")
    snowflake_user: str = os.getenv("SNOWFLAKE_USER", "")
    snowflake_password: str = os.getenv("SNOWFLAKE_PASSWORD", "")
    snowflake_role: str = os.getenv("SNOWFLAKE_ROLE", "")
    snowflake_warehouse: str = os.getenv("SNOWFLAKE_WAREHOUSE", "")
    snowflake_database: str = os.getenv("SNOWFLAKE_DATABASE", "TMDB_DWH")
    snowflake_schema: str = os.getenv("SNOWFLAKE_SCHEMA", "RAW")
    snowflake_raw_table: str = os.getenv("SNOWFLAKE_RAW_TABLE", "RAW_TMDB_API_RESPONSES")


settings = Settings()