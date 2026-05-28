from __future__ import annotations

import json
import subprocess
from pathlib import Path

ELK_HELPER = Path(__file__).resolve().parent.parent / "elk_helper" / "layout.js"


def run_layout(elk_graph: dict) -> dict:
    if not ELK_HELPER.exists():
        raise FileNotFoundError(f"ELK helper not found at {ELK_HELPER}")
    result = subprocess.run(
        ["node", str(ELK_HELPER)],
        input=json.dumps(elk_graph),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ELK layout failed: {result.stderr}")
    return json.loads(result.stdout)
