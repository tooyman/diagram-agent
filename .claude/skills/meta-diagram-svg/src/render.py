from __future__ import annotations

from html import escape as _escape
from typing import Iterable

from .schema import (
    Component,
    ComponentType,
    Connection,
    Diagram,
    Group,
    LifecycleStatus,
    ProtocolKind,
)
from .textlayout import (
    EDGE_LABEL_FONT,
    GROUP_LABEL_FONT,
    LINE_HEIGHT_MULT,
    TITLE_FONT,
    compute_node_layout,
)

COLORS = {
    "bg": "#FAFBFC",
    "node_stroke": "#1F2937",
    "label": "#111827",
    "group_stroke": "#9CA3AF",
    "group_label": "#4B5563",
    "edge_sync": "#1F2937",
    "edge_async": "#1F2937",
    "edge_data": "#2563EB",
    "fill_unchanged": "#FFFFFF",
    "fill_updated": "#FEF3C7",
    "fill_new": "#FCE7F3",
    "fill_core_engine": "#DBEAFE",
    "group_fill": "#F8FAFC",
}
FONT = "Inter, system-ui, -apple-system, sans-serif"
STROKE_W = 1.5
NODE_RADIUS = 6


def escape(s: str) -> str:
    return _escape(s, quote=True)


def lifecycle_fill(c: Component) -> str:
    if c.type == ComponentType.core_engine:
        return COLORS["fill_core_engine"]
    return {
        LifecycleStatus.new: COLORS["fill_new"],
        LifecycleStatus.updated: COLORS["fill_updated"],
        LifecycleStatus.unchanged: COLORS["fill_unchanged"],
    }[c.lifecycle_status]


def edge_color(kind: ProtocolKind) -> str:
    return {
        ProtocolKind.sync: COLORS["edge_sync"],
        ProtocolKind.async_: COLORS["edge_async"],
        ProtocolKind.data: COLORS["edge_data"],
    }[kind]


def build_abs_positions(elk: dict) -> dict[str, tuple[float, float]]:
    """Map every node id (including the root) to its absolute (x, y)."""
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


def walk_nodes(elk: dict, comp_ids: set[str], group_ids: set[str]):
    """Yield (kind, id, abs_x, abs_y, w, h, raw_node) for groups and components."""
    def rec(node: dict, ax: float, ay: float):
        for child in node.get("children", []):
            cx = ax + child.get("x", 0)
            cy = ay + child.get("y", 0)
            cw = child.get("width", 0)
            ch = child.get("height", 0)
            if child["id"] in group_ids:
                yield ("group", child["id"], cx, cy, cw, ch, child)
                yield from rec(child, cx, cy)
            elif child["id"] in comp_ids:
                yield ("component", child["id"], cx, cy, cw, ch, child)
    yield from rec(elk, 0, 0)


def walk_edges(elk: dict, abs_pos: dict[str, tuple[float, float]] | None = None):
    """Yield (edge, offset_x, offset_y).

    ELK stores all edges at the root array but tags each with a `container` field
    (the LCA of its endpoints). Edge coordinates are relative to that container.
    """
    if abs_pos is None:
        abs_pos = build_abs_positions(elk)

    def rec(node: dict):
        for e in node.get("edges", []):
            container = e.get("container")
            if container and container in abs_pos:
                cx, cy = abs_pos[container]
            else:
                cx, cy = 0.0, 0.0
            yield (e, cx, cy)
        for child in node.get("children", []):
            yield from rec(child)

    yield from rec(elk)


