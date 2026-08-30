import logging

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.services.weather_client import WeatherClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["weather"])


def _normalize_city(city: str | None) -> str | None:
    if city is None:
        return None
    city = city.strip()
    return city or None


@router.get("/weather")
async def get_weather(
    city: str | None = Query(default=None),
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
):
    city = _normalize_city(city)
    if city is None and (latitude is None or longitude is None):
        raise HTTPException(
            status_code=400,
            detail="Provide either city=... or latitude=...&longitude=...",
        )

    settings = get_settings()
    client = WeatherClient(settings)

    try:
        if city is not None:
            geo = await client.geocode_city(city)
            resolved_lat = float(geo["latitude"])
            resolved_lon = float(geo["longitude"])
            location = {
                "name": geo.get("name"),
                "country": geo.get("country"),
                "admin1": geo.get("admin1"),
                "latitude": resolved_lat,
                "longitude": resolved_lon,
            }
        else:
            resolved_lat = float(latitude)
            resolved_lon = float(longitude)
            location = {"latitude": resolved_lat, "longitude": resolved_lon}

        data = await client.current_weather(latitude=resolved_lat, longitude=resolved_lon)
        forecast = client.compact_forecast(data)
        return {
            "location": location,
            "current_weather": data.get("current_weather"),
            "hourly": forecast["hourly"],
            "daily": forecast["daily"],
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except httpx.HTTPError as e:
        logger.exception("Upstream weather provider error")
        raise HTTPException(status_code=502, detail="Upstream weather provider error") from e
