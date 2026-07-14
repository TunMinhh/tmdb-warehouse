import argparse
import json
from datetime import date

from extract.configs import settings
from extract.extract_movies import (
    extract_discover_movies,
    extract_movie_credits,
    extract_movie_details,
)
from extract.load_snowflake import ensure_raw_table, get_connection
from extract.tmdb_client import TMDBClient


def run_discover_backfill(
    start_year: int,
    end_year: int,
    pages_per_year: int = 10,
    business_date: str | None = None,
    sort_by: str = "popularity.desc",
    include_details: bool = True,
    include_credits: bool = True,
    create_table: bool = True,
) -> dict:
    if start_year > end_year:
        raise ValueError("start_year must be less than or equal to end_year")

    business_date = business_date or date.today().isoformat()

    if create_table:
        ensure_raw_table()

    client = TMDBClient()
    movie_ids = set()
    discover_rows_by_year = {}

    # One Snowflake connection for the whole backfill run.
    with get_connection(include_schema=False) as conn:
        for year in range(start_year, end_year + 1):
            inserted_count, year_movie_ids = extract_discover_movies(
                client=client,
                conn=conn,
                business_date=business_date,
                year=year,
                pages=pages_per_year,
                sort_by=sort_by,
            )
            discover_rows_by_year[str(year)] = inserted_count
            movie_ids.update(year_movie_ids)

        # These fan-out calls are optional because they can be much heavier than discover pages.
        detail_count = extract_movie_details(client, conn, business_date, movie_ids) if include_details else 0
        credit_count = extract_movie_credits(client, conn, business_date, movie_ids) if include_credits else 0

    return {
        "business_date": business_date,
        "snowflake_table": f"{settings.snowflake_database}.{settings.snowflake_schema}.{settings.snowflake_raw_table}",
        "year_range": f"{start_year}-{end_year}",
        "pages_per_year": pages_per_year,
        "sort_by": sort_by,
        "unique_movie_count": len(movie_ids),
        "raw_rows_inserted": {
            "discover_movie": sum(discover_rows_by_year.values()),
            "movie_detail": detail_count,
            "movie_credits": credit_count,
        },
        "discover_rows_by_year": discover_rows_by_year,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill TMDB discover/movie data into Snowflake.")
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--pages-per-year", type=int, default=10)
    parser.add_argument("--business-date", default=date.today().isoformat())
    parser.add_argument("--sort-by", default="popularity.desc")
    parser.add_argument("--skip-details", action="store_true")
    parser.add_argument("--skip-credits", action="store_true")
    parser.add_argument("--skip-create-table", action="store_true")
    args = parser.parse_args()

    summary = run_discover_backfill(
        start_year=args.start_year,
        end_year=args.end_year,
        pages_per_year=args.pages_per_year,
        business_date=args.business_date,
        sort_by=args.sort_by,
        include_details=not args.skip_details,
        include_credits=not args.skip_credits,
        create_table=not args.skip_create_table,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()