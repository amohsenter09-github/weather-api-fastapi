import requests
from typing import Dict, Any, Optional
from app.config import settings


class WeatherService:
    """Service for interacting with OpenWeatherMap API."""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self):
        self.api_key = settings.openweather_api_key
    
    def get_current_weather(self, city: str, units: str = "metric") -> Dict[str, Any]:
        """
        Get current weather for a city.
        
        Args:
            city: City name
            units: Units of measurement (metric, imperial, standard)
        
        Returns:
            Weather data dictionary
        
        Raises:
            Exception: If API request fails
        """
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key is not configured")
        
        url = f"{self.BASE_URL}/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": units
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    def get_forecast(self, city: str, units: str = "metric") -> Dict[str, Any]:
        """
        Get 5-day weather forecast for a city.
        
        Args:
            city: City name
            units: Units of measurement (metric, imperial, standard)
        
        Returns:
            Forecast data dictionary
        
        Raises:
            Exception: If API request fails
        """
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key is not configured")
        
        url = f"{self.BASE_URL}/forecast"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": units
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json()


weather_service = WeatherService()
