# weather-api-fastapi

Weather API microservice built with FastAPI.

Kubernetes manifests live in the sibling `kustomization-resources-applications` repo (`apps/weather-api`, image `weather-api:01`).

## Endpoints

- `GET /health` -> process up (does not need Postgres)
- `GET /ready` -> Postgres reachable
- `GET /weather` -> live Open-Meteo current weather plus 24 hourly and 7-day forecast (city or lat/lon)
- `POST /places` -> save a place (`{"name":"Berlin","latitude":52.52,"longitude":13.41}` or `{"city":"Berlin"}`)
- `GET /places` -> list saved places
- `POST /places/{id}/refresh` -> fetch live weather and store an observation
- `GET /places/{id}/history` -> last N snapshots
- `POST /alerts` -> `{ "place_id", "metric":"temperature", "operator":"lt", "threshold":0 }`
- `GET /alerts/evaluate?latitude=&longitude=` -> triggered alerts for saved places within 5 km
- `DELETE /places/{id}`

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

For `POST /places` and `GET /ready`, start Postgres first (`docker compose up postgres`).

## Docker

```bash
docker compose up --build
```

Local host port: **8000**. Postgres is on host **5434**.

## Kubernetes

```bash
docker build -t weather-api:01 .
kubectl apply -k ../kustomization-resources-applications/apps/weather-api/overlays/local
```
