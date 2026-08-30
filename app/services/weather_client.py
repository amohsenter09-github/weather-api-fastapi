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
            "hourly": "temperature_2m,precipitation_probability,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "forecast_days": 7,
            "timezone": "auto",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def compact_forecast(data: dict[str, Any]) -> dict[str, Any]:
        hourly = data.get("hourly") or {}
        times = hourly.get("time") or []
        temps = hourly.get("temperature_2m") or []
        rain = hourly.get("precipitation_probability") or []
        codes = hourly.get("weather_code") or []
        wind = hourly.get("wind_speed_10m") or []
        hourly_out = []
        for index, time in enumerate(times[:24]):
            hourly_out.append({
                "time": time,
                "temperature": temps[index] if index < len(temps) else None,
                "precipitation_probability": rain[index] if index < len(rain) else None,
                "weathercode": codes[index] if index < len(codes) else None,
                "windspeed": wind[index] if index < len(wind) else None,
            })
        daily = data.get("daily") or {}
        days = daily.get("time") or []
        codes_d = daily.get("weather_code") or []
        tmax = daily.get("temperature_2m_max") or []
        tmin = daily.get("temperature_2m_min") or []
        prmax = daily.get("precipitation_probability_max") or []
        daily_out = []
        for index, day in enumerate(days[:7]):
            daily_out.append({
                "date": day,
                "weathercode": codes_d[index] if index < len(codes_d) else None,
                "temperature_max": tmax[index] if index < len(tmax) else None,
                "temperature_min": tmin[index] if index < len(tmin) else None,
                "precipitation_probability_max": prmax[index] if index < len(prmax) else None,
            })
        return {"hourly": hourly_out, "daily": daily_out}
