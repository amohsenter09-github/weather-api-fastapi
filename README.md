# Weather API - FastAPI

A modern, RESTful weather API built with FastAPI and Python that provides current weather information and forecasts for cities worldwide.

## Features

- 🌤️ Get current weather data for any city
- 📅 Retrieve 5-day weather forecasts
- 🌡️ Support for multiple temperature units (Celsius, Fahrenheit, Kelvin)
- 📚 Interactive API documentation (Swagger UI)
- ✅ Health check endpoint
- 🔒 Environment-based configuration

## Prerequisites

- Python 3.8 or higher
- OpenWeatherMap API key (get it free at https://openweathermap.org/api)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/amohsenter09-github/weather-api-fastapi.git
cd weather-api-fastapi
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
```

4. Add your OpenWeatherMap API key to the `.env` file:
```
OPENWEATHER_API_KEY=your_actual_api_key_here
```

## Usage

### Running the Application

Start the server using:
```bash
python run.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check
```
GET /health
```
Check if the API is running.

### Current Weather
```
GET /weather/current/{city}?units=metric
```
Get current weather for a city.

**Parameters:**
- `city` (path): City name (e.g., "London", "New York")
- `units` (query, optional): Units of measurement
  - `metric` (default): Celsius, meter/sec
  - `imperial`: Fahrenheit, miles/hour
  - `standard`: Kelvin, meter/sec

**Example:**
```bash
curl http://localhost:8000/weather/current/London?units=metric
```

### Weather Forecast
```
GET /weather/forecast/{city}?units=metric
```
Get 5-day weather forecast for a city.

**Parameters:**
- `city` (path): City name (e.g., "London", "New York")
- `units` (query, optional): Units of measurement (same as above)

**Example:**
```bash
curl http://localhost:8000/weather/forecast/Paris?units=metric
```

## Example Responses

### Current Weather Response
```json
{
  "city": "London",
  "country": "GB",
  "coordinates": {
    "lon": -0.1257,
    "lat": 51.5085
  },
  "temperature": {
    "temp": 15.5,
    "feels_like": 14.8,
    "temp_min": 13.2,
    "temp_max": 17.1,
    "pressure": 1013,
    "humidity": 72
  },
  "weather": [
    {
      "main": "Clouds",
      "description": "scattered clouds",
      "icon": "03d"
    }
  ],
  "wind": {
    "speed": 4.1,
    "deg": 230
  },
  "visibility": 10000,
  "timestamp": 1639478400
}
```

## Project Structure

```
weather-api-fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and routes
│   ├── models.py            # Pydantic models
│   ├── weather_service.py   # Weather API service
│   └── config.py            # Configuration settings
├── .env.example             # Example environment file
├── .gitignore              # Git ignore file
├── requirements.txt        # Python dependencies
├── run.py                  # Application entry point
└── README.md               # This file
```

## Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running the application
- **Pydantic**: Data validation using Python type annotations
- **Requests**: HTTP library for API calls
- **python-dotenv**: Environment variable management

## Error Handling

The API includes comprehensive error handling:
- `400 Bad Request`: Invalid parameters or missing API key
- `404 Not Found`: City not found
- `500 Internal Server Error`: Server-side errors

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.