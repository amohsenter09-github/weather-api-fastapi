from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.services.weather_client import WeatherClient

router = APIRouter(prefix="", tags=["weather"])


@router.get("/weather")
async def get_weather(
    city: str | None = Query(default=None),
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
):
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
            latitude = float(geo["latitude"])
            longitude = float(geo["longitude"])
            location = {
                "name": geo.get("name"),
                "country": geo.get("country"),
                "admin1": geo.get("admin1"),
                "latitude": latitude,
                "longitude": longitude,
            }
        else:
            location = {"latitude": latitude, "longitude": longitude}

        data = await client.current_weather(latitude=latitude, longitude=longitude)  # type: ignore[arg-type]
        return {"location": location, "current_weather": data.get("current_weather"), "raw": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail="Upstream weather provider error") from e



