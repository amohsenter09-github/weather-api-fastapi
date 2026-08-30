# weather-api-fastapi

Sample FastAPI workload used to exercise the delivery platform. This is not a production weather product. The same image is what GitOps deploys to `workload-dev` and `workload-prod`.

Current conditions, 24-hour and 7-day forecast, saved places, and nearby alert evaluation.

## Role in the platform

| Piece | Repo |
| --- | --- |
| This app + Dockerfile | [weather-api-fastapi](https://github.com/amohsenter09-github/weather-api-fastapi) |
| Kustomize base + overlays | [kustomization-resources-applications](https://github.com/amohsenter09-github/kustomization-resources-applications) (`apps/weather-api`) |
| Argo CD Application | [bootstrap-control-plane](https://github.com/amohsenter09-github/bootstrap-control-plane) (`app-weather-dev`, `app-weather-prod`) |
| Cluster, registry, DNS | [scaleway-infrastructure](https://github.com/amohsenter09-github/scaleway-infrastructure) |

Image Updater watches `rg.fr-par.scw.cloud/cnpe/weather-api:02`.

**Scaleway URLs:** https://weather-api.cnpe-dev.cloud-master-ai.com · https://weather-api.cnpe-prod.cloud-master-ai.com

## Implementation

- FastAPI + SQLAlchemy async + PostgreSQL
- Static UI at `/`; “Use my location” fills lat/lon
- Open-Meteo for current, hourly, and daily forecast
- Saved alerts (`metric` + `operator` + `threshold`); `GET /alerts/evaluate` returns matches within 5 km

## Endpoints

- `GET /health` — process up (no Postgres)
- `GET /ready` — Postgres reachable
- `GET /weather` — current + 24 hourly + 7-day (`city` or `latitude`+`longitude`)
- `POST /places` · `GET /places` · `DELETE /places/{id}`
- `POST /places/{id}/refresh` · `GET /places/{id}/history`
- `POST /alerts` — `{ "place_id", "metric":"temperature", "operator":"lt", "threshold":0 }`
- `GET /alerts/evaluate?latitude=&longitude=`

## Local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up postgres
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

UI: http://localhost:8000/ · docs: http://localhost:8000/docs

Or `docker compose up --build` (API **8000**, Postgres host **5434**).

## Image for Kapsule

```bash
docker buildx build --platform linux/amd64 --provenance=false --sbom=false \
  -t rg.fr-par.scw.cloud/cnpe/weather-api:02 --push .
```

Kind local overlay still uses `weather-api:01`.
