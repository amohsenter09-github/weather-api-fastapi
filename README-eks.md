# Deploy `weather-api-fastapi` to AWS EKS (ALB Ingress + WAF + CloudFront)

This guide assumes you have **another repo** that provisions the AWS/EKS infrastructure. This repo provides the app and Kubernetes manifests.

## Target architecture

- **EKS** runs the app Pods (`Deployment`) behind a ClusterIP `Service`
- **AWS Load Balancer Controller** provisions an **ALB** from a Kubernetes `Ingress`
- **AWS WAFv2** protects traffic (recommended at **CloudFront**, optionally also at **ALB**)
- **CloudFront** fronts the ALB (TLS, caching, global edge, WAF attach point)

Request flow:
`Client → CloudFront (WAF) → ALB → Service → Pod`

### Architecture diagram

```mermaid
flowchart LR
  U[User / Client] -->|HTTPS| CF[CloudFront Distribution]
  WAF[WAFv2 Web ACL\n(scope: CLOUDFRONT)] --> CF
  CF -->|Origin request| ALB[(Application Load Balancer)]

  subgraph AWS[EKS / AWS]
    subgraph EKS[EKS Cluster]
      ING[Ingress (k8s)] -->|watched by| LBC[AWS Load Balancer Controller]
      LBC -->|provisions| ALB
      ALB --> SVC[Service (ClusterIP)]
      SVC --> PODS[Pods (Deployment)]
    end
  end

  R53[Route 53 DNS\napi.example.com] --> CF
  ACM1[ACM Cert (us-east-1)\nfor CloudFront] --> CF
  ACM2[ACM Cert (region)\noptional for ALB HTTPS] --> ALB
  WAF2[WAFv2 Web ACL\n(scope: REGIONAL)\noptional] --> ALB
```

## Prerequisites (infrastructure repo)

Your infra repo should provide at minimum:

- **EKS cluster** + node group(s) (or Fargate) + `kubectl` access
- **OIDC provider** enabled for IRSA
- **AWS Load Balancer Controller** installed (Helm) with:
  - IAM role for controller (IRSA)
  - correct `clusterName`, `region`, `vpcId`
- (Optional but common) **ExternalDNS** for Route53 records
- **ACM certificate** for your public domain (for ALB HTTPS)
- **CloudFront distribution** (optional) and **WAFv2 WebACL** (recommended)

## 1) Build and push the image (ECR recommended)

EKS nodes pull images easiest from **ECR**.

Example (adjust region/account/repo):

```bash
AWS_REGION=eu-west-1
AWS_ACCOUNT_ID=123456789012
ECR_REPO=weather-api-fastapi

aws ecr create-repository --repository-name "$ECR_REPO" --region "$AWS_REGION" 2>/dev/null || true
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build -t "$ECR_REPO:latest" .
docker tag "$ECR_REPO:latest" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest"
```

## 2) Deploy the app to EKS

### Point kubectl to your EKS cluster

Your cluster:
`arn:aws:eks:eu-west-1:918780499156:cluster/platform-dev-eks`

Run:

```bash
aws eks update-kubeconfig --region eu-west-1 --name platform-dev-eks
kubectl config current-context
kubectl get nodes
```

### Configure the image

Edit `k8s-eks/deployment.yaml` and set:

- `image: <your-ecr-repo-uri>:<tag>`

### Apply manifests

```bash
kubectl apply -k k8s-eks/
kubectl -n weather-api get pods,svc,ingress
```

### Test (once ALB is ready)

Get the ALB hostname:

```bash
kubectl -n weather-api get ingress weather-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}{"\n"}'
```

Then:

- `http://<alb-hostname>/health`
- `http://<alb-hostname>/weather?city=Berlin`

### DNS with ExternalDNS (Route53)

If your cluster has the ExternalDNS addon and you control a Route53 hosted zone (example: `cloud-master-ai.com`),
the Ingress can request a record like:

- `weather.cloud-master-ai.com`

