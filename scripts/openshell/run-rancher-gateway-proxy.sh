#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

CONTAINER_NAME="${OPENSHELL_RANCHER_PROXY_CONTAINER:-openshell-rd-gateway-proxy}"
PYTHON_IMAGE="${OPENSHELL_RANCHER_PROXY_IMAGE:-python:3.12-slim-trixie}"

exec docker run --rm \
  --name "$CONTAINER_NAME" \
  --network host \
  -v "$ROOT_DIR/scripts/openshell/rancher-gateway-proxy.py:/proxy.py:ro" \
  "$PYTHON_IMAGE" \
  python -u /proxy.py
