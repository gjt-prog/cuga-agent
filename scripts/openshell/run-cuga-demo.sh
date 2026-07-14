#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

: "${OPENAI_API_KEY:?Set OPENAI_API_KEY in the environment or local .env}"
: "${OPENAI_BASE_URL:?Set OPENAI_BASE_URL in the environment or local .env}"
: "${MODEL_NAME:?Set MODEL_NAME in the environment or local .env}"

PROVIDER_NAME="${OPENSHELL_CUGA_PROVIDER:-cuga-openai}"
SANDBOX_NAME="${OPENSHELL_CUGA_SANDBOX:-cuga-demo}"
FORWARD_PORT="${OPENSHELL_CUGA_PORT:-7860}"
TIMEOUT_SECONDS="${OPENSHELL_INFERENCE_TIMEOUT:-300}"
PROVIDER_BASE_URL="${OPENSHELL_OPENAI_BASE_URL:-$OPENAI_BASE_URL}"
BUILD_CONTEXT="$(mktemp -d "${TMPDIR:-/tmp}/cuga-openshell-build.XXXXXX")"

cleanup() {
  if [[ "${OPENSHELL_KEEP_BUILD_CONTEXT:-0}" != "1" ]]; then
    rm -rf "$BUILD_CONTEXT"
  else
    echo "Kept OpenShell build context at $BUILD_CONTEXT" >&2
  fi
}
trap cleanup EXIT

if ! command -v openshell >/dev/null 2>&1; then
  echo "openshell is not installed or not on PATH" >&2
  exit 127
fi

cp Dockerfile.openshell "$BUILD_CONTEXT/Dockerfile"
cp pyproject.toml uv.lock "$BUILD_CONTEXT/"
mkdir -p "$BUILD_CONTEXT/src" "$BUILD_CONTEXT/scripts/openshell"
cp -R src/. "$BUILD_CONTEXT/src/"
cp scripts/openshell/cuga-openshell-demo.sh "$BUILD_CONTEXT/scripts/openshell/"

if openshell provider get "$PROVIDER_NAME" >/dev/null 2>&1; then
  openshell provider update "$PROVIDER_NAME" \
    --credential OPENAI_API_KEY \
    --config "OPENAI_BASE_URL=$PROVIDER_BASE_URL"
else
  openshell provider create \
    --name "$PROVIDER_NAME" \
    --type openai \
    --credential OPENAI_API_KEY \
    --config "OPENAI_BASE_URL=$PROVIDER_BASE_URL"
fi

openshell inference set \
  --provider "$PROVIDER_NAME" \
  --model "$MODEL_NAME" \
  --timeout "$TIMEOUT_SECONDS"

openshell sandbox create \
  --name "$SANDBOX_NAME" \
  --from "$BUILD_CONTEXT" \
  --forward "$FORWARD_PORT" \
  --provider "$PROVIDER_NAME" \
  --policy cuga-policy.yaml \
  -- /usr/local/bin/cuga-openshell-demo
