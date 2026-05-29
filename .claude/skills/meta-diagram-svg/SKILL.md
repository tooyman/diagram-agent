---
name: meta-diagram-svg
description: Generate architecture / system / integration diagrams from declarative YAML metadata. Use when the user wants to draw a diagram from a structured description (components, groups, connections), convert prose architecture notes into a diagram, or update an existing diagram metadata file. The LLM only writes schema-valid YAML — layout (ELK) and rendering (SVG) are deterministic, avoiding visual hallucination. Outputs an SVG and an HTML viewer with pan/zoom. Triggers include "draw an architecture diagram", "diagram this system", "generate a logical diagram", or any task involving a `.yaml` whose shape matches the metadata schema.
---

# meta-diagram-svg

Architecture-diagram generator that separates **semantic extraction** (LLM's job) from **layout + rendering** (deterministic pipeline's job). The LLM only emits YAML conforming to the schema; the program does layout, validation, and SVG rendering.

## When to use this skill

Use it when the user wants any of:
- Generate a diagram from a free-text description of an architecture.
- Convert a list of components / connections into a visual diagram.
- Update or extend an existing metadata YAML (e.g. `nleads_metadata.yaml`).
- Re-render a diagram after editing metadata.

Do **not** use it for:
- Cloud-icon-specific diagrams (AWS / Azure icon notation) — this skill is for *logical* diagrams.
- Sequence / flowchart / ER diagrams — different shape vocabulary.

## How to use

1. **Derive the structure** from user input. Identify: groups (zones / tiers), components (with type), connections (with protocol).
2. **Write metadata YAML** matching the schema below. Save it anywhere convenient (e.g. project root or `examples/`).
3. **Run the bundled generator**:
   ```bash
   .claude/skills/meta-diagram-svg/run.sh <input.yaml> -o output/<name>.svg
   ```
   The runner resolves its own `.venv/` and ELK helper internally, so input/output paths are relative to your CWD (not the skill folder).
4. **Report results**: print the path to the `.html` viewer (`output/<name>.html`) so the user can pan/zoom in a browser. Mention any validator issues.

If this is the first time, run the one-shot setup (creates the venv, installs deps):
```bash
.claude/skills/meta-diagram-svg/setup.sh
```
Setup requires `python3` and `node` on PATH.

## Schema cheat sheet

```yaml
title: "Diagram title"

groups:                                # nestable via `parent`
  - id: app_tier
    name: "Application tier"
  - id: data_tier
    name: "Data tier"
    parent: null                       # or another group id
    location: east                     # optional compass hint (see below)

components:
  - id: order_api
    name: "Order API"
    group: app_tier                    # optional; null = top-level
    type: server                       # see vocab below
    lifecycle_status: unchanged        # unchanged | updated | new
    location: west                     # optional compass hint (see below)

connections:
  - from: order_api
    to: orders_db
    protocol: REST                     # see protocol routing below
    status: existing                   # existing | new
  - from: order_api
    to: data_tier                      # endpoint may be a GROUP id: edge attaches to the
    protocol: MQ                       # group's boundary (component↔group or group↔group)
```

### Closed vocabularies

**`type`** — one of:
| value | shape | when to use |
|---|---|---|
| `actor` | stick figure | end user, customer, operator |
| `channel` | rounded rect | user-facing interface (web, mobile, IVR) |
| `gateway` | hexagon | API gateway, message broker entry, ESB |
| `server` | rounded rect | generic service / app / worker |
| `core_engine` | bold blue rect | the central system being diagrammed |
| `mainframe` | folded-corner rect | mainframe / legacy system |
| `datastore` | cylinder | DB, store, lake |
| `queue` | divided rect | queue / topic / event bus |
| `external_partner` | double-border rect | 3rd-party / partner system |

**`lifecycle_status`** drives node fill:
- `unchanged` → white
- `updated` → light yellow
- `new` → light pink
- (core_engine type overrides → blue)

**`protocol`** is free-text but routed to edge styling:
- Solid line (sync): `REST`, `SOAP`, `HTTPS`, `gRPC`
- Dashed line (async): `MQ`, `MQ/XML`, `Kafka`, `Publish`, `Subscribe`
- Blue line (data): `SFTP`, `SMTP`, `XML`
- Anything else → solid (sync default)

### `location` — optional layout hint (groups & components)

