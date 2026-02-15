# RBAC and Network Policies

This document describes the RBAC and network policy configuration for restricting authorization and traffic between workload clusters.

## 1. RBAC (Role-Based Access Control)

### What's configured

- **Dedicated ServiceAccounts**: `weather-api` and `air-quality-api` – pods run as these instead of `default`.
- **Minimal Role**: Empty rules – apps don't need k8s API access.
- **RoleBinding**: Binds the Role to the ServiceAccount in each namespace.

### Effect

- Each app pod is identified by its ServiceAccount.
- No extra k8s API permissions beyond the default (effectively none).
- Defense in depth: even if a pod is compromised, it cannot list pods, secrets, or other resources.

### Files

| App              | Base                               | Overlay patches                    |
|------------------|------------------------------------|------------------------------------|
| weather-api      | `api-fastapi/base/serviceaccount.yaml`, `rbac-role.yaml`, `rbac-rolebinding.yaml` | `overlays/*/rbac-rolebinding-patch.yaml` |
| air-quality-api  | `air-quality-api/base/...`          | Same pattern                       |

## 2. Network Policies

### Ingress (who can reach the API)

- **Same namespace**: Pods in the same namespace (e.g. Service → Pod) can reach port 8000.
- **VPC CIDR**: ALB traffic from the cluster's VPC is allowed.

### Overlay-specific VPC CIDRs

| Overlay     | Cluster   | VPC CIDR       |
|-------------|-----------|----------------|
| development | platform-dev-eks  | 10.30.0.0/16 |
| production  | platform-prod-eks | 10.20.0.0/16 |
| uat         | platform-ua-eks   | 10.40.0.0/16 |

Each overlay patches the base network policy with the correct CIDR for its workload cluster.

### Egress (unchanged)

- DNS (UDP 53) to kube-system.
- HTTPS (TCP 443) to external APIs, excluding private ranges.

## 3. Argo CD Projects (restrict deployment targets)

Argo CD AppProjects limit which clusters each project can deploy to. These live in `weather-platform-terraform/helm/argocd/projects.yaml`.

Each project restricts deployments to its cluster and namespaces only:

| Project     | Cluster            | Namespaces                                                                 |
|-------------|--------------------|----------------------------------------------------------------------------|
| development | platform-dev-eks   | `weather-api-development`, `air-quality-api-development`                  |
| uat         | platform-ua-eks    | `weather-api-uat`, `air-quality-api-uat`                                 |
| production  | platform-prod-eks  | `weather-api`, `air-quality-api`                                          |

Cluster URLs are configured in `weather-platform-terraform/helm/argocd/projects.yaml`.

## 4. ApplicationSet and workload clusters

To deploy to workload clusters instead of the hub:

1. Register clusters in Argo CD (`argocd cluster add <context>`).
2. Add a `uat` AppProject in `weather-platform-terraform/helm/argocd/projects.yaml` (if missing).
3. Update each project's `destinations` with the correct cluster `server` URL.
4. Update the ApplicationSet `server` fields in:
   - `api-fastapi/argocd-applicationset-weather-api.yaml`
   - `air-quality-api/argocd-applicationset-air-quality-api.yaml`

Replace `https://kubernetes.default.svc` with the spoke cluster API URL for each env.
