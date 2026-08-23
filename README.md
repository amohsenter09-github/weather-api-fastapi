# weather-api-fastapi

Weather API microservice built with FastAPI.

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

## Kubernetes

Overlays live under `k8s/overlays/`:

| Overlay | Cluster | Namespace | Host | Image |
| --- | --- | --- | --- | --- |
| `local` | kind | `weather-api` | `weather-api.local` | `weather-api:local` |
| `cnpe-dev` | cnpe-dev | `weather-api-cnpe-dev` | `weather-api.cnpe-dev` | `weather-api:cnpe-dev` |
| `cnpe-prod` | cnpe-prod | `weather-api-cnpe-prod` | `weather-api.cnpe-prod` | `weather-api:cnpe-prod` |

Validate all overlays:

```bash
./scripts/kustomize-build.sh
```

### Local kind

1. Create the kind cluster:

```bash
kind delete cluster --name local-cluster
kind create cluster --name local-cluster --config kind-ingress-config.yaml
kubectl config use-context kind-local-cluster
```

2. Install ingress-nginx:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl -n ingress-nginx wait --for=condition=Ready pod -l app.kubernetes.io/component=controller --timeout=180s
```

3. Build and load the image:

```bash
docker build -t weather-api:local .
kind load docker-image weather-api:local --name local-cluster
```

4. Apply the local overlay:

```bash
kubectl apply -k k8s/overlays/local
```

5. Add a host entry (macOS):

```bash
sudo sh -c 'echo "127.0.0.1 weather-api.local" >> /etc/hosts'
```

Then open:

- `http://weather-api.local/health`
- `http://weather-api.local/weather?city=Berlin`
- `http://weather-api.local/docs`

### CNPE

```bash
kubectl apply -k k8s/overlays/cnpe-dev
kubectl apply -k k8s/overlays/cnpe-prod
```
