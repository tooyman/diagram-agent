---
name: integration-flow-html
description: Translates Acme enterprise architecture YAML metadata into a premium, interactive 2D diagram dashboard HTML page using a native interactive SVG rendering engine with obstacle avoidance and nested fanning.
---

# Skill: Acme Integration Flow Diagram Agent (Interactive HTML Edition)

This skill enables the main agent to compile hierarchical Siamese Commercial Bank (Acme) enterprise architecture metadata YAML files directly into a self-contained, responsive, interactive HTML/JS diagram dashboard. The layout rendering, node alignments, and orthogonal elbow connections are handled programmatically by a native client-side SVG rendering engine with dynamic obstacle-avoidance routing and nested fanning, guaranteeing 100% parity with vector SVG outputs.

---

## 1. Main Agent Playbook

When the user triggers `/integration-flow-html <metadata.yaml> [output_name.html]`, the main agent must follow this protocol:

1. **Read & Parse Input**: Read the input architecture metadata YAML file.
2. **Compile to JSON**: Structure the parsed YAML file into a valid JSON object matching this schema:
   ```json
   {
     "title": "Diagram Title String",
     "groups": [
       { "id": "group_id", "name": "Group Label Name", "style": "visual style description", "parent": "parent_group_id_if_nested" }
     ],
     "components": [
       { "id": "comp_id", "name": "Component Label Name", "group": "container_group_id", "type": "server/gateway/mainframe/channel/external_partner", "lifecycle_status": "unchanged/updated/new" }
     ],
     "connections": [
       { "from": "source_comp_id", "to": "target_comp_id", "protocol": "REST/SOAP/MQ/XML", "status": "existing/new" }
     ]
   }
   ```
3. **Read HTML Template**: Load the contents of the template HTML file located at `.agents/skills/integration_flow_html/resources/template.html`.
4. **Inject JSON Payload**:
   - Replace the placeholder comment `/* DIAGRAM_DATA_JSON_PLACEHOLDER */` inside the `<script id="diagram-data-block">` block with the compiled JSON string representing the architecture metadata.
   - For example:
     ```html
     <script id="diagram-data-block" type="application/json">
       {
         "title": "NLEADS - Real-time Integration Architecture",
         "groups": [...],
         "components": [...],
         "connections": [...]
       }
     </script>
     ```
5. **Write Output File**: Save the resulting HTML file in the workspace under `generated_diagrams/[output_name].html`.
6. **Await & Report**: Provide the clickable link to the generated HTML file in the workspace (e.g. `[nleads_viewer.html](file:///path/to/generated_diagrams/[output_name].html)`) so the user can open it in their browser.
