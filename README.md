# weather-api-fastapi

Weather API microservice built with FastAPI.

Kubernetes manifests live in the sibling `kustomization-resources-applications` repo.

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

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open the GUI at `http://localhost:8000/` and API docs at `http://localhost:8000/docs`.

## Docker

```bash
docker build -t weather-api:local .
docker compose up --build
```

Local host port: **8000** (`http://localhost:8000`).