def render_svg(elk_result: dict, diagram: Diagram) -> str:
    comp_by_id: dict[str, Component] = {c.id: c for c in diagram.components}
    group_by_id: dict[str, Group] = {g.id: g for g in diagram.groups}
    conn_by_idx: dict[int, Connection] = {i: c for i, c in enumerate(diagram.connections)}

    canvas_w = elk_result.get("width", 1000)
    canvas_h = elk_result.get("height", 800)
    margin = 28
    title_h = 50

    out: list[str] = []
    # No fixed width/height — only viewBox. This makes the SVG scale to the
    # container in browsers (and HTML viewers), enabling zoom-by-resize.
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {canvas_w + margin*2} {canvas_h + margin*2 + title_h}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'font-family="{FONT}">'
    )
    out.append(f'<rect width="100%" height="100%" fill="{COLORS["bg"]}"/>')
    out.append(_defs())
    out.append(
        f'<text x="{margin}" y="{margin + TITLE_FONT + 4}" font-size="{TITLE_FONT}" '
        f'font-weight="700" fill="{COLORS["label"]}">{escape(diagram.title)}</text>'
    )
    out.append(f'<g transform="translate({margin},{margin + title_h})">')

    # Collect into render order: groups first (outer→inner), then edges, then components, then edge labels.
    nodes = list(walk_nodes(elk_result, set(comp_by_id), set(group_by_id)))
    groups = [n for n in nodes if n[0] == "group"]
    comps = [n for n in nodes if n[0] == "component"]

    # Render groups (outer first — they appear first in the walk because we yield then recurse).
    for _, gid, x, y, w, h, _ in groups:
        out.append(_render_group(group_by_id[gid], x, y, w, h))

    # Render edges (under nodes so arrowheads don't poke out from on top).
    edges = list(walk_edges(elk_result))
    for edge, cx, cy in edges:
        idx = int(edge["id"][1:])
        conn = conn_by_idx[idx]
        out.append(_render_edge_path(edge, cx, cy, conn))

    # Render components.
    for _, cid, x, y, w, h, _ in comps:
        out.append(_render_component(comp_by_id[cid], x, y, w, h))

    # Render edge labels on top (so the white background isn't hidden by lines).
    for edge, cx, cy in edges:
        idx = int(edge["id"][1:])
        conn = conn_by_idx[idx]
        out.append(_render_edge_label(edge, cx, cy, conn))

    out.append('</g></svg>')
    return "\n".join(p for p in out if p)


def render_html(svg: str, title: str) -> str:
    """Wrap an SVG in an HTML page with pan/zoom (mousewheel + drag + buttons)."""
    return _HTML_TEMPLATE.replace("__TITLE__", escape(title)).replace("__SVG__", svg)


_HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>__TITLE__</title>
<style>
html,body{margin:0;height:100%;overflow:hidden;background:#FAFBFC;font:13px system-ui,-apple-system,sans-serif}
#wrap{width:100vw;height:100vh;cursor:grab;overflow:hidden;position:relative}
#wrap.grab{cursor:grabbing}
#wrap svg{display:block;transform-origin:0 0;will-change:transform;user-select:none}
#tb{position:fixed;top:10px;right:10px;background:#fff;border:1px solid #e5e7eb;border-radius:6px;padding:4px 6px;box-shadow:0 1px 3px rgba(0,0,0,.08);display:flex;align-items:center}
#tb button{border:0;background:#f3f4f6;padding:5px 10px;margin:0 1px;cursor:pointer;border-radius:3px;font:13px system-ui}
#tb button:hover{background:#e5e7eb}
#zlbl{margin:0 10px;color:#6b7280;min-width:42px;text-align:center}
.hint{position:fixed;bottom:10px;left:10px;color:#9ca3af;font-size:11px;user-select:none}
</style></head><body>
<div id="wrap">__SVG__</div>
<div id="tb"><button onclick="zoomAt(1.25)">+</button><button onclick="zoomAt(0.8)">&minus;</button><span id="zlbl">100%</span><button onclick="reset()">Fit</button></div>
<div class="hint">scroll to zoom &middot; drag to pan</div>
<script>
const wrap=document.getElementById('wrap'),svg=wrap.querySelector('svg');
let s=1,tx=0,ty=0;
function apply(){svg.style.transform=`translate(${tx}px,${ty}px) scale(${s})`;document.getElementById('zlbl').textContent=Math.round(s*100)+'%';}
function reset(){const r=wrap.getBoundingClientRect(),v=svg.viewBox.baseVal;s=Math.min(r.width/v.width,r.height/v.height)*0.96;tx=(r.width-v.width*s)/2;ty=(r.height-v.height*s)/2;apply();}
function zoomAt(f,cx,cy){if(cx===undefined){const r=wrap.getBoundingClientRect();cx=r.width/2;cy=r.height/2;}tx=cx-(cx-tx)*f;ty=cy-(cy-ty)*f;s*=f;apply();}
wrap.addEventListener('wheel',e=>{e.preventDefault();zoomAt(Math.pow(1.0015,-e.deltaY),e.clientX,e.clientY);},{passive:false});
let drag=null;
wrap.addEventListener('mousedown',e=>{drag={x:e.clientX-tx,y:e.clientY-ty};wrap.classList.add('grab');});
window.addEventListener('mouseup',()=>{drag=null;wrap.classList.remove('grab');});
window.addEventListener('mousemove',e=>{if(drag){tx=e.clientX-drag.x;ty=e.clientY-drag.y;apply();}});
window.addEventListener('keydown',e=>{if(e.key==='0'&&(e.metaKey||e.ctrlKey)){e.preventDefault();reset();}});
const v=svg.viewBox.baseVal;svg.style.width=v.width+'px';svg.style.height=v.height+'px';
reset();
window.addEventListener('resize',reset);
</script>
</body></html>
"""


def _defs() -> str:
    markers = []
    for kind in ("sync", "async", "data"):
        color = edge_color(ProtocolKind(kind))
        markers.append(
            f'<marker id="arrow-{kind}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>'
        )
    return "<defs>" + "".join(markers) + "</defs>"


def _render_group(g: Group, x: float, y: float, w: float, h: float) -> str:
    return (
        f'<g>'
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="10" '
        f'fill="{COLORS["group_fill"]}" stroke="{COLORS["group_stroke"]}" '
        f'stroke-width="{STROKE_W}" stroke-dasharray="6,4"/>'
        f'<text x="{x + 16:.1f}" y="{y + GROUP_LABEL_FONT + 8:.1f}" '
        f'font-size="{GROUP_LABEL_FONT}" font-weight="700" '
        f'fill="{COLORS["group_label"]}">{escape(g.name)}</text>'
        f'</g>'
    )


def _render_edge_path(edge: dict, cx: float, cy: float, conn: Connection) -> str:
    sections = edge.get("sections", [])
    if not sections:
        return ""
    color = edge_color(conn.protocol_kind)
    dash = ' stroke-dasharray="6,4"' if conn.protocol_kind == ProtocolKind.async_ else ""

    path_parts: list[str] = []
    for section in sections:
        sp = section["startPoint"]
        ep = section["endPoint"]
        bends = section.get("bendPoints", [])
        pts = [(sp["x"] + cx, sp["y"] + cy)]
        pts.extend((b["x"] + cx, b["y"] + cy) for b in bends)
        pts.append((ep["x"] + cx, ep["y"] + cy))
        d = "M " + " L ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        path_parts.append(d)

    d = " ".join(path_parts)
    marker = f'arrow-{conn.protocol_kind.value}'
    return (
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{STROKE_W}"{dash} '
        f'marker-end="url(#{marker})"/>'
    )


def _render_edge_label(edge: dict, cx: float, cy: float, conn: Connection) -> str:
    if not conn.protocol:
        return ""
    labels = edge.get("labels", [])
    if not labels:
        return ""
    label = labels[0]
    lx = label.get("x", 0) + cx
    ly = label.get("y", 0) + cy
    lw = label.get("width", 40)
    lh = label.get("height", 16)
    text = escape(conn.protocol)
    pad = 3
    return (
        f'<g>'
        f'<rect x="{lx-pad:.1f}" y="{ly-pad:.1f}" width="{lw+pad*2:.1f}" height="{lh+pad*2:.1f}" '
        f'fill="#FFFFFF" fill-opacity="0.95" rx="3"/>'
        f'<text x="{lx + lw/2:.1f}" y="{ly + lh - 3:.1f}" text-anchor="middle" '
        f'font-size="{EDGE_LABEL_FONT}" fill="{COLORS["label"]}">{text}</text>'
        f'</g>'
    )


def _label_tspans(
    lines: list[str],
    cx: float,
    cy: float,
    font: int,
    weight: str = "400",
    color: str | None = None,
) -> str:
    """Multi-line label vertically centered on (cx, cy)."""
    n = len(lines)
    line_h = font * LINE_HEIGHT_MULT
    # Baseline of the first line. Vertically center the block on cy.
    first_baseline = cy + font * 0.34 - (n - 1) * line_h / 2
    spans = "".join(
        f'<tspan x="{cx:.1f}" y="{first_baseline + i * line_h:.1f}">{escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    fill = color or COLORS["label"]
    return (
        f'<text text-anchor="middle" font-size="{font}" '
        f'font-weight="{weight}" fill="{fill}">{spans}</text>'
    )


def _render_component(c: Component, x: float, y: float, w: float, h: float) -> str:
    fill = lifecycle_fill(c)
    cx, cy = x + w / 2, y + h / 2
    stroke = COLORS["node_stroke"]
    _, _, lines, font, weight = compute_node_layout(c.name, c.type)

    if c.type == ComponentType.datastore:
        ry = 9
        # Label center is shifted down to clear the elliptical lid.
        label_cy = y + (h + ry) / 2 + 2
        return (
            f'<g>'
            f'<path d="M {x:.1f},{y+ry:.1f} A {w/2:.1f},{ry} 0 0 0 {x+w:.1f},{y+ry:.1f} '
            f'L {x+w:.1f},{y+h-ry:.1f} A {w/2:.1f},{ry} 0 0 1 {x:.1f},{y+h-ry:.1f} Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{STROKE_W}"/>'
            f'<ellipse cx="{cx:.1f}" cy="{y+ry:.1f}" rx="{w/2:.1f}" ry="{ry}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{STROKE_W}"/>'
            f'{_label_tspans(lines, cx, label_cy, font, weight)}'
            f'</g>'
        )

    if c.type == ComponentType.queue:
        divs = 3
        dividers = "".join(
            f'<line x1="{x + w*i/divs:.1f}" y1="{y:.1f}" x2="{x + w*i/divs:.1f}" '
            f'y2="{y+h:.1f}" stroke="{stroke}" stroke-width="1"/>'
            for i in range(1, divs)
        )
        return (
            f'<g>'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="3" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{STROKE_W}"/>'
            f'{dividers}'
            f'{_label_tspans(lines, cx, cy, font, weight)}'
            f'</g>'
        )

    if c.type == ComponentType.external_partner:
        return (
            f'<g>'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{NODE_RADIUS}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{STROKE_W}"/>'
            f'<rect x="{x+3:.1f}" y="{y+3:.1f}" width="{w-6:.1f}" height="{h-6:.1f}" '
            f'rx="{NODE_RADIUS-2}" fill="none" stroke="{stroke}" stroke-width="1"/>'
            f'{_label_tspans(lines, cx, cy, font, weight)}'
            f'</g>'
        )

    if c.type == ComponentType.actor:
        hx = x + w / 2
        hy = y + 16
        figure_bottom = hy + 46
        # Label sits below the figure, centered in the remaining space.
        label_cy = (figure_bottom + (y + h)) / 2
        return (
            f'<g>'
            f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="9" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{STROKE_W}"/>'
            f'<line x1="{hx:.1f}" y1="{hy+9:.1f}" x2="{hx:.1f}" y2="{hy+30:.1f}" '
            f'stroke="{stroke}" stroke-width="{STROKE_W}"/>'
            f'<line x1="{hx-11:.1f}" y1="{hy+17:.1f}" x2="{hx+11:.1f}" y2="{hy+17:.1f}" '
            f'stroke="{stroke}" stroke-width="{STROKE_W}"/>'
            f'<line x1="{hx:.1f}" y1="{hy+30:.1f}" x2="{hx-9:.1f}" y2="{hy+46:.1f}" '
            f'stroke="{stroke}" stroke-width="{STROKE_W}"/>'
            f'<line x1="{hx:.1f}" y1="{hy+30:.1f}" x2="{hx+9:.1f}" y2="{hy+46:.1f}" '
            f'stroke="{stroke}" stroke-width="{STROKE_W}"/>'
            f'{_label_tspans(lines, hx, label_cy, font, weight)}'
            f'</g>'
        )

    if c.type == ComponentType.mainframe:
        fold = 12
        return (
            f'<g>'
            f'<path d="M {x:.1f},{y:.1f} L {x+w-fold:.1f},{y:.1f} L {x+w:.1f},{y+fold:.1f} '
            f'L {x+w:.1f},{y+h:.1f} L {x:.1f},{y+h:.1f} Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{STROKE_W}"/>'
            f'<path d="M {x+w-fold:.1f},{y:.1f} L {x+w-fold:.1f},{y+fold:.1f} '
            f'L {x+w:.1f},{y+fold:.1f}" fill="none" stroke="{stroke}" stroke-width="1"/>'
            f'{_label_tspans(lines, cx, cy, font, weight)}'
            f'</g>'
        )

    if c.type == ComponentType.core_engine:
        return (
            f'<g>'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{NODE_RADIUS}" '
            f'fill="{COLORS["fill_core_engine"]}" stroke="{stroke}" stroke-width="2"/>'
            f'{_label_tspans(lines, cx, cy, font, weight)}'
            f'</g>'
        )

    if c.type == ComponentType.gateway:
        chev = 12
        return (
            f'<g>'
            f'<path d="M {x+chev:.1f},{y:.1f} L {x+w-chev:.1f},{y:.1f} L {x+w:.1f},{cy:.1f} '
            f'L {x+w-chev:.1f},{y+h:.1f} L {x+chev:.1f},{y+h:.1f} L {x:.1f},{cy:.1f} Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{STROKE_W}"/>'
            f'{_label_tspans(lines, cx, cy, font, weight)}'
            f'</g>'
        )

    # server / channel / default → rounded rectangle
    return (
        f'<g>'
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{NODE_RADIUS}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{STROKE_W}"/>'
        f'{_label_tspans(lines, cx, cy, font, weight)}'
        f'</g>'
    )
