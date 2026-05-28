from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .schema import Diagram

Rect = tuple[float, float, float, float]  # x, y, w, h
Segment = tuple[float, float, float, float]  # x1, y1, x2, y2


@dataclass
class Issue:
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


def _walk_node_rects(elk: dict, comp_ids: set[str]) -> list[tuple[str, Rect]]:
    out: list[tuple[str, Rect]] = []

    def rec(node: dict, ax: float, ay: float) -> None:
        for child in node.get("children", []):
            cx = ax + child.get("x", 0)
            cy = ay + child.get("y", 0)
            cw = child.get("width", 0)
            ch = child.get("height", 0)
            if child["id"] in comp_ids:
                out.append((child["id"], (cx, cy, cw, ch)))
            rec(child, cx, cy)

    rec(elk, 0, 0)
    return out


def _walk_group_rects(elk: dict, group_ids: set[str]) -> list[tuple[str, Rect, list[str]]]:
    """Return groups with their child component IDs (direct + nested)."""
    out: list[tuple[str, Rect, list[str]]] = []

    def collect_descendants(node: dict) -> list[str]:
        ids: list[str] = []
        for child in node.get("children", []):
            ids.append(child["id"])
            ids.extend(collect_descendants(child))
        return ids

    def rec(node: dict, ax: float, ay: float) -> None:
        for child in node.get("children", []):
            cx = ax + child.get("x", 0)
            cy = ay + child.get("y", 0)
            cw = child.get("width", 0)
            ch = child.get("height", 0)
            if child["id"] in group_ids:
                out.append((child["id"], (cx, cy, cw, ch), collect_descendants(child)))
            rec(child, cx, cy)

    rec(elk, 0, 0)
    return out


def _build_abs_positions(elk: dict) -> dict[str, tuple[float, float]]:
    pos: dict[str, tuple[float, float]] = {}
    if "id" in elk:
        pos[elk["id"]] = (elk.get("x", 0), elk.get("y", 0))

    def rec(node: dict, ax: float, ay: float) -> None:
        for child in node.get("children", []):
            cx = ax + child.get("x", 0)
            cy = ay + child.get("y", 0)
            pos[child["id"]] = (cx, cy)
            rec(child, cx, cy)

    rec(elk, 0, 0)
    return pos


def _walk_edges(elk: dict) -> list[tuple[dict, float, float]]:
    abs_pos = _build_abs_positions(elk)
    out: list[tuple[dict, float, float]] = []

    def rec(node: dict) -> None:
        for e in node.get("edges", []):
            container = e.get("container")
            if container and container in abs_pos:
                cx, cy = abs_pos[container]
            else:
                cx, cy = 0.0, 0.0
            out.append((e, cx, cy))
        for child in node.get("children", []):
            rec(child)

    rec(elk)
    return out


def _rects_overlap(a: Rect, b: Rect, tol: float = -0.5) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (
        ax + aw <= bx - tol
        or bx + bw <= ax - tol
        or ay + ah <= by - tol
        or by + bh <= ay - tol
    )


def _segment_intersects_rect(seg: Segment, rect: Rect, tol: float = 0.5) -> bool:
    x1, y1, x2, y2 = seg
    rx, ry, rw, rh = rect
    # Inflate rect slightly to avoid touch-only false positives
    rx += tol
    ry += tol
    rw -= 2 * tol
    rh -= 2 * tol
    if rw <= 0 or rh <= 0:
        return False
    # Quick reject
    if max(x1, x2) < rx or min(x1, x2) > rx + rw:
        return False
    if max(y1, y2) < ry or min(y1, y2) > ry + rh:
        return False
    # Orthogonal-only: segment is either horizontal or vertical (ELK ORTHOGONAL).
    if abs(x1 - x2) < 1e-6:  # vertical
        if rx < x1 < rx + rw and not (max(y1, y2) <= ry or min(y1, y2) >= ry + rh):
            return True
    elif abs(y1 - y2) < 1e-6:  # horizontal
        if ry < y1 < ry + rh and not (max(x1, x2) <= rx or min(x1, x2) >= rx + rw):
            return True
    return False


