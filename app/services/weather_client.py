from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings


class WeatherClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._timeout = httpx.Timeout(settings.http_timeout_seconds)

    async def geocode_city(self, city: str) -> dict[str, Any]:
        url = f"{self._settings.open_meteo_geocoding_base_url.rstrip('/')}/search"
        params = {"name": city, "count": 1, "language": "en", "format": "json"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        results = data.get("results") or []
        if not results:
            raise ValueError(f"City not found: {city}")
        return results[0]

    async def current_weather(self, latitude: float, longitude: float) -> dict[str, Any]:
        url = f"{self._settings.open_meteo_base_url.rstrip('/')}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()



