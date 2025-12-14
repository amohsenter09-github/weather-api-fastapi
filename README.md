# weather-api-fastapi

Minimal Weather API built with FastAPI.

## Endpoints

- `GET /health` -> service health check
- `GET /weather` -> current weather by city or coordinates

### `GET /weather` query params

- `city` (string) OR
- `latitude` (float) + `longitude` (float)

Example:

- `GET /weather?city=Berlin`
- `GET /weather?latitude=52.52&longitude=13.41`

## Local dev (venv)

1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create an env file:

```bash
cp .env.example .env
```

3. Run the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open API docs at `http://localhost:8000/docs`.

## Docker

```bash
docker compose up --build
```