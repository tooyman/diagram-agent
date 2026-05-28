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

components:
  - id: order_api
    name: "Order API"
    group: app_tier                    # optional; null = top-level
    type: server                       # see vocab below
    lifecycle_status: unchanged        # unchanged | updated | new

connections:
  - from: order_api
    to: orders_db
    protocol: REST                     # see protocol routing below
    status: existing                   # existing | new
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

## Pipeline

```
YAML → pydantic validation → metadata-to-ELK JSON
     → Node.js elkjs subprocess (layered, orthogonal, INCLUDE_CHILDREN)
     → geometry validator (overlap, edge-through-node, crossings, label collision)
     → SVG renderer (multi-line wrapped labels, per-type shapes)
     → HTML viewer wrapper (mousewheel zoom, drag pan, Fit button)
```

If hard geometry failures (node overlap, edge-through-node, group overflow, excess crossings) are detected, the CLI retries layout with progressively bigger spacings / different placement strategy (up to 5 retries). The LLM is **never** in this retry loop.

## CLI flags

```
run.sh <input.yaml> [-o OUTPUT_PATH] [--no-retry] [--quiet]
```

- Default output: `output/diagram.svg` (HTML viewer written as `.html` alongside).
- `--no-retry`: run layout once, skip validator-driven retries.

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
│   ├── validator.py         # geometry checks
│   ├── textlayout.py        # word wrap + per-type sizing
│   └── cli.py               # entrypoint + retry loop
├── elk_helper/              # Node.js ELK runner
│   ├── layout.js
│   ├── package.json
│   └── node_modules/        # created by setup.sh
└── reference/
    ├── schema.md            # full field-by-field schema
    └── example.yaml         # minimal 5-node example

## Important constraints

- **Never ask the LLM to produce SVG, drawio XML, or coordinates.** Only YAML metadata.
- **Never put the LLM in a visual-verification loop.** The validator handles that deterministically.
- **Closed vocabularies matter.** Unknown enum values for `type`, `lifecycle_status`, or `status` will fail schema validation.
- **Component IDs must be unique and referenced consistently** in `group`, `from`, `to`, `parent`.
