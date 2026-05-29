from __future__ import annotations

from .schema import Component, Diagram, Group, Location
from .textlayout import (
    EDGE_LABEL_FONT,
    GROUP_LABEL_FONT,
    compute_node_layout,
    estimate_text_size,
)

# Tightened padding to reduce whitespace inside group boxes (top leaves room for the
# group label). See default_layout_opts() for the spacing rationale.
GROUP_PADDING = "[top=32,left=16,bottom=16,right=16]"


def default_layout_opts() -> dict[str, str]:
    # INCLUDE_CHILDREN is required: SEPARATE_CHILDREN drops all cross-hierarchy
    # edges from routing (~80% of NLEADS edges are cross-hierarchy). Compaction
    # is achieved via tightened spacing + aspectRatio + post-compaction + thoroughness.
    #
    # Wraparound control (instead of a custom edge-rewriting pass): the two options
    # below let ELK's own engine route backward / hub edges shorter, which both shrinks
    # the canvas and cuts the "perimeter-hugging" detours at the source.
    #   - nodePlacement = BRANDES_KOEPF (ELK's well-tested default; we had overridden
    #     it to NETWORK_SIMPLEX). BK packs layers tighter, so backward edges into a
    #     high-degree hub no longer have to loop around the whole canvas border.
    #   - considerModelOrder = NONE frees crossing-minimization from input authoring
    #     order, letting ELK reorder nodes within a layer to minimize edge length.
    # On the NLEADS hub-and-spoke this drops canvas area ~14% and the worst detour
    # ratio from ~3.8x to ~2.7x with no extra crossings. Both are coarse, whole-graph
    # levers — no per-edge rewriting, so endpoints/arrowheads stay exactly where ELK
    # puts them.
    return {
        "elk.algorithm": "layered",
        "elk.direction": "RIGHT",
        "elk.layered.spacing.nodeNodeBetweenLayers": "40",
        "elk.spacing.nodeNode": "24",
        "elk.spacing.edgeNode": "16",
        "elk.spacing.edgeEdge": "10",
        "elk.spacing.componentComponent": "28",
        "elk.edgeRouting": "ORTHOGONAL",
        "elk.layered.nodePlacement.strategy": "BRANDES_KOEPF",
        "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
        "elk.layered.considerModelOrder.strategy": "NONE",
        "elk.hierarchyHandling": "INCLUDE_CHILDREN",
        "elk.layered.mergeEdges": "false",
        "elk.aspectRatio": "1.6",
        "elk.layered.thoroughness": "30",
        "elk.layered.compaction.postCompaction.strategy": "LEFT_RIGHT_CONSTRAINT_LOCKING",
        "elk.layered.compaction.connectedComponents": "true",
    }


# --- location (compass) hint -> ELK layout options -------------------------------
#
# A compass region splits into two independent levers for a layered (direction=RIGHT)
# graph: horizontal = which layer (column), vertical = order within a layer.

# Horizontal band -> layer constraint. center/north/south get no horizontal force
# (a forced *middle* column isn't expressible in ELK layered without partitioning,
# which would collapse the natural multi-layer flow).
_LOC_LAYER_CONSTRAINT: dict[Location, str] = {
    Location.north_west: "FIRST",
    Location.west: "FIRST",
    Location.south_west: "FIRST",
    Location.north_east: "LAST",
    Location.east: "LAST",
    Location.south_east: "LAST",
}

# Vertical band -> in-layer y-seed (only relative magnitude matters; semiInteractive
# orders nodes that carry a position and leaves the rest free).
_LOC_Y_SEED: dict[Location, int] = {
    Location.north_west: 0, Location.north: 0, Location.north_east: 0,
    Location.west: 10000, Location.center: 10000, Location.east: 10000,
    Location.south_west: 20000, Location.south: 20000, Location.south_east: 20000,
}


def _location_node_opts(loc: Location) -> dict[str, str]:
    """Per-node ELK layoutOptions realizing a compass location hint."""
    opts: dict[str, str] = {}
    constraint = _LOC_LAYER_CONSTRAINT.get(loc)
    if constraint:
        opts["elk.layered.layering.layerConstraint"] = constraint
    y = _LOC_Y_SEED.get(loc)
    if y is not None:
        # x is ignored for placement (NETWORK_SIMPLEX); y drives semiInteractive order.
        opts["elk.position"] = f"(0,{y})"
    return opts


def _has_locations(diagram: Diagram) -> bool:
    return any(g.location for g in diagram.groups) or any(
        c.location for c in diagram.components
    )


def metadata_to_elk(diagram: Diagram, layout_opts: dict[str, str] | None = None) -> dict:
    layout_opts = dict(layout_opts or default_layout_opts())

    has_locations = _has_locations(diagram)
    if has_locations:
        # semiInteractive is a per-parent option: it makes the layered crossing-min keep
        # nodes that carry an elk.position in that relative order, leaving others free.
        layout_opts["elk.layered.crossingMinimization.semiInteractive"] = "true"

    children_by_parent: dict[str | None, list[Group]] = {}
    for g in diagram.groups:
        children_by_parent.setdefault(g.parent, []).append(g)

    comps_by_group: dict[str | None, list[Component]] = {}
    for c in diagram.components:
        comps_by_group.setdefault(c.group, []).append(c)

    def build_group(g: Group) -> dict:
        lw, lh = estimate_text_size(g.name, GROUP_LABEL_FONT)
        group_opts: dict[str, str] = {
            "elk.padding": GROUP_PADDING,
            "elk.nodeLabels.placement": "[H_LEFT, V_TOP, INSIDE]",
        }
        if has_locations:
            # Located children inside this group need semiInteractive on the parent.
            group_opts["elk.layered.crossingMinimization.semiInteractive"] = "true"
        if g.location:
            group_opts.update(_location_node_opts(g.location))
        node: dict = {
            "id": g.id,
            "labels": [{"text": g.name, "width": lw, "height": lh}],
            "layoutOptions": group_opts,
            "children": [],
        }
        for sub in children_by_parent.get(g.id, []):
            node["children"].append(build_group(sub))
        for c in comps_by_group.get(g.id, []):
            node["children"].append(build_component(c))
        return node

    def build_component(c: Component) -> dict:
        w, h, lines, font, _ = compute_node_layout(c.name, c.type)
        longest_chars = max(len(l) for l in lines)
        lw = int(longest_chars * font * 0.58)
        lh = int(len(lines) * font * 1.25)
        node: dict = {
            "id": c.id,
            "width": w,
            "height": h,
            "labels": [{"text": c.name, "width": lw, "height": lh}],
        }
        if c.location:
            node["layoutOptions"] = _location_node_opts(c.location)
        return node

    root_children: list[dict] = []
    for g in children_by_parent.get(None, []):
        root_children.append(build_group(g))
    for c in comps_by_group.get(None, []):
        root_children.append(build_component(c))

    edges: list[dict] = []
    for i, conn in enumerate(diagram.connections):
        edge: dict = {
            "id": f"e{i}",
            "sources": [conn.from_],
            "targets": [conn.to],
        }
        if conn.protocol:
            lw, lh = estimate_text_size(conn.protocol, EDGE_LABEL_FONT)
            edge["labels"] = [{"text": conn.protocol, "width": lw, "height": lh}]
        edges.append(edge)

    return {
        "id": "root",
        "layoutOptions": layout_opts,
        "children": root_children,
        "edges": edges,
    }
