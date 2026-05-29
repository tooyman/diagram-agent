# Schema reference

The full pydantic schema lives in `src/schema.py`. This is a flat field-by-field summary.

## Top-level

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | yes | Rendered at top of SVG |
| `groups` | list[Group] | no | Optional grouping boundaries |
| `components` | list[Component] | yes | The nodes in the diagram |
| `connections` | list[Connection] | yes | The edges |

## Group

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `id` | string | yes | — | Unique within `groups` |
| `name` | string | yes | — | Rendered as group label |
| `parent` | string \| null | no | null | Parent group id; null = top-level |
| `kind` | enum | no | `generic` | Reserved for future per-zone styling: `cloud / onprem / partner / saas / internal / generic` |
| `location` | enum \| null | no | null | Optional compass placement hint — see [Location hints](#location-hints) |

Notes:
- Groups can nest arbitrarily deep via `parent`.
- An unknown `parent` id fails validation.

## Component

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `id` | string | yes | — | Unique within `components` |
| `name` | string | yes | — | Rendered as node label (wraps to ≤3 lines) |
| `group` | string \| null | no | null | Owning group id; null = top-level |
| `type` | enum | no | `server` | See type table |
| `lifecycle_status` | enum | no | `unchanged` | `unchanged / updated / new` |
| `location` | enum \| null | no | null | Optional compass placement hint — see [Location hints](#location-hints) |

### type enum

| value | shape rendered |
|---|---|
| `actor` | Stick figure (user/customer/operator) |
| `channel` | Rounded rectangle (user-facing UI) |
| `gateway` | Hexagon (API gateway, broker entry) |
| `server` | Rounded rectangle (default) |
| `core_engine` | Bold rectangle, light blue fill (the centerpiece system) |
| `mainframe` | Rectangle with folded top-right corner |
| `datastore` | Cylinder |
| `queue` | Rectangle with internal vertical dividers |
| `external_partner` | Double-bordered rectangle |

### lifecycle_status enum

| value | node fill |
|---|---|
| `unchanged` | White |
| `updated` | Light yellow |
| `new` | Light pink |

(`core_engine` overrides fill to light blue regardless of status.)

## Location hints

`location` is an **optional** coarse placement hint you can put on any group or component.
Omit it and placement is fully automatic (the default). Add it and the layout engine tries
to anchor that node to the named region of a 3×3 compass.

| value | horizontal | vertical |
|---|---|---|
| `north_west` | left column | top |
| `north` | natural flow | top |
| `north_east` | right column | top |
| `west` | left column | middle |
| `center` | natural flow | middle |
| `east` | right column | middle |
| `south_west` | left column | bottom |
| `south` | natural flow | bottom |
| `south_east` | right column | bottom |

How it maps onto the layered engine (direction = left→right):

- **Horizontal** is a hard *column* pin. `west*` forces the node into the **first** column
  (ELK `layerConstraint = FIRST`), `east*` into the **last** column (`LAST`). `center` /
  `north` / `south` apply **no** horizontal force — the node lands wherever the edge flow
  puts it. (A forced *middle* column isn't expressible without partitioning, which would
  break the flow, so it's intentionally left free.)
- **Vertical** is a *soft* ordering seed. `north*` sorts toward the top of its column,
  `south*` toward the bottom, `*center*`/`west`/`east` toward the middle. It nudges
  in-column order; it is not an absolute y coordinate.

### Practical rules of thumb

- The hint is opt-in *per diagram*: the engine only switches on location handling when at
  least one node carries a `location`. A diagram with none behaves exactly as before.
- `west` = literally column 0 (nothing can precede it), `east` = the final column (nothing
  can follow it). So put `west` on a **true source** and `east` on a **true sink**. Do not
  pin a whole source→…→sink *chain* to `west` — that collapses the columns and produces
  backward-routed spaghetti. Pin the entry tier (or just the entry node) and let the rest
  flow.
- These are *hints*, not guarantees. If a hinted layout produces hard geometry failures
  (overlap, edge-through-node, overflow), the retry ladder may relax things; the
  direction-flipping retry step is automatically skipped while locations are in play so the
  compass mapping stays consistent.

See `reference/located.yaml` for a worked example (channels left, core engine center, data
stores right, SMTP/log servers at the bottom).

## Connection

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `from` | string | yes | — | Source — a component **or** group id |
| `to` | string | yes | — | Target — a component **or** group id |
| `protocol` | string \| null | no | null | Free text; categorized for edge style |
| `status` | enum | no | `existing` | `existing / new` |

### Group endpoints

An endpoint (`from` / `to`) may name a **group** instead of a component. ELK attaches the
edge to that group's boundary (the dashed zone rectangle), so you can draw a connection that
targets a whole zone rather than one node inside it — e.g. "Client → Edge zone" or
"Edge zone → Core zone". Both endpoints can be groups (group→group) or mixed
(component↔group). The group is a layout container, so the edge lands on its border, not on
any particular child. Nothing else changes: routing, styling, and arrowheads behave exactly
as for component endpoints.

### Protocol → edge style mapping

| Protocol | Line style | Color |
|---|---|---|
| `REST`, `SOAP`, `HTTPS`, `gRPC` | Solid | Black |
| `MQ`, `MQ/XML`, `Kafka`, `Publish`, `Subscribe` | Dashed | Black |
| `SFTP`, `SMTP`, `XML` | Solid | Blue |
| anything else | Solid | Black |

All edges are routed orthogonally with arrowheads at the target.

## Validation rules (enforced by pydantic before layout)

- Every `parent` must reference an existing group id.
- Every `group` (on component) must reference an existing group id.
- Every `from` / `to` must reference an existing component **or** group id.
- A single id may not be used by both a group and a component (the union would be ambiguous
  for connection endpoints).
- Enum values must be in the closed vocabulary above.
- Extra fields in YAML are silently ignored (allows the original `style:` field in `nleads_metadata.yaml` to coexist without erroring).

## Geometry validation (after layout, before SVG emission)

These checks run on ELK's laid-out output. Hard failures trigger a retry with adjusted layout parameters.

| Code | Severity | Meaning |
|---|---|---|
| `node_overlap` | hard | Two component rectangles intersect |
| `edge_through_node` | hard | An edge segment crosses a non-endpoint node |
| `group_overflow` | hard | A component rectangle extends past its declared group |
| `edge_crossings` (>30) | hard | Excessive edge crossings (warn at >10) |
| `label_collision` | soft | An edge label overlaps a node |
| `aspect_ratio` | soft | Canvas w/h outside [0.4, 3.0] |

### Edge-through-node repair (runs before any retry)

`edge_through_node` — an edge routed straight through a node it isn't connected to — is the
single ugliest layout defect, and the old fix (retry with bigger spacing) wasted space. So
before the retry ladder kicks in, a targeted repair pass reroutes *just the offending
segment* around the obstacle with a small orthogonal detour. A detour may add an edge
crossing, which is fine: the validator tolerates crossings up to a budget (default 10,
configurable via `--crossing-budget`), so the pass "spends" from that quota instead of
forcing a global spread. Obstacles that can't be cleared within budget are left in place and
fall through to the spacing-bump retry ladder. This keeps the tight, compact spacing while
still eliminating the ugly lines in the common case.

### Wraparound control (handled inside ELK, not as a post-pass)

A different ugliness from edge-through-node: an edge that doesn't pierce any box but is routed
the long way *around* the canvas. ELK does this most often for a backward edge into a
high-degree hub — the direct lane is packed with boxes, so the only collision-free route left
is the outer border, producing a loop several times longer than the straight-line distance.

This is addressed at the source by the base layout options in `default_layout_opts()`
(`src/transformer.py`), not by rewriting routes afterwards. Two ELK levers do the work:

- `elk.layered.nodePlacement.strategy = BRANDES_KOEPF` — ELK's well-tested default placement
  (the pipeline had previously overridden it to `NETWORK_SIMPLEX`). BK packs the layers
  tighter, so a backward edge into a hub no longer has to detour around the whole border.
- `elk.layered.considerModelOrder.strategy = NONE` — frees crossing-minimization from the
  YAML authoring order so ELK can reorder nodes within a layer to shorten edges.

On the NLEADS hub-and-spoke these two together shrink canvas area ~14% and drop the worst
detour ratio from ~3.8× to ~2.7× with no extra crossings. The trade-off is deliberate: this
is a coarse, whole-graph adjustment (it affects every edge, and some backward edges into a
busy hub are still longer than ideal), but every node, endpoint, and arrowhead stays exactly
where ELK's own router places it — no custom edge geometry, so nothing can break ELK's port
attachment or arrowhead direction.
