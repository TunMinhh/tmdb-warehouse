import argparse
import json
from datetime import date

from extract.configs import settings
from extract.extract_movies import (
    extract_genres,
    extract_movie_credits,
    extract_movie_details,
    extract_movie_list,
    extract_trending_movies,
)
from extract.load_snowflake import ensure_raw_table, get_connection
from extract.tmdb_client import TMDBClient


def run_daily_extract(
    business_date: str | None = None,
    popular_pages: int = 10,
    include_details: bool = True,
    include_credits: bool = True,
    create_table: bool = True,
) -> dict:
    business_date = business_date or date.today().isoformat()

    if create_table:
        ensure_raw_table()

    client = TMDBClient()
    movie_ids = set()

    # Open one Snowflake connection for this run, then reuse it for all inserts.
    with get_connection(include_schema=False) as conn:
        genre_count = extract_genres(client, conn, business_date)

        trending_day_count, trending_day_ids = extract_trending_movies(client, conn, business_date, "day")
        movie_ids.update(trending_day_ids)

        trending_week_count, trending_week_ids = extract_trending_movies(client, conn, business_date, "week")
        movie_ids.update(trending_week_ids)

        popular_count, popular_ids = extract_movie_list(
            client=client,
            conn=conn,
            business_date=business_date,
            endpoint="/movie/popular",
            endpoint_name="movie_popular",
            pages=popular_pages,
        )
        movie_ids.update(popular_ids)

        # Details and credits are optional because they can create many API calls.
        detail_count = extract_movie_details(client, conn, business_date, movie_ids) if include_details else 0
        credit_count = extract_movie_credits(client, conn, business_date, movie_ids) if include_credits else 0

    return {
        "business_date": business_date,
        "snowflake_table": f"{settings.snowflake_database}.{settings.snowflake_schema}.{settings.snowflake_raw_table}",
        "unique_movie_count": len(movie_ids),
        "raw_rows_inserted": {
            "genre_movie_list": genre_count,
            "trending_movie_day": trending_day_count,
            "trending_movie_week": trending_week_count,
            "movie_popular": popular_count,
            "movie_detail": detail_count,
            "movie_credits": credit_count,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract TMDB API data into Snowflake raw table.")
    parser.add_argument("--business-date", default=date.today().isoformat())
    parser.add_argument("--popular-pages", type=int, default=10)
    parser.add_argument("--skip-details", action="store_true")
    parser.add_argument("--skip-credits", action="store_true")
    parser.add_argument("--skip-create-table", action="store_true")
    args = parser.parse_args()

    summary = run_daily_extract(
        business_date=args.business_date,
        popular_pages=args.popular_pages,
        include_details=not args.skip_details,
        include_credits=not args.skip_credits,
        create_table=not args.skip_create_table,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()