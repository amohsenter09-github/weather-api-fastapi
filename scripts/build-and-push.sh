#!/usr/bin/env bash
# Build and push weather-api and air-quality-api images to all ECR repos.
# Requires: docker, aws-cli, AWS credentials with ECR push access.
#
# Usage: ./scripts/build-and-push.sh [tag]
#   tag: image tag (default: latest)

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-918780499156}"
AWS_REGION="${AWS_REGION:-eu-west-1}"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
TAG="${1:-latest}"

echo "=== Logging in to ECR ==="
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$ECR_REGISTRY"

echo ""
echo "=== Building weather-platform ==="
docker build -f Dockerfile --platform linux/amd64 -t weather-platform:"$TAG" .
docker tag weather-platform:"$TAG" "$ECR_REGISTRY/weather-platform:$TAG"
docker tag weather-platform:"$TAG" "$ECR_REGISTRY/weather-platform-dev:$TAG"
docker tag weather-platform:"$TAG" "$ECR_REGISTRY/weather-platform-ua:$TAG"

echo "=== Pushing weather-platform to ECR ==="
docker push "$ECR_REGISTRY/weather-platform:$TAG"
docker push "$ECR_REGISTRY/weather-platform-dev:$TAG"
docker push "$ECR_REGISTRY/weather-platform-ua:$TAG"

echo ""
echo "=== Building air-quality-platform ==="
docker build -f Dockerfile.air-quality --platform linux/amd64 -t air-quality-platform:"$TAG" .
docker tag air-quality-platform:"$TAG" "$ECR_REGISTRY/air-quality-platform:$TAG"
docker tag air-quality-platform:"$TAG" "$ECR_REGISTRY/air-quality-platform-dev:$TAG"
docker tag air-quality-platform:"$TAG" "$ECR_REGISTRY/air-quality-platform-ua:$TAG"

echo "=== Pushing air-quality-platform to ECR ==="
docker push "$ECR_REGISTRY/air-quality-platform:$TAG"
docker push "$ECR_REGISTRY/air-quality-platform-dev:$TAG"
docker push "$ECR_REGISTRY/air-quality-platform-ua:$TAG"

echo ""
echo "Done. Images pushed with tag: $TAG"
