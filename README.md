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

## Kubernetes (kind)

### Option A (recommended): Ingress on host ports 80/443 (no port-forward)

This repo includes `kind-ingress-config.yaml` which creates a kind cluster with port mappings so you can use:
- `http://weather-api.local/health`
- `http://weather-api.local/weather?city=Berlin`
- `http://weather-api.local/docs`

1. (Re)create the kind cluster:

```bash
kind delete cluster --name local-cluster
kind create cluster --name local-cluster --config kind-ingress-config.yaml
```

2. Set context:

```bash
kubectl config use-context kind-local-cluster
```

3. Install ingress-nginx:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl -n ingress-nginx wait --for=condition=Ready pod -l app.kubernetes.io/component=controller --timeout=180s
```

4. Apply manifests:

```bash
kubectl apply -k k8s/
```

5. Verify:

```bash
kubectl -n weather-api get pods,svc,ing
```

6. Add host entry (macOS):

```bash
sudo sh -c 'echo "127.0.0.1 weather-api.local" >> /etc/hosts'
```

### Local image workflow (kind)

If you want to build the Docker image locally (fast iteration), use the kind overlay:

```bash
docker build -t weather-api-fastapi:local .
kind load docker-image weather-api-fastapi:local --name local-cluster
kubectl apply -k k8s-kind/
```

### Option B: Port-forward (works even without host port mappings)

If you have an ingress controller but your kind cluster does not expose ports 80/443, port-forward the controller:

```bash
kubectl -n ingress-nginx port-forward svc/ingress-nginx-controller 8080:80
```

Then use (and ensure `weather-api.local` is in `/etc/hosts`):
- `http://weather-api.local:8080/health`
- `http://weather-api.local:8080/weather?city=Berlin`
- `http://weather-api.local:8080/docs`