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

## Connection

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `from` | string | yes | — | Source component id |
| `to` | string | yes | — | Target component id |
| `protocol` | string \| null | no | null | Free text; categorized for edge style |
| `status` | enum | no | `existing` | `existing / new` |

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
- Every `from` / `to` must reference an existing component id.
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