This repo’s `k8s-eks/ingress-alb.yaml` includes:
- `spec.rules[].host: weather.cloud-master-ai.com`
- `external-dns.alpha.kubernetes.io/hostname: weather.cloud-master-ai.com`

Verify:

```bash
kubectl -n weather-api describe ingress weather-api
kubectl -n weather-api get ingress weather-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}{"\n"}'
```

## 3) ALB Ingress: recommended annotations

This repo includes an example ALB Ingress at `k8s-eks/ingress-alb.yaml` using:

- internet-facing ALB
- target-type `ip`
- healthcheck `/health`
- HTTP (port 80) by default

### Enable HTTPS on the ALB

Add to `k8s-eks/ingress-alb.yaml`:

- `alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80},{"HTTPS":443}]'`
- `alb.ingress.kubernetes.io/certificate-arn: <acm-arn-in-your-region>`
- `alb.ingress.kubernetes.io/ssl-redirect: "443"`

## 4) Add WAF (recommended patterns)

### Recommended: WAF on CloudFront

- Create a **WAFv2 WebACL** in scope **CLOUDFRONT**
- Attach AWS managed rule groups (example):
  - `AWSManagedRulesCommonRuleSet`
  - `AWSManagedRulesKnownBadInputsRuleSet`
  - `AWSManagedRulesAmazonIpReputationList`
- Associate the WebACL with your **CloudFront distribution**

### Optional: WAF on ALB too

You can also attach a **regional WAFv2 WebACL** to the ALB for an extra layer (useful if ALB is directly reachable).

## 5) Put CloudFront in front of the ALB

CloudFront setup (high-level):

- **Origin**: the ALB DNS name
- **Viewer protocol policy**: Redirect HTTP → HTTPS
- **ACM cert**: must be in **us-east-1** for CloudFront
- **Cache policy**:
  - For APIs, typically set **low TTL** or disable caching unless you’re sure responses can be cached
- **WAF**: attach WebACL (recommended)

After creating CloudFront:

- Create DNS record (Route53) `api.example.com` → CloudFront distribution
- Use `https://api.example.com/health` etc.

## 6) How to expose paths / multiple services

ALB Ingress can route by host/path. Example:

- `api.example.com/weather` → `weather-api` service
- `argocd.example.com/` → `argocd-server` service (different namespace/ingress)

Each Ingress can create its own ALB, or you can share one ALB using:
- `alb.ingress.kubernetes.io/group.name: <shared-group>`

## Notes / gotchas

- **Ingress controller choice**: on EKS, for ALB you typically use **AWS Load Balancer Controller** (not nginx) for the public edge.
- **TLS cert location**:
  - ALB cert: ACM in the same region as the ALB
  - CloudFront cert: ACM in **us-east-1**
- **Caching**: be careful caching dynamic API responses in CloudFront.
- **Health checks**: make sure `/health` stays fast and returns 200.

## Troubleshooting

### ALB Ingress error: couldn't auto-discover subnets (missing VPC tags)

If you see an event like:
`Failed build model due to couldn't auto-discover subnets ... tags: [kubernetes.io/role/elb]`

It means the AWS Load Balancer Controller **could not find any subnets in the cluster VPC** tagged for ALB creation.

Typical required tags:

- Public subnets (internet-facing ALB):
  - `kubernetes.io/role/elb=1`
  - `kubernetes.io/cluster/<cluster-name>=shared` (or `owned`)
- Private subnets (internal ALB):
  - `kubernetes.io/role/internal-elb=1`
  - `kubernetes.io/cluster/<cluster-name>=shared` (or `owned`)

Workarounds:
- Add the missing tags in your infra repo (recommended).
- Or explicitly select subnets with the Ingress annotation:
  - `alb.ingress.kubernetes.io/subnets: subnet-aaa,subnet-bbb`

### Pod Pending: `0/1 nodes are available: Too many pods`

If you see:
`FailedScheduling ... Too many pods`

Your node is at its **max pod capacity** (common on small instance types).

Fix:
- Scale your nodegroup to **2+ nodes**, or use a larger instance type.
- Then you can increase `spec.replicas` in `k8s-eks/deployment.yaml`.
