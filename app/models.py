from pydantic import BaseModel
from typing import List, Optional


class Weather(BaseModel):
    """Weather condition details."""
    main: str
    description: str
    icon: str


class Temperature(BaseModel):
    """Temperature information."""
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int


class Wind(BaseModel):
    """Wind information."""
    speed: float
    deg: Optional[int] = None


class Coordinates(BaseModel):
    """Geographic coordinates."""
    lon: float
    lat: float


class CurrentWeatherResponse(BaseModel):
    """Current weather response model."""
    city: str
    country: str
    coordinates: Coordinates
    temperature: Temperature
    weather: List[Weather]
    wind: Wind
    visibility: int
    timestamp: int


class ForecastItem(BaseModel):
    """Individual forecast item."""
    datetime: str
    temperature: Temperature
    weather: List[Weather]
    wind: Wind


class WeatherForecastResponse(BaseModel):
    """Weather forecast response model."""
    city: str
    country: str
    forecasts: List[ForecastItem]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
