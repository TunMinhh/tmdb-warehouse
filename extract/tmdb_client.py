import time

import requests

from extract.configs import settings


class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self):
        if not settings.tmdb_api_key:
            raise ValueError("Missing TMDB_API_KEY")

        # Reuse one session so every request automatically includes auth headers.
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {settings.tmdb_api_key}",
                "accept": "application/json",
            }
        )

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.get(url, params=params, timeout=30)

        # TMDB may return 429 if requests are too fast; wait and retry once.
        if response.status_code == 429:
            time.sleep(5)
            response = self.session.get(url, params=params, timeout=30)

        response.raise_for_status()
        return response.json()

    def get_paginated(
        self,
        endpoint: str,
        pages: int = 1,
        params: dict | None = None,
    ) -> list[dict]:
        if pages < 1:
            raise ValueError("pages must be greater than or equal to 1")

        results = []

        for page in range(1, pages + 1):
            # Copy params so adding page does not mutate the caller's dict.
            page_params = dict(params or {})
            page_params["page"] = page

            data = self.get(endpoint, page_params)
            results.append(data)

            time.sleep(0.5)

        return results