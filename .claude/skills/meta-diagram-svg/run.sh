#!/usr/bin/env bash
# meta-diagram-svg runner.
#
# Resolves to this skill's bundled Python venv and ELK helper, then invokes the
# pipeline. Input/output paths the caller passes are resolved against the
# caller's CWD (PYTHONPATH is set, but CWD is not changed), so relative paths
# like `examples/foo.yaml -o output/foo.svg` work from anywhere.
set -euo pipefail

SKILL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PY="$SKILL_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
  echo "[meta-diagram-svg] First-time setup needed."
  echo "  Run: $SKILL_DIR/setup.sh"
  exit 1
fi

if [[ ! -d "$SKILL_DIR/elk_helper/node_modules" ]]; then
  echo "[meta-diagram-svg] ELK Node deps missing."
  echo "  Run: $SKILL_DIR/setup.sh"
  exit 1
fi

PYTHONPATH="$SKILL_DIR" exec "$VENV_PY" -m src "$@"
