#!/usr/bin/env sh
set -eu

export AGENT_SETTING_CONFIG="${AGENT_SETTING_CONFIG:-settings.openai.toml}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://inference.local/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-unused}"
export MODEL_NAME="${MODEL_NAME:-openshell-routed-model}"
export CUGA_DBS_DIR="${CUGA_DBS_DIR:-/tmp/cuga/dbs}"
export CUGA_LOGGING_DIR="${CUGA_LOGGING_DIR:-/tmp/cuga/logging}"
export CUGA_FOLDER="${CUGA_FOLDER:-/tmp/cuga/policies}"
# Local embedding cache lives under writable /tmp; the model is baked into the
# image (huggingface.co egress is policy-denied) and seeded below. Force offline
# loads so no runtime download is attempted.
export FASTEMBED_CACHE_PATH="${FASTEMBED_CACHE_PATH:-/tmp/cuga/fastembed}"
export HF_HOME="${HF_HOME:-/tmp/cuga/hf}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"

mkdir -p "$CUGA_DBS_DIR" "$CUGA_LOGGING_DIR" "$CUGA_FOLDER" "$FASTEMBED_CACHE_PATH" "$HF_HOME" /sandbox/cuga_workspace

if [ -d /app/cuga_workspace ] && [ ! -f /sandbox/cuga_workspace/contacts.txt ]; then
  cp -R /app/cuga_workspace/. /sandbox/cuga_workspace/
fi

# Seed the baked embedding model into the writable cache on first start.
if [ -d /app/fastembed-cache ] && [ -z "$(ls -A "$FASTEMBED_CACHE_PATH" 2>/dev/null)" ]; then
  cp -R /app/fastembed-cache/. "$FASTEMBED_CACHE_PATH"/
fi

cd /sandbox

exec /app/.venv/bin/cuga start demo_crm \
  --host "${CUGA_HOST:-127.0.0.1}" \
  --read-only \
  --no-email \
  --cuga-workspace /sandbox/cuga_workspace
