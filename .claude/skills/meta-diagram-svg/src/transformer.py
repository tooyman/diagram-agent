from __future__ import annotations

from .schema import Component, Diagram, Group
from .textlayout import (
    EDGE_LABEL_FONT,
    GROUP_LABEL_FONT,
    compute_node_layout,
    estimate_text_size,
)

GROUP_PADDING = "[top=42,left=22,bottom=22,right=22]"


def default_layout_opts() -> dict[str, str]:
    # INCLUDE_CHILDREN is required: SEPARATE_CHILDREN drops all cross-hierarchy
    # edges from routing (~80% of NLEADS edges are cross-hierarchy). Compaction
    # is instead achieved via aspectRatio + post-compaction + thoroughness.
    return {
        "elk.algorithm": "layered",
        "elk.direction": "RIGHT",
        "elk.layered.spacing.nodeNodeBetweenLayers": "55",
        "elk.spacing.nodeNode": "32",
        "elk.spacing.edgeNode": "18",
        "elk.spacing.edgeEdge": "10",
        "elk.spacing.componentComponent": "40",
        "elk.edgeRouting": "ORTHOGONAL",
        "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
        "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
        "elk.hierarchyHandling": "INCLUDE_CHILDREN",
        "elk.layered.mergeEdges": "false",
        "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
        "elk.aspectRatio": "1.6",
        "elk.layered.thoroughness": "30",
        "elk.layered.compaction.postCompaction.strategy": "LEFT_RIGHT_CONSTRAINT_LOCKING",
        "elk.layered.compaction.connectedComponents": "true",
    }


def metadata_to_elk(diagram: Diagram, layout_opts: dict[str, str] | None = None) -> dict:
    layout_opts = layout_opts or default_layout_opts()

    children_by_parent: dict[str | None, list[Group]] = {}
    for g in diagram.groups:
        children_by_parent.setdefault(g.parent, []).append(g)

    comps_by_group: dict[str | None, list[Component]] = {}
    for c in diagram.components:
        comps_by_group.setdefault(c.group, []).append(c)

    def build_group(g: Group) -> dict:
        lw, lh = estimate_text_size(g.name, GROUP_LABEL_FONT)
        node: dict = {
            "id": g.id,
            "labels": [{"text": g.name, "width": lw, "height": lh}],
            "layoutOptions": {
                "elk.padding": GROUP_PADDING,
                "elk.nodeLabels.placement": "[H_LEFT, V_TOP, INSIDE]",
            },
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
        return {
            "id": c.id,
            "width": w,
            "height": h,
            "labels": [{"text": c.name, "width": lw, "height": lh}],
        }

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
