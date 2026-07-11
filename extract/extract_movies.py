import time
from typing import Iterable

from extract.configs import settings
from extract.load_snowflake import insert_raw_api_response
from extract.tmdb_client import TMDBClient


def save_raw_response(
    conn,
    data: dict,
    source_endpoint: str,
    endpoint_name: str,
    business_date: str,
    request_params: dict | None = None,
) -> None:
    # Store raw API response first; dbt will flatten JSON later.
    insert_raw_api_response(
        conn=conn,
        source_endpoint=source_endpoint,
        endpoint_name=endpoint_name,
        request_params=request_params or {},
        response_json=data,
        business_date=business_date,
    )


def collect_movie_ids(response: dict) -> set[int]:
    return {movie["id"] for movie in response.get("results", []) if movie.get("id")}


def extract_genres(client: TMDBClient, conn, business_date: str) -> int:
    endpoint = "/genre/movie/list"
    params = {"language": settings.tmdb_language}
    data = client.get(endpoint, params=params)

    save_raw_response(conn, data, endpoint, "genre_movie_list", business_date, params)
    return 1


def extract_trending_movies(
    client: TMDBClient,
    conn,
    business_date: str,
    time_window: str,
) -> tuple[int, set[int]]:
    endpoint = f"/trending/movie/{time_window}"
    params = {"language": settings.tmdb_language}
    data = client.get(endpoint, params=params)

    save_raw_response(
        conn=conn,
        data=data,
        source_endpoint=endpoint,
        endpoint_name=f"trending_movie_{time_window}",
        business_date=business_date,
        request_params={"time_window": time_window, **params},
    )

    # Collect movie IDs for detail and credits fan-out calls.
    return 1, collect_movie_ids(data)


def extract_movie_list(
    client: TMDBClient,
    conn,
    business_date: str,
    endpoint: str,
    endpoint_name: str,
    pages: int,
) -> tuple[int, set[int]]:
    inserted_count = 0
    movie_ids = set()
    base_params = {"language": settings.tmdb_language}

    responses = client.get_paginated(endpoint, pages=pages, params=base_params)

    for response in responses:
        request_params = dict(base_params)
        request_params["page"] = response.get("page")

        save_raw_response(conn, response, endpoint, endpoint_name, business_date, request_params)
        inserted_count += 1
        movie_ids.update(collect_movie_ids(response))

    return inserted_count, movie_ids


def extract_discover_movies(
    client: TMDBClient,
    conn,
    business_date: str,
    year: int,
    pages: int,
    sort_by: str = "popularity.desc",
) -> tuple[int, set[int]]:
    endpoint = "/discover/movie"
    endpoint_name = "discover_movie"
    inserted_count = 0
    movie_ids = set()

    base_params = {
        "language": settings.tmdb_language,
        "include_adult": "false",
        "primary_release_year": year,
        "sort_by": sort_by,
    }

    responses = client.get_paginated(endpoint, pages=pages, params=base_params)

    for response in responses:
        request_params = dict(base_params)
        request_params["page"] = response.get("page")

        save_raw_response(conn, response, endpoint, endpoint_name, business_date, request_params)
        inserted_count += 1
        movie_ids.update(collect_movie_ids(response))

    return inserted_count, movie_ids


def extract_movie_details(
    client: TMDBClient,
    conn,
    business_date: str,
    movie_ids: Iterable[int],
    sleep_seconds: float = 0.25,
) -> int:
    inserted_count = 0

    for movie_id in sorted(set(movie_ids)):
        endpoint = f"/movie/{movie_id}"
        api_params = {"language": settings.tmdb_language}
        request_params = dict(api_params)
        request_params["movie_id"] = movie_id
        data = client.get(endpoint, params=api_params)

        save_raw_response(conn, data, endpoint, "movie_detail", business_date, request_params)
        inserted_count += 1
        time.sleep(sleep_seconds)

    return inserted_count


def extract_movie_credits(
    client: TMDBClient,
    conn,
    business_date: str,
    movie_ids: Iterable[int],
    sleep_seconds: float = 0.25,
) -> int:
    inserted_count = 0

    for movie_id in sorted(set(movie_ids)):
        endpoint = f"/movie/{movie_id}/credits"
        api_params = {"language": settings.tmdb_language}
        request_params = dict(api_params)
        request_params["movie_id"] = movie_id
        data = client.get(endpoint, params=api_params)

        save_raw_response(conn, data, endpoint, "movie_credits", business_date, request_params)
        inserted_count += 1
        time.sleep(sleep_seconds)

    return inserted_count