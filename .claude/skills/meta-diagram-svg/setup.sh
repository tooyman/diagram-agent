#!/usr/bin/env bash
# One-shot setup for meta-diagram-svg: Python venv + npm deps.
# Safe to re-run; only installs what's missing.
set -euo pipefail

SKILL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SKILL_DIR"

# --- Python venv ---
if [[ ! -d .venv ]]; then
  echo "[setup] Creating Python venv at .venv"
  python3 -m venv .venv
fi
echo "[setup] Installing Python deps"
.venv/bin/pip install --quiet --upgrade pip >/dev/null 2>&1 || true
.venv/bin/pip install --quiet -r requirements.txt

# --- Node deps for ELK helper ---
if ! command -v node >/dev/null 2>&1; then
  echo "[setup] ERROR: node is not on PATH. Install Node.js first (e.g. 'brew install node')."
  exit 1
fi

if [[ ! -d elk_helper/node_modules ]]; then
  echo "[setup] Installing elkjs"
  (cd elk_helper && npm install --silent)
else
  echo "[setup] elkjs already installed"
fi

echo "[setup] Done. Try:  $SKILL_DIR/run.sh examples/simple.yaml -o output/simple.svg"