def _edge_segments(edge: dict, cx: float, cy: float) -> list[tuple[Segment, bool, bool]]:
    """Return [(segment, is_first, is_last), ...] across all sections."""
    segs: list[tuple[Segment, bool, bool]] = []
    sections = edge.get("sections", [])
    for section in sections:
        sp = section["startPoint"]
        ep = section["endPoint"]
        bends = section.get("bendPoints", [])
        pts = [(sp["x"] + cx, sp["y"] + cy)]
        pts.extend((b["x"] + cx, b["y"] + cy) for b in bends)
        pts.append((ep["x"] + cx, ep["y"] + cy))
        for i in range(len(pts) - 1):
            seg = (pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
            segs.append((seg, i == 0, i == len(pts) - 2))
    return segs


def _segments_cross(a: Segment, b: Segment) -> bool:
    """Detect orthogonal segment crossing (one horizontal, one vertical, intersecting strictly inside both)."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    a_horiz = abs(ay1 - ay2) < 1e-6
    b_horiz = abs(by1 - by2) < 1e-6
    if a_horiz == b_horiz:
        return False  # parallel — overlap handled separately
    if a_horiz:
        hx1, hx2 = min(ax1, ax2), max(ax1, ax2)
        hy = ay1
        vy1, vy2 = min(by1, by2), max(by1, by2)
        vx = bx1
    else:
        hx1, hx2 = min(bx1, bx2), max(bx1, bx2)
        hy = by1
        vy1, vy2 = min(ay1, ay2), max(ay1, ay2)
        vx = ax1
    return hx1 < vx < hx2 and vy1 < hy < vy2


def validate_geometry(
    elk_result: dict,
    diagram: Diagram,
    *,
    crossings_warn: int = 10,
    crossings_fail: int = 30,
) -> list[Issue]:
    comp_ids = {c.id for c in diagram.components}
    group_ids = {g.id for g in diagram.groups}

    node_rects = _walk_node_rects(elk_result, comp_ids)
    group_rects = _walk_group_rects(elk_result, group_ids)
    edges = _walk_edges(elk_result)

    issues: list[Issue] = []

    # Node-node overlap
    for i, (id1, r1) in enumerate(node_rects):
        for id2, r2 in node_rects[i + 1 :]:
            if _rects_overlap(r1, r2, tol=-1.0):
                issues.append(Issue("node_overlap", f"{id1} ↔ {id2}"))

    # Group overflow: component outside its declared group
    rect_by_comp = dict(node_rects)
    for gid, grect, child_ids in group_rects:
        gx, gy, gw, gh = grect
        for cid in child_ids:
            if cid not in rect_by_comp:
                continue
            cx, cy, cw, ch = rect_by_comp[cid]
            if cx < gx - 1 or cy < gy - 1 or cx + cw > gx + gw + 1 or cy + ch > gy + gh + 1:
                issues.append(Issue("group_overflow", f"{cid} extends outside {gid}"))

    # Edge-through-node (excluding endpoints)
    for edge, cx, cy in edges:
        endpoints = set(edge.get("sources", [])) | set(edge.get("targets", []))
        for seg, _, _ in _edge_segments(edge, cx, cy):
            for nid, nrect in node_rects:
                if nid in endpoints:
                    continue
                if _segment_intersects_rect(seg, nrect, tol=1.0):
                    issues.append(
                        Issue("edge_through_node", f"edge {edge['id']} crosses {nid}")
                    )
                    break

    # Edge crossings (between non-shared edges)
    all_segs: list[tuple[str, Segment]] = []
    for edge, cx, cy in edges:
        for seg, _, _ in _edge_segments(edge, cx, cy):
            all_segs.append((edge["id"], seg))
    crossings = 0
    for i, (id1, s1) in enumerate(all_segs):
        for id2, s2 in all_segs[i + 1 :]:
            if id1 == id2:
                continue
            if _segments_cross(s1, s2):
                crossings += 1
    if crossings > crossings_fail:
        issues.append(Issue("edge_crossings", f"{crossings} edge crossings (fail > {crossings_fail})"))
    elif crossings > crossings_warn:
        issues.append(Issue("edge_crossings_warn", f"{crossings} edge crossings (warn > {crossings_warn})"))

    # Label collisions (edge label rect vs any node rect)
    for edge, cx, cy in edges:
        for label in edge.get("labels", []):
            lx = label.get("x", 0) + cx
            ly = label.get("y", 0) + cy
            lw = label.get("width", 0)
            lh = label.get("height", 0)
            if lw == 0 or lh == 0:
                continue
            lrect = (lx, ly, lw, lh)
            for nid, nrect in node_rects:
                if _rects_overlap(lrect, nrect, tol=-1.0):
                    issues.append(Issue("label_collision", f"edge {edge['id']} label ↔ {nid}"))
                    break

    # Aspect ratio
    w = elk_result.get("width", 1)
    h = elk_result.get("height", 1)
    ratio = w / h if h else 0
    if ratio < 0.4 or ratio > 3.0:
        issues.append(Issue("aspect_ratio", f"w/h = {ratio:.2f}"))

    return issues


# Severity classification used by the retry loop.
HARD_FAIL_CODES = {"node_overlap", "edge_through_node", "group_overflow", "edge_crossings"}


def has_hard_failures(issues: Iterable[Issue]) -> bool:
    return any(i.code in HARD_FAIL_CODES for i in issues)
