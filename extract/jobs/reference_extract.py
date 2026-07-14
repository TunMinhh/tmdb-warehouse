import argparse
import json
from datetime import date

from extract.configs import settings
from extract.extract_movies import extract_genres
from extract.load_snowflake import ensure_raw_table, get_connection
from extract.tmdb_client import TMDBClient


def run_reference_extract(
    business_date: str | None = None,
    create_table: bool = True,
) -> dict:
    business_date = business_date or date.today().isoformat()

    if create_table:
        ensure_raw_table()

    client = TMDBClient()

    with get_connection(include_schema=False) as conn:
        genre_count = extract_genres(client, conn, business_date)

    return {
        "business_date": business_date,
        "snowflake_table": f"{settings.snowflake_database}.{settings.snowflake_schema}.{settings.snowflake_raw_table}",
        "raw_rows_inserted": {
            "genre_movie_list": genre_count,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract slow-changing TMDB reference data into Snowflake.")
    parser.add_argument("--business-date", default=date.today().isoformat())
    parser.add_argument("--skip-create-table", action="store_true")
    args = parser.parse_args()

    summary = run_reference_extract(
        business_date=args.business_date,
        create_table=not args.skip_create_table,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()