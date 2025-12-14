from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
import requests

from app.models import (
    CurrentWeatherResponse,
    WeatherForecastResponse,
    ErrorResponse,
    Weather,
    Temperature,
    Wind,
    Coordinates,
    ForecastItem
)
from app.weather_service import weather_service

app = FastAPI(
    title="Weather API",
    description="A FastAPI-based weather API that provides current weather and forecasts",
    version="1.0.0",
    docs_url="/",
    redoc_url="/redoc"
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get(
    "/weather/current/{city}",
    response_model=CurrentWeatherResponse,
    tags=["Weather"],
    summary="Get current weather",
    responses={
        200: {"description": "Successfully retrieved current weather"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "City not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_current_weather(
    city: str,
    units: str = Query(
        default="metric",
        description="Units of measurement (metric, imperial, standard)",
        regex="^(metric|imperial|standard)$"
    )
):
    """
    Get current weather for a specified city.
    
    - **city**: City name (e.g., "London", "New York")
    - **units**: Units of measurement
        - metric: Celsius, meter/sec
        - imperial: Fahrenheit, miles/hour
        - standard: Kelvin, meter/sec
    """
    try:
        data = weather_service.get_current_weather(city, units)
        
        return CurrentWeatherResponse(
            city=data["name"],
            country=data["sys"]["country"],
            coordinates=Coordinates(
                lon=data["coord"]["lon"],
                lat=data["coord"]["lat"]
            ),
            temperature=Temperature(
                temp=data["main"]["temp"],
                feels_like=data["main"]["feels_like"],
                temp_min=data["main"]["temp_min"],
                temp_max=data["main"]["temp_max"],
                pressure=data["main"]["pressure"],
                humidity=data["main"]["humidity"]
            ),
            weather=[
                Weather(
                    main=w["main"],
                    description=w["description"],
                    icon=w["icon"]
                ) for w in data["weather"]
            ],
            wind=Wind(
                speed=data["wind"]["speed"],
                deg=data["wind"]["deg"]
            ),
            visibility=data.get("visibility", 0),
            timestamp=data["dt"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"City '{city}' not found")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather data: {str(e)}")


@app.get(
    "/weather/forecast/{city}",
    response_model=WeatherForecastResponse,
    tags=["Weather"],
    summary="Get weather forecast",
    responses={
        200: {"description": "Successfully retrieved weather forecast"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "City not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_weather_forecast(
    city: str,
    units: str = Query(
        default="metric",
        description="Units of measurement (metric, imperial, standard)",
        regex="^(metric|imperial|standard)$"
    )
):
    """
    Get 5-day weather forecast for a specified city.
    
    - **city**: City name (e.g., "London", "New York")
    - **units**: Units of measurement
        - metric: Celsius, meter/sec
        - imperial: Fahrenheit, miles/hour
        - standard: Kelvin, meter/sec
    """
    try:
        data = weather_service.get_forecast(city, units)
        
        forecasts = []
        for item in data["list"]:
            forecasts.append(
                ForecastItem(
                    datetime=item["dt_txt"],
                    temperature=Temperature(
                        temp=item["main"]["temp"],
                        feels_like=item["main"]["feels_like"],
                        temp_min=item["main"]["temp_min"],
                        temp_max=item["main"]["temp_max"],
                        pressure=item["main"]["pressure"],
                        humidity=item["main"]["humidity"]
                    ),
                    weather=[
                        Weather(
                            main=w["main"],
                            description=w["description"],
                            icon=w["icon"]
                        ) for w in item["weather"]
                    ],
                    wind=Wind(
                        speed=item["wind"]["speed"],
                        deg=item["wind"]["deg"]
                    )
                )
            )
        
        return WeatherForecastResponse(
            city=data["city"]["name"],
            country=data["city"]["country"],
            forecasts=forecasts
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"City '{city}' not found")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch forecast data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