A coarse 3×3 **compass** anchor for macro layout control ("channels left, data lake
right, logging at the bottom"). **Optional** — omit it for fully automatic placement.
Values: `north_west north north_east west center east south_west south south_east`.

- **Horizontal** is a hard column pin: `west*` → first column, `east*` → last column,
  `center`/`north`/`south` → no horizontal force (natural flow).
- **Vertical** is a soft ordering seed: `north*` → top, `south*` → bottom, middle band → centred.
- It only activates when ≥1 node carries a `location`; otherwise behaviour is unchanged.
- **Put `west` on a true source and `east` on a true sink** — `west` is literally column 0
  (nothing precedes it). Pinning a whole source→…→sink chain to `west` collapses columns
  into spaghetti; pin the entry tier only and let the rest flow.

Full table + worked example: `reference/schema.md` (Location hints) and `reference/located.yaml`.

## Pipeline

```
YAML → pydantic validation → metadata-to-ELK JSON (compact spacing + optional location hints)
     → Node.js elkjs subprocess (layered, orthogonal, INCLUDE_CHILDREN)
     → geometry validator (overlap, edge-through-node, crossings, label collision, fill ratio)
     → targeted edge-through-node repair (reroute ugly lines, spend crossing quota)
     → SVG renderer (multi-line wrapped labels, per-type shapes)
     → HTML viewer wrapper (mousewheel zoom, drag pan, Fit button)
```

When an edge is routed straight *through* a node, a repair pass reroutes just that segment
around the obstacle, "spending" from the crossing budget (default 10) rather than spreading
the whole diagram out — this keeps layouts compact. Only if hard failures *survive* repair
(node overlap, group overflow, excess crossings, or an unrepairable through-node) does the
CLI fall back to retrying layout with progressively bigger spacings / a different placement
strategy (up to 5 retries). The LLM is **never** in this retry loop.

**Wraparound control is handled by ELK itself, not a post-pass.** ELK can route an edge
(classically a backward edge into a high-degree hub) the long way around the canvas border
when the direct lane is blocked by the boxes in the middle. Rather than rewrite such edges
afterwards (which fights ELK's port/arrowhead placement), the base layout options in
`default_layout_opts()` are tuned so ELK's own router produces shorter routes:
`nodePlacement.strategy = BRANDES_KOEPF` (ELK's default; packs layers tighter so backward
edges don't have to loop the border) and `considerModelOrder.strategy = NONE` (frees
crossing-minimization from input order to shorten edges). On the NLEADS hub-and-spoke this
shrinks canvas area ~14% and cuts the worst detour ratio from ~3.8× to ~2.7× with no extra
crossings. These are coarse whole-graph levers — every node, endpoint, and arrowhead stays
exactly where ELK places it.

## CLI flags

```
run.sh <input.yaml> [-o OUTPUT_PATH] [--no-retry] [--crossing-budget N] [--quiet]
```

- Default output: `output/diagram.svg` (HTML viewer written as `.html` alongside).
- `--no-retry`: run layout once, skip validator-driven retries (edge repair still runs).
- `--crossing-budget N`: max edge crossings the ugly-line (edge-through-node) repair may spend (default 10).

## Bundled layout

This skill is self-contained — no files at the project root are required.

```
.claude/skills/meta-diagram-svg/
├── SKILL.md
├── README.html              # human-readable summary
├── setup.sh                 # one-shot install (python venv + npm)
├── run.sh                   # runner — call this
├── requirements.txt
├── .venv/                   # created by setup.sh
├── src/                     # the Python pipeline
│   ├── schema.py            # pydantic models
│   ├── transformer.py       # metadata → ELK JSON
│   ├── layout.py            # subprocess to elk_helper
│   ├── render.py            # SVG + HTML viewer
│   ├── validator.py         # geometry checks + fill_ratio + crossing count
│   ├── reroute.py           # targeted edge-through-node repair
│   ├── textlayout.py        # word wrap + per-type sizing
│   └── cli.py               # entrypoint + repair/retry loop
├── elk_helper/              # Node.js ELK runner
│   ├── layout.js
│   ├── package.json
│   └── node_modules/        # created by setup.sh
└── reference/
    ├── schema.md            # full field-by-field schema
    ├── example.yaml         # minimal 5-node example
    └── located.yaml         # compass `location` hint demo

## Important constraints

- **Never ask the LLM to produce SVG, drawio XML, or coordinates.** Only YAML metadata.
- **Never put the LLM in a visual-verification loop.** The validator handles that deterministically.
- **Closed vocabularies matter.** Unknown enum values for `type`, `lifecycle_status`, or `status` will fail schema validation.
- **Component IDs must be unique and referenced consistently** in `group`, `from`, `to`, `parent`.
- **A connection endpoint (`from`/`to`) may be a component *or* a group id.** Naming a group
  attaches the edge to that zone's boundary (component↔group or group↔group). Group and
  component ids must not collide, since endpoints resolve against both id-spaces.
