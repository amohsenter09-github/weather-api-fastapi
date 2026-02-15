#!/usr/bin/env bash
# Sanity check: run kustomize build on all overlays.
# Exits with 1 if any build fails.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OVERLAYS=(
  "api-fastapi/overlays/development"
  "api-fastapi/overlays/uat"
  "api-fastapi/overlays/production"
  "air-quality-api/overlays/development"
  "air-quality-api/overlays/uat"
  "air-quality-api/overlays/production"
)

FAILED=0
for overlay in "${OVERLAYS[@]}"; do
  echo "Building $overlay ..."
  if output=$(kustomize build "$overlay" 2>&1); then
    echo "  ✓ $overlay OK"
  else
    echo "  ✗ $overlay FAILED"
    echo "$output" | head -50
    FAILED=1
  fi
done

if [ $FAILED -eq 1 ]; then
  echo ""
  echo "One or more overlays failed to build."
  exit 1
fi

echo ""
echo "All overlays built successfully."
