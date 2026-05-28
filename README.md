# diagram-agent

A Claude skill that generates good-looking **logical architecture diagrams** from declarative YAML metadata — without putting the LLM in the visual loop.

The LLM only writes schema-valid YAML. Layout (ELK) and rendering (SVG) are deterministic. A geometry validator checks the output and retries layout on hard failures — but the LLM is never asked to "look at the picture and fix it."

## Quick start

```bash
# One-time install (requires python3 and node on PATH)
.claude/skills/meta-diagram-svg/setup.sh

# Generate
.claude/skills/meta-diagram-svg/run.sh examples/simple.yaml -o output/simple.svg
```

Outputs:
- `output/simple.svg` — raw SVG (scales in any browser)
- `output/simple.html` — viewer with mousewheel zoom, drag pan, Fit button

## What's inside

| Path | Purpose |
|---|---|
| `.claude/skills/meta-diagram-svg/` | The whole skill — self-contained, bundle-able |
| `.claude/skills/meta-diagram-svg/SKILL.md` | Skill definition (frontmatter + how-to-use) |
| `.claude/skills/meta-diagram-svg/README.html` | Human-readable summary (open in browser) |
| `.claude/skills/meta-diagram-svg/src/` | Python pipeline |
| `.claude/skills/meta-diagram-svg/elk_helper/` | Node.js ELK runner |
| `.claude/skills/meta-diagram-svg/reference/` | Schema docs + minimal example |
| `examples/simple.yaml` | Minimal example metadata |

## Pipeline

```
YAML → pydantic validation → ELK JSON
     → elkjs (layered, orthogonal, INCLUDE_CHILDREN)
     → geometry validator (overlaps, edge-through-node, crossings)
     → SVG renderer (per-type shapes, wrapped multi-line labels)
     → HTML viewer (pan/zoom)
```

See `.claude/skills/meta-diagram-svg/README.html` for the full write-up, schema reference, and embedded example output.

## Using the skill in Claude

The skill is project-local. With this repo open in Claude Code, ask things like:

- "Draw an architecture diagram for an order-processing system with a web channel, an API, a Postgres database, and a Kafka event bus."
- "Update `examples/simple.yaml` to add a Redis cache between the API and DB, then re-render."

Claude picks up the skill via its `description` and writes schema-valid YAML; the runner produces the SVG.
