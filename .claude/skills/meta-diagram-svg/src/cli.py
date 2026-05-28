from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .layout import run_layout
from .render import render_html, render_svg
from .schema import Diagram
from .transformer import default_layout_opts, metadata_to_elk
from .validator import has_hard_failures, validate_geometry


RETRY_STRATEGIES: list[dict[str, str]] = [
    # Each step bumps spacing / changes strategy. Tried in order on hard failures.
    {"elk.spacing.nodeNode": "55", "elk.layered.spacing.nodeNodeBetweenLayers": "90"},
    {"elk.spacing.nodeNode": "70", "elk.layered.spacing.nodeNodeBetweenLayers": "110",
     "elk.spacing.edgeNode": "35"},
    {"elk.layered.nodePlacement.strategy": "BRANDES_KOEPF",
     "elk.spacing.nodeNode": "70", "elk.layered.spacing.nodeNodeBetweenLayers": "110"},
    {"elk.direction": "DOWN", "elk.spacing.nodeNode": "60",
     "elk.layered.spacing.nodeNodeBetweenLayers": "90"},
    {"elk.spacing.nodeNode": "100", "elk.layered.spacing.nodeNodeBetweenLayers": "140",
     "elk.spacing.edgeNode": "40", "elk.spacing.edgeEdge": "25"},
]


def run_with_retries(diagram: Diagram, *, max_retries: int = 5, verbose: bool = True):
    base_opts = default_layout_opts()
    best_result = None
    best_issues: list = []

    for attempt in range(max_retries + 1):
        opts = dict(base_opts)
        if attempt > 0:
            opts.update(RETRY_STRATEGIES[min(attempt - 1, len(RETRY_STRATEGIES) - 1)])
        if verbose:
            print(f"  attempt {attempt}: {_summarize_opts(opts)}")
        elk_graph = metadata_to_elk(diagram, opts)
        result = run_layout(elk_graph)
        issues = validate_geometry(result, diagram)
        hard = has_hard_failures(issues)
        if verbose:
            print(f"    → {len(issues)} issue(s), hard_fail={hard}")
            for issue in issues[:8]:
                print(f"       {issue}")
            if len(issues) > 8:
                print(f"       (+{len(issues) - 8} more)")
        if best_result is None or len(issues) < len(best_issues):
            best_result, best_issues = result, issues
        if not hard:
            return result, issues
    return best_result, best_issues


def _summarize_opts(opts: dict[str, str]) -> str:
    keys = ("elk.direction", "elk.spacing.nodeNode",
            "elk.layered.spacing.nodeNodeBetweenLayers",
            "elk.layered.nodePlacement.strategy")
    return " ".join(f"{k.split('.')[-1]}={opts[k]}" for k in keys if k in opts)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="diagram-agent")
    p.add_argument("input", help="Input YAML metadata file")
    p.add_argument("-o", "--output", default="output/diagram.svg", help="SVG output path")
    p.add_argument("--no-retry", action="store_true",
                   help="Run layout once; skip validator-driven retries")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    diagram = Diagram.from_yaml(args.input)
    if not args.quiet:
        print(
            f"Loaded: {len(diagram.components)} components, "
            f"{len(diagram.groups)} groups, "
            f"{len(diagram.connections)} connections"
        )

    if args.no_retry:
        elk_graph = metadata_to_elk(diagram)
        result = run_layout(elk_graph)
        issues = validate_geometry(result, diagram)
    else:
        result, issues = run_with_retries(diagram, verbose=not args.quiet)

    svg = render_svg(result, diagram)
    out = Path(args.output)
    out.parent.mkdir(exist_ok=True, parents=True)
    out.write_text(svg)
    html_out = out.with_suffix(".html")
    html_out.write_text(render_html(svg, diagram.title))
    if not args.quiet:
        print(f"Wrote {out}")
        print(f"Wrote {html_out}  (open in browser for pan/zoom)")
        print(f"Final: {len(issues)} issue(s)")
        for issue in issues:
            print(f"  {issue}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
