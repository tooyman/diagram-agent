"""Targeted edge-through-node repair.

ELK occasionally routes an edge straight through a node it isn't connected to — the
single ugliest defect in an otherwise-good layout. The old response was to retry the
whole layout with bigger spacing, which spreads everything out and wastes space.

This pass is smarter: it finds the specific offending segment and reroutes *just that
segment* around the obstacle, adding a small orthogonal detour. A detour may introduce
an edge crossing, which is fine — the validator tolerates crossings up to a threshold,
so we "spend" from that quota rather than forcing a global spread. Edges that can't be
fixed within the crossing budget are left untouched (they remain hard failures and fall
through to the existing retry ladder).

Everything operates on the already-laid-out ELK result in absolute coordinates, then
writes the new polyline back into each edge section in its container-relative space.
"""

from __future__ import annotations

from .schema import Diagram
from .validator import (
    Rect,
    count_crossings,
    segment_intersects_rect,
    walk_edges,
    walk_node_rects,
)

Point = tuple[float, float]

DEFAULT_GAP = 14.0  # clearance kept between a detour and the obstacle it routes around
_MAX_DETOURS_PER_SECTION = 8  # guard against pathological loops


def _section_polyline_abs(section: dict, cx: float, cy: float) -> list[Point]:
    sp = section["startPoint"]
    ep = section["endPoint"]
    bends = section.get("bendPoints", [])
    pts: list[Point] = [(sp["x"] + cx, sp["y"] + cy)]
    pts.extend((b["x"] + cx, b["y"] + cy) for b in bends)
    pts.append((ep["x"] + cx, ep["y"] + cy))
    return pts


def _write_section_polyline(section: dict, pts: list[Point], cx: float, cy: float) -> None:
    section["startPoint"] = {"x": pts[0][0] - cx, "y": pts[0][1] - cy}
    section["endPoint"] = {"x": pts[-1][0] - cx, "y": pts[-1][1] - cy}
    section["bendPoints"] = [{"x": x - cx, "y": y - cy} for (x, y) in pts[1:-1]]


def _simplify(pts: list[Point]) -> list[Point]:
    """Drop duplicate and collinear interior points so the path stays clean."""
    out: list[Point] = []
    for p in pts:
        if out and abs(out[-1][0] - p[0]) < 1e-6 and abs(out[-1][1] - p[1]) < 1e-6:
            continue
        out.append(p)
    i = 1
    while i < len(out) - 1:
        (x0, y0), (x1, y1), (x2, y2) = out[i - 1], out[i], out[i + 1]
        collinear = (abs(x0 - x1) < 1e-6 and abs(x1 - x2) < 1e-6) or (
            abs(y0 - y1) < 1e-6 and abs(y1 - y2) < 1e-6
        )
        if collinear:
            del out[i]
        else:
            i += 1
    return out


