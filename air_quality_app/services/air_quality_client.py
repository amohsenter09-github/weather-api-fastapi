from __future__ import annotations

from typing import Any

import httpx

from air_quality_app.core.config import Settings


class AirQualityClient:
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

    async def current_air_quality(self, latitude: float, longitude: float) -> dict[str, Any]:
        url = f"{self._settings.open_meteo_air_quality_base_url.rstrip('/')}/air-quality"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "us_aqi,european_aqi,pm10,pm2_5,ozone,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
