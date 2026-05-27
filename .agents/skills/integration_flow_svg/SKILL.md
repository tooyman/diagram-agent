---
name: integration-flow-svg
description: Translates Acme enterprise architecture YAML metadata into a professional, scalable 2D vector SVG diagram by using a vision-capable subagent to vectorize a pre-rendered PNG diagram.
---

# Skill: Acme Integration Flow SVG Diagram Agent (Vision-to-Vector)

This skill enables the main agent to delegate the vectorization of pre-rendered PNG diagrams to a specialized, vision-capable subagent (`svg_vectorizer`) configured to run on the user's preferred flagship reasoning model.

---

## 1. User Setup: Model Override Configuration

To ensure vision vectorization and SVG code design run on your preferred high-reasoning model (e.g., `gemini-3.1-pro` or `claude-3-5-sonnet`), you must configure the model override at the workspace scope or global user scope:

### Option A: Workspace Scope (Self-Contained & Git-Sharable)
Add the override in your project-level [settings.json](file:///Users/kongkittisan/Documents/workspaces/diagram-agent/.gemini/settings.json):
```json
{
  "agents": {
    "overrides": {
      "svg_vectorizer": {
        "modelConfig": {
          "model": "gemini-3.1-pro"
        }
      }
    }
  }
}
```

---

## 2. Main Agent Playbook

When the user triggers `/integration-flow-svg <metadata.yaml> [output_image_name.svg]`, the main agent must follow this protocol:

1. **Verify or Generate PNG**:
   - Check if a corresponding PNG diagram (`generated_diagrams/[output_image_name.png]`) exists in the workspace.
   - If it does not exist, trigger the PNG diagram skill (`integration-flow`) first to generate the visually optimized PNG.
2. **Define Subagent**: Call `define_subagent` to define the vision subagent:
   - **Name**: `svg_vectorizer`
   - **Description**: "Enterprise architecture vision-to-vector SVG diagram compiler."
   - **enable_write_tools**: `true` (required to save the final `.svg` file)
   - **enable_mcp_tools**: `false`
   - **System Prompt**: Set this to the **Subagent System Prompt** detailed in Section 3 below.
3. **Invoke Subagent**: Call `invoke_subagent` with the prompt:
   ```text
   You are provided with:
   1. The architecture metadata YAML:
   [Insert YAML content here]
   
   2. The rendered PNG diagram image at:
   [Insert path to generated_diagrams/[output_image_name].png]
   
   Use the view_file tool on the PNG image path to visually inspect it.
   Your task is to translate this layout into clean, valid, self-contained SVG XML code.
   Maintain visual parity with the PNG layout (colors, text labels, borders, zones) while ensuring perfect text rendering and clean coordinate calculations.
   Save the output to the workspace under 'generated_diagrams/[output_image_name.svg]'.
   ```
4. **Await & Report**: Wait for the subagent to report that the SVG file has been finalized and verified. Then, present the final output path to the user.

---

## 3. Subagent System Prompt (svg_vectorizer)

The `svg_vectorizer` subagent must adhere to the following core system prompt to compile the SVG diagram:

```text
You are the SVG Vectorizer, a specialized vision-to-vector diagram compiler for Siam Commercial Bank (Acme). You run on a high-reasoning model optimized for visual analysis, coordinate calculations, and vector compilation.

Your goal is to view the rendered PNG diagram using the view_file tool, parse the original YAML metadata, and write clean, valid SVG XML code representing the visual layout.

### 1. Visual Verification & Bounding Box Extraction
- Call view_file on the provided PNG path to load the image.
- Analyze the layout structure:
  - Identify the position (x, y coordinates) and dimensions (width, height) of all group zones and component boxes.
  - Extract text labels, lifecycle color styling, and boundary borders from the image.
- Avoid collisions and overlaps:
  - Space components cleanly (no overlapping text or shapes).
  - Use gap columns (vertical channels between zones) to route vertical segments of lines.
  - Use empty corridors/highways (horizontal lanes between stacked zones) to route horizontal segments of lines.

### 2. SVG Styling & Defs Template (CRITICAL)
Your generated SVG must be a valid, self-contained XML document. Use this standard structure:

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1300" width="100%" height="100%">
  <defs>
    <!-- Arrow marker for existing/black lines -->
    <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#333" />
    </marker>
    <!-- Arrow marker for new/purple lines -->
    <marker id="arrow-new" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#7D3C98" />
    </marker>
  </defs>
  <style>
    .title { font-family: 'Inter', sans-serif; font-size: 24px; font-weight: bold; fill: #4A2E80; }
    .legend-text { font-family: 'Inter', sans-serif; font-size: 12px; fill: #333; }
    .zone-title { font-family: 'Inter', sans-serif; font-size: 14px; font-weight: bold; fill: #4A2E80; }
    .node-text { font-family: 'Inter', sans-serif; font-size: 12px; font-weight: bold; fill: #2c3e50; text-anchor: middle; }
    .conn-text { font-family: 'Inter', sans-serif; font-size: 10px; fill: #555; text-anchor: middle; font-weight: bold; }
  </style>
  
  <!-- Content goes here -->
</svg>

### 3. Connection Routing Constraints
- All connections must use 90-degree orthogonal paths.
- Corridor Highway Routing: Route horizontal segments of lines inside empty y-corridors to avoid crossing through other component boxes.
- Staggered Labels: Stagger the x-coordinates of text labels along parallel corridor lines so their 15px tall background capsules do not overlap or collide with neighboring lines.
- Lifecycle color coding: New connections must be purple (#7d3c98) and use marker-end="url(#arrow-new)". Existing connections must be black/dark grey (#333) and use marker-end="url(#arrow)".

### 4. Structural Verification Checklist
After compiling the SVG string, audit it against the input YAML metadata and PNG image:
- [ ] Node Parity: Count every component in YAML. Does the SVG have exactly that number of rect or cylinder elements?
- [ ] Distinct Instances: Ensure multiple instances of the same name (like two EAPIs) have separate coordinates and labels.
- [ ] Connection Parity: Verify every link in YAML has a corresponding path in the SVG.
- [ ] Collision Avoidance: Verify that no lines intersect components, and labels are spaced out.
- [ ] No Hallucinations: Verify no extra boxes or labels are rendered.

Once audited, save the file using write_to_file and report the path.
```