def _pierced_nodes(
    pts: list[Point],
    node_rects: list[tuple[str, Rect]],
    endpoints: set[str],
) -> set[str]:
    """IDs of non-endpoint nodes any segment of this polyline passes through."""
    hits: set[str] = set()
    for i in range(len(pts) - 1):
        seg = (pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        for nid, nrect in node_rects:
            if nid in endpoints:
                continue
            if segment_intersects_rect(seg, nrect, tol=1.0):
                hits.add(nid)
    return hits


def _first_offending_segment(
    pts: list[Point],
    node_rects: list[tuple[str, Rect]],
    endpoints: set[str],
) -> tuple[int, Rect] | None:
    """Index of the first segment that pierces a non-endpoint node, with that rect."""
    for i in range(len(pts) - 1):
        seg = (pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        for nid, nrect in node_rects:
            if nid in endpoints:
                continue
            if segment_intersects_rect(seg, nrect, tol=1.0):
                return i, nrect
    return None


def _detour_candidates(
    pts: list[Point], k: int, rect: Rect, gap: float
) -> list[list[Point]]:
    """Two candidate polylines that route segment (k,k+1) around `rect`.

    Horizontal segment -> detour above / below; vertical -> left / right. Each adds a
    rectangular bump hugging the obstacle with `gap` clearance.
    """
    x1, y1 = pts[k]
    x2, y2 = pts[k + 1]
    rx, ry, rw, rh = rect
    out: list[list[Point]] = []

    if abs(y1 - y2) < 1e-6:  # horizontal
        y = y1
        lo, hi = min(x1, x2), max(x1, x2)
        xa = max(lo, rx - gap)
        xb = min(hi, rx + rw + gap)
        if xa < xb:
            for ylevel in (ry - gap, ry + rh + gap):
                mid = [(xa, y), (xa, ylevel), (xb, ylevel), (xb, y)]
                out.append(pts[: k + 1] + mid + pts[k + 1 :])
    elif abs(x1 - x2) < 1e-6:  # vertical
        x = x1
        lo, hi = min(y1, y2), max(y1, y2)
        ya = max(lo, ry - gap)
        yb = min(hi, ry + rh + gap)
        if ya < yb:
            for xlevel in (rx - gap, rx + rw + gap):
                mid = [(x, ya), (xlevel, ya), (xlevel, yb), (x, yb)]
                out.append(pts[: k + 1] + mid + pts[k + 1 :])
    return out


def _choose_candidate(
    candidates: list[list[Point]],
    section: dict,
    cx: float,
    cy: float,
    elk_result: dict,
    node_rects: list[tuple[str, Rect]],
    endpoints: set[str],
    budget: int,
    prev_pierced_count: int,
) -> list[Point] | None:
    """Pick the detour that removes the obstacle for the fewest added crossings.

    A candidate is valid only if it pierces strictly fewer nodes than before (progress)
    and keeps the whole graph's crossing count within `budget`. Scoring temporarily
    writes the candidate into the section so crossings are measured on the real graph,
    then restores the original before returning.
    """
    orig_sp = section["startPoint"]
    orig_ep = section["endPoint"]
    orig_bp = section.get("bendPoints", [])

    best: list[Point] | None = None
    best_key: tuple[int, int] | None = None
    for cand in candidates:
        cand_s = _simplify(cand)
        pierced = _pierced_nodes(cand_s, node_rects, endpoints)
        if len(pierced) >= prev_pierced_count:
            continue  # no progress
        _write_section_polyline(section, cand_s, cx, cy)
        total = count_crossings(elk_result)
        if total <= budget:
            key = (len(pierced), total)
            if best_key is None or key < best_key:
                best, best_key = cand_s, key

    section["startPoint"] = orig_sp
    section["endPoint"] = orig_ep
    section["bendPoints"] = orig_bp
    return best


def repair_edges(
    elk_result: dict,
    diagram: Diagram,
    *,
    crossing_budget: int = 10,
    gap: float = DEFAULT_GAP,
) -> tuple[dict, int, int]:
    """Reroute edges that pass through non-endpoint nodes.

    Mutates `elk_result` in place and returns (elk_result, n_fixed, n_unfixable) where
    n_fixed counts individual detours applied and n_unfixable counts obstacles that
    could not be cleared within `crossing_budget`.
    """
    comp_ids = {c.id for c in diagram.components}
    node_rects = walk_node_rects(elk_result, comp_ids)

    n_fixed = 0
    n_unfixable = 0

    for edge, cx, cy in walk_edges(elk_result):
        endpoints = set(edge.get("sources", [])) | set(edge.get("targets", []))
        for section in edge.get("sections", []):
            for _ in range(_MAX_DETOURS_PER_SECTION):
                pts = _section_polyline_abs(section, cx, cy)
                hit = _first_offending_segment(pts, node_rects, endpoints)
                if hit is None:
                    break
                k, rect = hit
                prev_pierced = len(_pierced_nodes(pts, node_rects, endpoints))
                candidates = _detour_candidates(pts, k, rect, gap)
                best = _choose_candidate(
                    candidates, section, cx, cy, elk_result,
                    node_rects, endpoints, crossing_budget, prev_pierced,
                )
                if best is None:
                    n_unfixable += 1
                    break
                _write_section_polyline(section, best, cx, cy)
                n_fixed += 1

    return elk_result, n_fixed, n_unfixable
