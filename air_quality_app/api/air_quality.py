from fastapi import APIRouter, HTTPException, Query

from air_quality_app.core.config import get_settings
from air_quality_app.services.air_quality_client import AirQualityClient

router = APIRouter(prefix="", tags=["air-quality"])


@router.get("/air-quality")
async def get_air_quality(
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
    client = AirQualityClient(settings)

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

        data = await client.current_air_quality(latitude=latitude, longitude=longitude)
        return {"location": location, "current_air_quality": data.get("current"), "raw": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail="Upstream air quality provider error") from e
