import json
import re

# Import data from generate_svg
from generate_svg import data

template_path = "/Users/kongkittisan/Documents/workspaces/diagram-agent/.agents/skills/integration_flow_html/resources/template.html"
viewer_path = "/Users/kongkittisan/Documents/workspaces/diagram-agent/generated_diagrams/nleads_viewer.html"

# 1. Update template.html
with open(template_path, 'r') as f:
    template_content = f.read()

# Replace subtitle text in header if present
template_content = template_content.replace(
    '<p style="font-size: 11px; color: var(--text-muted);">Layout-Engine Rendered (Cytoscape.js + Dagre)</p>',
    '<p style="font-size: 11px; color: var(--text-muted);">Dynamic Obstacle-Avoidance SVG Layout</p>'
)

# Replace the App Logic Script block
# Find everything from <script> after <!-- App Logic Script -->
pattern = r'(<!-- App Logic Script -->\s*<script>).*?(</script>\s*</body>)'
app_logic_replacement = r'\\1\n        // App logic replaced programmatically\n\\2'

# Let's write the App Logic JavaScript code
js_code = """
        let data = null;
        let zoom = 1.0;
        let panX = 0;
        let panY = 0;
        let isPanning = false;
        let startX = 0;
        let startY = 0;
        let selectedElementId = null;
        let isSelectedEdge = false;

        // Load data from script block
        function loadDiagramData() {
            try {
                const text = document.getElementById('diagram-data-block').textContent;
                if (text.includes('DIAGRAM_DATA_JSON_PLACEHOLDER')) {
                    return getSampleData();
                }
                return JSON.parse(text);
            } catch (e) {
                console.error("Failed to parse diagram data JSON, falling back to sample data.", e);
                return getSampleData();
            }
        }

        // Theme toggler
        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            body.setAttribute('data-theme', newTheme);
            document.getElementById('theme-toggle').textContent = newTheme === 'light' ? '🌙 Theme' : '☀️ Theme';
            
            // Re-render SVG to apply theme color mappings
            const viewport = document.querySelector('g.viewport');
            const currentTransform = viewport ? viewport.getAttribute('transform') : '';
            renderDiagram();
            const newViewport = document.querySelector('g.viewport');
            if (newViewport && currentTransform) {
                newViewport.setAttribute('transform', currentTransform);
            }
            applyFilters();
            if (selectedElementId !== null) {
                highlightSVGElement(selectedElementId, isSelectedEdge);
            }
        }

        const nodePositions = {
            "acme_connect": {"x": 150, "y": 140},
            "partner_eco": {"x": 370, "y": 140},
            "acme_one": {"x": 590, "y": 140},
            "ast_tool": {"x": 920, "y": 140},
            "call_center": {"x": 1470, "y": 140},

            "eapi_onprem_1": {"x": 480, "y": 330},
            "eapi_onprem_2": {"x": 700, "y": 330},
            "mq_broker_1": {"x": 480, "y": 470},
            "nleads_engine": {"x": 920, "y": 470},
            "mq_broker_2": {"x": 1360, "y": 470},
            "eapi_azure": {"x": 1360, "y": 330},

            "als": {"x": 150, "y": 340},
            "mg_cheque": {"x": 150, "y": 430},
            "gn": {"x": 150, "y": 520},

            "rm": {"x": 1580, "y": 340},
            "im_st": {"x": 1580, "y": 430},
            "faat": {"x": 1580, "y": 520},

            "estm": {"x": 150, "y": 720},
            "lhs": {"x": 370, "y": 720},
            "ncb": {"x": 590, "y": 720},
            "ncbos": {"x": 810, "y": 720},
            
            "nss": {"x": 150, "y": 810},
            "sfwh": {"x": 370, "y": 810},
            "ref_data": {"x": 590, "y": 810},
            "svaf": {"x": 810, "y": 810},

            "watch_list": {"x": 150, "y": 900},
            "actm": {"x": 370, "y": 900},
            "enlite": {"x": 590, "y": 900},

            "ecm_unsecured": {"x": 1580, "y": 720},
            "ecm_lead": {"x": 1580, "y": 810},
            "fos": {"x": 1580, "y": 900},

            "ade": {"x": 1360, "y": 580},
            "emv": {"x": 1360, "y": 670},
            "nmsx": {"x": 1360, "y": 760},

            "confluent_kafka": {"x": 1140, "y": 630},
            "e_kafka": {"x": 1140, "y": 720},

            "sftp_server": {"x": 150, "y": 1080},
            "smtp_custard": {"x": 370, "y": 1080},
            "smtp_zimba": {"x": 590, "y": 1080},
            "dmip_nleads": {"x": 810, "y": 1080},
            "ecm_autoloan": {"x": 810, "y": 1170},

            "mitsubishi": {"x": 1030, "y": 1080},
            "deves": {"x": 1250, "y": 1080},
            "omakase": {"x": 1140, "y": 1170},
            "dlt": {"x": 1360, "y": 1170},

            "payroll": {"x": 1470, "y": 1080},
            "icore": {"x": 1580, "y": 1080}
        };

        const parentOverrides = {
            "nleads_engine": "on_premise_upper",
            "eapi_azure": "on_premise_upper",
            "confluent_kafka": "on_premise_upper",
            "e_kafka": "on_premise_upper"
        };

        function getNodeDims(id, type) {
            if (id === 'nleads_engine') {
                return { w: 145, h: 65 };
            } else if (type === 'mainframe') {
                return { w: 130, h: 42 };
            } else {
                return { w: 125, h: 46 };
            }
        }

        // SVG blockage helpers
        function isVerticalSegmentBlocked(x, yMin, yMax, excludeIds) {
            const marginX = 10;
            const marginY = 5;
            const yStart = Math.min(yMin, yMax);
            const yEnd = Math.max(yMin, yMax);
            for (const cId of Object.keys(nodePositions)) {
                if (excludeIds && excludeIds.includes(cId)) continue;
                const pos = nodePositions[cId];
                const comp = data.components.find(c => c.id === cId);
                if (!comp) continue;
                const dims = getNodeDims(cId, comp.type);
                const compXMin = pos.x - dims.w/2 - marginX;
                const compXMax = pos.x + dims.w/2 + marginX;
                const compYMin = pos.y - dims.h/2 - marginY;
                const compYMax = pos.y + dims.h/2 + marginY;
                
                if (x >= compXMin && x <= compXMax) {
                    if (Math.max(yStart, compYMin) <= Math.min(yEnd, compYMax)) {
                        return true;
                    }
                }
            }
            return false;
        }

        function isHorizontalSegmentBlocked(y, xMin, xMax, excludeIds) {
            const marginX = 5;
            const marginY = 10;
            const xStart = Math.min(xMin, xMax);
            const xEnd = Math.max(xMin, xMax);
            for (const cId of Object.keys(nodePositions)) {
                if (excludeIds && excludeIds.includes(cId)) continue;
                const pos = nodePositions[cId];
                const comp = data.components.find(c => c.id === cId);
                if (!comp) continue;
                const dims = getNodeDims(cId, comp.type);
                const compXMin = pos.x - dims.w/2 - marginX;
                const compXMax = pos.x + dims.w/2 + marginX;
                const compYMin = pos.y - dims.h/2 - marginY;
                const compYMax = pos.y + dims.h/2 + marginY;
                
                if (y >= compYMin && y <= compYMax) {
                    if (Math.max(xStart, compXMin) <= Math.min(xEnd, compXMax)) {
                        return true;
                    }
                }
            }
            return false;
        }

        function findCleanVerticalCorridor(sxPort, syPort, txPort, tyPort, srcId, tgtId) {
            const candidates = [
                (sxPort + txPort) / 2,
                260, 450, 535, 645, 755, 880, 920, 1005, 1255, 1430, 1525
            ];
            let bestX = null;
            let minDist = 999999;
            for (const x of candidates) {
                if (isVerticalSegmentBlocked(x, syPort, tyPort, [srcId, tgtId])) continue;
                if (isHorizontalSegmentBlocked(syPort, sxPort, x, [srcId, tgtId])) continue;
                if (isHorizontalSegmentBlocked(tyPort, x, txPort, [srcId, tgtId])) continue;
                
                const midpoint = (sxPort + txPort) / 2;
                let dist = Math.abs(x - midpoint);
                const xMin = Math.min(sxPort, txPort);
                const xMax = Math.max(sxPort, txPort);
                if (!(x >= xMin - 5 && x <= xMax + 5)) {
                    dist += 300;
                }
                if (dist < minDist) {
                    minDist = dist;
                    bestX = x;
                }
            }
            if (bestX !== null) return bestX;
            return (sxPort + txPort) / 2;
        }

        function findCleanHorizontalCorridor(sxPort, syPort, txPort, tyPort, srcId, tgtId) {
            const candidates = [
                (syPort + tyPort) / 2,
                235, 610, 990
            ];
            let bestY = null;
            let minDist = 999999;
            for (const y of candidates) {
                if (isHorizontalSegmentBlocked(y, sxPort, txPort, [srcId, tgtId])) continue;
                if (isVerticalBlockedSimple(srcId, {x: sxPort, y: y}) || isVerticalBlockedNearTargetSimple(tgtId, {x: txPort, y: y})) continue;
                if (isVerticalSegmentBlocked(sxPort, syPort, y, [srcId, tgtId])) continue;
                if (isVerticalSegmentBlocked(txPort, y, tyPort, [srcId, tgtId])) continue;
                
                const midpoint = (syPort + tyPort) / 2;
                let dist = Math.abs(y - midpoint);
                const yMin = Math.min(syPort, tyPort);
                const yMax = Math.max(syPort, tyPort);
                if (!(y >= yMin - 5 && y <= yMax + 5)) {
                    dist += 300;
                }
                if (dist < minDist) {
                    minDist = dist;
                    bestY = y;
                }
            }
            if (bestY !== null) return bestY;
            return (syPort + tyPort) / 2;
        }

        function isVerticalBlockedSimple(srcId, tgtPos) {
            const srcPos = nodePositions[srcId];
            if (!srcPos) return false;
            const yMin = Math.min(srcPos.y, tgtPos.y);
            const yMax = Math.max(srcPos.y, tgtPos.y);
            for (const cId of Object.keys(nodePositions)) {
                if (cId === srcId) continue;
                const pos = nodePositions[cId];
                if (Math.abs(pos.x - srcPos.x) < 15 && pos.y > yMin && pos.y < yMax) {
                    return true;
                }
            }
            return false;
        }

        function isVerticalBlockedNearTargetSimple(tgtId, srcPos) {
            const tgtPos = nodePositions[tgtId];
            if (!tgtPos) return false;
            const yMin = Math.min(srcPos.y, tgtPos.y);
            const yMax = Math.max(srcPos.y, tgtPos.y);
            for (const cId of Object.keys(nodePositions)) {
                if (cId === tgtId) continue;
                const pos = nodePositions[cId];
                if (Math.abs(pos.x - tgtPos.x) < 15 && pos.y > yMin && pos.y < yMax) {
                    return true;
                }
            }
            return false;
        }

        function renderDiagram() {
            const theme = document.body.getAttribute('data-theme') || 'light';
            const isDark = theme === 'dark';
            
            const themeColors = {
                yellowFill: isDark ? "rgba(254, 253, 232, 0.05)" : "rgba(254, 253, 232, 0.15)",
                purpleFill: isDark ? "rgba(250, 244, 252, 0.05)" : "rgba(250, 244, 252, 0.15)",
                greenFill: isDark ? "rgba(244, 253, 248, 0.05)" : "rgba(244, 253, 248, 0.15)",
                blueFill: isDark ? "rgba(244, 249, 253, 0.04)" : "rgba(244, 249, 253, 0.12)",
                blackFill: isDark ? "rgba(30, 35, 53, 0.4)" : "rgba(248, 249, 249, 0.4)",
                greyFill: isDark ? "rgba(30, 35, 53, 0.1)" : "rgba(149, 165, 166, 0.05)",
                whiteFill: isDark ? "#1f2335" : "#ffffff",
                nodeText: isDark ? "#f8f9fa" : "#2d3748",
                edgeColor: isDark ? "#8a9ab0" : "#4a5568",
                groupTitle: isDark ? "#a0aec0" : "#4A2E80",
                labelBg: isDark ? "#1f2335" : "#ffffff",
                labelBorder: isDark ? "#2e344e" : "#e2e8f0"
            };

            const groupsChildren = {};
            data.components.forEach(comp => {
                const cId = comp.id;
                const groupId = parentOverrides[cId] || comp.group;
                if (groupId) {
                    if (!groupsChildren[groupId]) groupsChildren[groupId] = [];
                    groupsChildren[groupId].push(cId);
                }
            });

            const groupBounds = {};
            const groupDefinitions = {};
            data.groups.forEach(g => {
                groupDefinitions[g.id] = g;
            });

            Object.keys(groupsChildren).forEach(gId => {
                const children = groupsChildren[gId];
                let xs = [], ys = [];
                children.forEach(cId => {
                    const pos = nodePositions[cId];
                    if (pos) {
                        const comp = data.components.find(c => c.id === cId) || { type: 'server' };
                        const dims = getNodeDims(cId, comp.type);
                        xs.push(pos.x - dims.w / 2, pos.x + dims.w / 2);
                        ys.push(pos.y - dims.h / 2, pos.y + dims.h / 2);
                    }
                });
                if (xs.length && ys.length) {
                    const padX = 35, padY = 45;
                    groupBounds[gId] = {
                        x: Math.min(...xs) - padX,
                        y: Math.min(...ys) - padY,
                        w: (Math.max(...xs) - Math.min(...xs)) + (2 * padX),
                        h: (Math.max(...ys) - Math.min(...ys)) + (2 * padY)
                    };
                }
            });

            data.groups.forEach(g => {
                const gId = g.id;
                const parentId = g.parent;
                if (parentId && groupBounds[gId]) {
                    if (!groupBounds[parentId]) {
                        groupBounds[parentId] = { x: 9999, y: 9999, w: 0, h: 0 };
                    }
                    const pBounds = groupBounds[parentId];
                    const cBounds = groupBounds[gId];
                    
                    const minX = pBounds.x !== 9999 ? Math.min(pBounds.x, cBounds.x) : cBounds.x;
                    const minY = pBounds.y !== 9999 ? Math.min(pBounds.y, cBounds.y) : cBounds.y;
                    const pMaxX = pBounds.w > 0 ? pBounds.x + pBounds.w : -9999;
                    const cMaxX = cBounds.x + cBounds.w;
                    const maxX = Math.max(pMaxX, cMaxX);
                    const pMaxY = pBounds.h > 0 ? pBounds.y + pBounds.h : -9999;
                    const cMaxY = cBounds.y + cBounds.h;
                    const maxY = Math.max(pMaxY, cMaxY);
                    
                    pBounds.x = minX - 10;
                    pBounds.y = minY - 10;
                    pBounds.w = (maxX - minX) + 20;
                    pBounds.h = (maxY - minY) + 20;
                }
            });

            const nodePorts = {};
            Object.keys(nodePositions).forEach(id => {
                nodePorts[id] = { Left: [], Right: [], Top: [], Bottom: [] };
            });
            const connectionFaces = [];

            data.connections.forEach((conn, index) => {
                const srcId = conn.from;
                const tgtId = conn.to;
                const srcPos = nodePositions[srcId];
                const tgtPos = nodePositions[tgtId];
                if (!srcPos || !tgtPos) {
                    connectionFaces.push({ exitFace: null, entryFace: null });
                    return;
                }
                let exitFace, entryFace;
                if (Math.abs(srcPos.x - tgtPos.x) < 15 && Math.abs(srcPos.y - tgtPos.y) > 150) {
                    if (tgtPos.y > srcPos.y) {
                        exitFace = "Bottom"; entryFace = tgtPos.x > 1500 ? "Left" : "Right";
                    } else {
                        exitFace = "Top"; entryFace = tgtPos.x > 1500 ? "Left" : "Right";
                    }
                } else if (srcId === "nleads_engine" && tgtPos.y >= 1000 && tgtPos.x < 1400) {
                    exitFace = "Bottom"; entryFace = "Top";
                } else if (isVerticalBlockedSimple(srcId, tgtPos) || isVerticalBlockedNearTargetSimple(tgtId, srcPos)) {
                    const dx = tgtPos.x - srcPos.x;
                    exitFace = dx > 0 ? "Right" : "Left"; entryFace = dx > 0 ? "Left" : "Right";
                } else {
                    const dx = tgtPos.x - srcPos.x;
                    const dy = tgtPos.y - srcPos.y;
                    if (Math.abs(dx) >= Math.abs(dy)) {
                        exitFace = dx > 0 ? "Right" : "Left"; entryFace = dx > 0 ? "Left" : "Right";
                    } else {
                        exitFace = dy > 0 ? "Bottom" : "Top"; entryFace = dy > 0 ? "Top" : "Bottom";
                    }
                }
                nodePorts[srcId][exitFace].push(index);
                nodePorts[tgtId][entryFace].push(index);
                connectionFaces.push({ exitFace, entryFace });
            });

            Object.keys(nodePorts).forEach(cId => {
                ["Left", "Right", "Top", "Bottom"].forEach(face => {
                    const connIndices = nodePorts[cId][face];
                    connIndices.sort((idxA, idxB) => {
                        const connA = data.connections[idxA];
                        const connB = data.connections[idxB];
                        const otherIdA = connA.from === cId ? connA.to : connA.from;
                        const otherIdB = connB.from === cId ? connB.to : connB.from;
                        const posA = nodePositions[otherIdA] || { x: 0, y: 0 };
                        const posB = nodePositions[otherIdB] || { x: 0, y: 0 };
                        return (face === "Top" || face === "Bottom") ? (posA.x - posB.x) : (posA.y - posB.y);
                    });
                });
            });

            const preparedConnections = [];
            data.connections.forEach((conn, index) => {
                const srcId = conn.from;
                const tgtId = conn.to;
                const srcPos = nodePositions[srcId];
                const tgtPos = nodePositions[tgtId];
                if (!srcPos || !tgtPos) {
                    preparedConnections.push(null);
                    return;
                }
                const faces = connectionFaces[index];
                if (!faces || !faces.exitFace) {
                    preparedConnections.push(null);
                    return;
                }
                const exitFace = faces.exitFace;
                const entryFace = faces.entryFace;
                const srcComp = data.components.find(c => c.id === srcId) || { type: 'server' };
                const tgtComp = data.components.find(c => c.id === tgtId) || { type: 'server' };
                const srcDims = getNodeDims(srcId, srcComp.type);
                const tgtDims = getNodeDims(tgtId, tgtComp.type);
                const sx = srcPos.x, sy = srcPos.y, tx = tgtPos.x, ty = tgtPos.y;

                const outList = nodePorts[srcId][exitFace];
                const i = outList.indexOf(index);
                const K = outList.length;
                let offsetSrc;
                if (srcId === "nleads_engine" && exitFace === "Bottom") {
                    const fanningW = 95;
                    offsetSrc = (fanningW / (K + 1)) * (i + 1) - fanningW / 2 + 12;
                } else {
                    const L_src = (exitFace === "Left" || exitFace === "Right") ? srcDims.h : srcDims.w;
                    offsetSrc = (L_src / (K + 1)) * (i + 1) - L_src / 2;
                }

                let sxPort, syPort;
                if (exitFace === "Right") {
                    sxPort = sx + srcDims.w/2; syPort = sy + offsetSrc;
                } else if (exitFace === "Left") {
                    sxPort = sx - srcDims.w/2; syPort = sy + offsetSrc;
                } else if (exitFace === "Bottom") {
                    sxPort = sx + offsetSrc; syPort = sy + srcDims.h/2;
                } else {
                    sxPort = sx + offsetSrc; syPort = sy - srcDims.h/2;
                }

                const inList = nodePorts[tgtId][entryFace];
                const j = inList.indexOf(index);
                const M = inList.length;
                const L_tgt = (entryFace === "Left" || entryFace === "Right") ? tgtDims.h : tgtDims.w;
                const offsetTgt = (L_tgt / (M + 1)) * (j + 1) - L_tgt / 2;

                let txPort, tyPort;
                if (entryFace === "Right") {
                    txPort = tx + tgtDims.w/2; tyPort = ty + offsetTgt;
                } else if (entryFace === "Left") {
                    txPort = tx - tgtDims.w/2; tyPort = ty + offsetTgt;
                } else if (entryFace === "Bottom") {
                    txPort = tx + offsetTgt; tyPort = ty + tgtDims.h/2;
                } else {
                    txPort = tx + offsetTgt; tyPort = ty - tgtDims.h/2;
                }

                const direction = (exitFace === "Top" || exitFace === "Bottom") && (entryFace === "Top" || entryFace === "Bottom") ? "Vertical" : "Horizontal";
                let midX = null, midY = null;
                if (direction === "Horizontal") {
                    midX = findCleanVerticalCorridor(sxPort, syPort, txPort, tyPort, srcId, tgtId);
                } else {
                    midY = findCleanHorizontalCorridor(sxPort, syPort, txPort, tyPort, srcId, tgtId);
                }

                preparedConnections.push({
                    index, conn, sxPort, syPort, txPort, tyPort, direction, midX, midY, srcId, tgtId, offsetVal: 0
                });
            });

            const vCorridorGroups = {};
            const hCorridorGroups = {};
            preparedConnections.forEach(prep => {
                if (!prep) return;
                if (prep.direction === "Horizontal") {
                    const corrKey = Math.round(prep.midX / 10) * 10;
                    if (!vCorridorGroups[corrKey]) vCorridorGroups[corrKey] = [];
                    vCorridorGroups[corrKey].push(prep);
                } else {
                    const corrKey = Math.round(prep.midY / 10) * 10;
                    if (!hCorridorGroups[corrKey]) hCorridorGroups[corrKey] = [];
                    hCorridorGroups[corrKey].push(prep);
                }
            });

            Object.keys(vCorridorGroups).forEach(corrKey => {
                const preps = vCorridorGroups[corrKey];
                preps.sort((a, b) => (a.syPort + a.tyPort) / 2 - (b.syPort + b.tyPort) / 2);
                const N = preps.length;
                preps.forEach((prep, idx) => {
                    prep.offsetVal = idx * 12 - (N - 1) * 6;
                });
            });

            Object.keys(hCorridorGroups).forEach(corrKey => {
                const preps = hCorridorGroups[corrKey];
                preps.sort((a, b) => (a.sxPort + a.txPort) / 2 - (b.sxPort + b.txPort) / 2);
                const N = preps.length;
                preps.forEach((prep, idx) => {
                    prep.offsetVal = idx * 12 - (N - 1) * 6;
                });
            });

            let svgMarkup = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1760 1280" width="100%" height="100%" id="svg-diagram-element">
              <defs>
                <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="${themeColors.edgeColor}" />
                </marker>
                <marker id="arrow-new" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#7D3C98" />
                </marker>
              </defs>
              <g class="viewport" transform="translate(${panX},${panY}) scale(${zoom})">
            `;

            data.groups.forEach(g => {
                const bounds = groupBounds[g.id];
                if (!bounds) return;
                let dashStyle = g.style.includes('dashed') ? 'stroke-dasharray="4,4"' : '';
                let strokeColor = "#95a5a6";
                let fill = themeColors.greyFill;
                if (g.style.includes('yellow')) {
                    strokeColor = "#f1c40f"; fill = themeColors.yellowFill;
                } else if (g.style.includes('purple')) {
                    strokeColor = "#9b59b6"; fill = themeColors.purpleFill;
                } else if (g.style.includes('green')) {
                    strokeColor = "#2ecc71"; fill = themeColors.greenFill;
                } else if (g.style.includes('blue')) {
                    strokeColor = "#3498db"; fill = themeColors.blueFill;
                } else if (g.style.includes('black')) {
                    strokeColor = isDark ? "#8a9ab0" : "#333333"; fill = themeColors.blackFill;
                }
                if (["mainframe_1", "mainframe_2", "depts_mcs", "verification_grid"].includes(g.id)) {
                    fill = themeColors.whiteFill; strokeColor = isDark ? "#2e344e" : "#a0aec0";
                } else if (g.id === "service_grid") {
                    fill = isDark ? "rgba(30, 35, 53, 0.5)" : "rgba(250, 250, 250, 0.8)";
                    strokeColor = isDark ? "#2e344e" : "#cbd5e0"; dashStyle = 'stroke-dasharray="3,3"';
                }
                svgMarkup += `
                  <g class="group-container" id="grp-${g.id}">
                    <rect x="${bounds.x}" y="${bounds.y}" width="${bounds.w}" height="${bounds.h}" fill="${fill}" stroke="${strokeColor}" stroke-width="1.5" ${dashStyle} rx="6" ry="6"/>
                    <text x="${bounds.x + 15}" y="${bounds.y + 20}" class="zone-title" font-family="'Inter', sans-serif" font-size="12px" font-weight="bold" fill="${themeColors.groupTitle}" text-transform="uppercase" letter-spacing="0.5px">${g.name}</text>
                  </g>
                `;
            });

            data.components.forEach(comp => {
                const pos = nodePositions[comp.id];
                if (!pos) return;
                const dims = getNodeDims(comp.id, comp.type);
                const xLeft = pos.x - dims.w / 2;
                const yTop = pos.y - dims.h / 2;
                let stroke = isDark ? "#8a9ab0" : "#333333";
                let fill = themeColors.whiteFill;
                let strokeWidth = "1.5";
                if (comp.id === "nleads_engine") {
                    fill = isDark ? "rgba(232, 244, 252, 0.15)" : "#e8f4fc"; stroke = "#7d3c98"; strokeWidth = "2.5";
                } else if (["confluent_kafka", "e_kafka"].includes(comp.id)) {
                    stroke = "#7d3c98"; strokeWidth = "2";
                } else if (comp.lifecycle_status === 'updated' || comp.type === 'gateway') {
                    fill = isDark ? "rgba(255, 234, 167, 0.15)" : "#ffeaa7";
                    stroke = comp.lifecycle_status === 'updated' ? "#0984e3" : (isDark ? "#8a9ab0" : "#333333");
                    strokeWidth = comp.lifecycle_status === 'updated' ? "2" : "1.5";
                } else if (comp.lifecycle_status === 'new') {
                    stroke = "#7d3c98"; strokeWidth = "2";
                }
                svgMarkup += `<g class="node-group" id="${comp.id}" style="cursor:pointer;" data-status="${comp.lifecycle_status}">`;
                if (comp.type === 'mainframe') {
                    svgMarkup += `
                      <rect x="${xLeft}" y="${yTop + 6}" width="${dims.w}" height="${dims.h - 6}" fill="${fill}" stroke="${stroke}" stroke-width="${strokeWidth}" rx="2" ry="2"/>
                      <ellipse cx="${pos.x}" cy="${yTop + 6}" rx="${dims.w/2}" ry="6" fill="${fill}" stroke="${stroke}" stroke-width="${strokeWidth}"/>
                      <path d="M ${xLeft} ${pos.y + dims.h/2 - 6} A ${dims.w/2} 6 0 0 0 ${xLeft + dims.w} ${pos.y + dims.h/2 - 6}" fill="none" stroke="${stroke}" stroke-width="${strokeWidth}"/>
                    `;
                } else {
                    svgMarkup += `
                      <rect x="${xLeft}" y="${yTop}" width="${dims.w}" height="${dims.h}" fill="${fill}" stroke="${stroke}" stroke-width="${strokeWidth}" rx="4" ry="4"/>
                    `;
                }
                const nameParts = comp.name.split(' ');
                if (nameParts.length > 1 && comp.name.length > 12) {
                    const yOffset = nameParts.length === 2 ? -4 : -8;
                    nameParts.slice(0, 3).forEach((part, i) => {
                        svgMarkup += `
                          <text x="${pos.x}" y="${pos.y + yOffset + (i * 12) + 4}" class="node-text" font-family="'Inter', sans-serif" font-size="11px" font-weight="bold" fill="${themeColors.nodeText}" text-anchor="middle">${part}</text>
                        `;
                    });
                } else {
                    svgMarkup += `
                      <text x="${pos.x}" y="${pos.y + 4}" class="node-text" font-family="'Inter', sans-serif" font-size="11px" font-weight="bold" fill="${themeColors.nodeText}" text-anchor="middle">${comp.name}</text>
                    `;
                }
                svgMarkup += `</g>`;
            });

            preparedConnections.forEach((prep, index) => {
                if (!prep) return;
                const conn = prep.conn;
                const isNew = conn.status === 'new';
                const edgeColor = isNew ? "#7d3c98" : themeColors.edgeColor;
                const marker = isNew ? "url(#arrow-new)" : "url(#arrow)";
                let pathD = "";
                let labelX = 0, labelY = 0;
                
                if (prep.direction === "Horizontal") {
                    if (Math.abs(prep.syPort - prep.tyPort) < 15 && !isHorizontalSegmentBlocked(prep.syPort, prep.sxPort, prep.txPort, [prep.srcId, prep.tgtId])) {
                        pathD = `M ${prep.sxPort} ${prep.syPort} L ${prep.txPort} ${prep.tyPort}`;
                        labelX = (prep.sxPort + prep.txPort) / 2; labelY = prep.syPort - 6;
                    } else {
                        const staggeredMidX = prep.midX + prep.offsetVal;
                        pathD = `M ${prep.sxPort} ${prep.syPort} L ${staggeredMidX} ${prep.syPort} L ${staggeredMidX} ${prep.tyPort} L ${prep.txPort} ${prep.tyPort}`;
                        labelX = staggeredMidX; labelY = (prep.syPort + prep.tyPort) / 2;
                    }
                } else {
                    if (Math.abs(prep.sxPort - prep.txPort) < 15 && !isVerticalSegmentBlocked(prep.sxPort, prep.syPort, prep.tyPort, [prep.srcId, prep.tgtId])) {
                        pathD = `M ${prep.sxPort} ${prep.syPort} L ${prep.txPort} ${prep.tyPort}`;
                        labelX = prep.sxPort + 6; labelY = (prep.syPort + prep.tyPort) / 2;
                    } else {
                        const staggeredMidY = prep.midY + prep.offsetVal;
                        pathD = `M ${prep.sxPort} ${prep.syPort} L ${prep.sxPort} ${staggeredMidY} L ${prep.txPort} ${staggeredMidY} L ${prep.txPort} ${prep.tyPort}`;
                        labelX = (prep.sxPort + prep.txPort) / 2; labelY = staggeredMidY - 6;
                    }
                }
                
                svgMarkup += `
                  <g class="edge-group" id="e-${index}" style="cursor:pointer;" data-status="${conn.status || 'existing'}">
                    <path d="${pathD}" fill="none" stroke="${edgeColor}" stroke-width="1.8" marker-end="${marker}"/>
                `;
                if (conn.protocol) {
                    const labelW = conn.protocol.length * 6 + 10;
                    svgMarkup += `
                      <g class="proto-label" transform="translate(${labelX}, ${labelY})">
                        <rect x="${-labelW/2}" y="-7" width="${labelW}" height="13" fill="${themeColors.labelBg}" stroke="${themeColors.labelBorder}" stroke-width="0.7" rx="2" ry="2"/>
                        <text x="0" y="2" class="conn-text" font-family="'Inter', sans-serif" font-size="8px" font-weight="bold" fill="${edgeColor}" text-anchor="middle">${conn.protocol}</text>
                      </g>
                    `;
                }
                svgMarkup += `</g>`;
            });

            svgMarkup += `</g></svg>`;
            
            document.getElementById('cy').innerHTML = svgMarkup;
        }

        function highlightSVGElement(idOrIndex, isEdge) {
            clearHighlights();
            const svg = document.getElementById('svg-diagram-element');
            if (!svg) return;
            
            selectedElementId = idOrIndex;
            isSelectedEdge = isEdge;

            const allGroups = svg.querySelectorAll('.node-group, .edge-group, .group-container');
            allGroups.forEach(el => el.classList.add('svg-faded'));

            if (isEdge) {
                const connIndex = idOrIndex;
                const conn = data.connections[connIndex];
                const edgeEl = svg.getElementById(`e-${connIndex}`);
                if (edgeEl) edgeEl.classList.remove('svg-faded');
                const srcNode = svg.getElementById(conn.from);
                const tgtNode = svg.getElementById(conn.to);
                if (srcNode) srcNode.classList.remove('svg-faded');
                if (tgtNode) tgtNode.classList.remove('svg-faded');
            } else {
                const nodeEl = svg.getElementById(idOrIndex);
                if (nodeEl) {
                    nodeEl.classList.remove('svg-faded');
                    nodeEl.classList.add('svg-highlighted');
                }
                data.connections.forEach((conn, index) => {
                    if (conn.from === idOrIndex || conn.to === idOrIndex) {
                        const edgeEl = svg.getElementById(`e-${index}`);
                        if (edgeEl) edgeEl.classList.remove('svg-faded');
                        const otherNodeId = conn.from === idOrIndex ? conn.to : conn.from;
                        const otherNode = svg.getElementById(otherNodeId);
                        if (otherNode) otherNode.classList.remove('svg-faded');
                    }
                });
            }
        }

        function clearHighlights() {
            selectedElementId = null;
            const svg = document.getElementById('svg-diagram-element');
            if (!svg) return;
            const all = svg.querySelectorAll('.node-group, .edge-group, .group-container');
            all.forEach(el => {
                el.classList.remove('svg-faded');
                el.classList.remove('svg-highlighted');
            });
        }

        function showDetails(elementData, isEdge) {
            const container = document.getElementById('inspector-content');
            let html = '<div style="display:flex; flex-direction:column; gap:16px; overflow-y:auto; flex:1;">';
            if (isEdge) {
                html += `
                    <div class="meta-property">
                        <div class="meta-label">Type</div>
                        <div class="meta-value" style="font-weight:700; color:var(--acme-purple-light);">Connection Flow</div>
                    </div>
                    <div class="meta-property">
                        <div class="meta-label">Protocol</div>
                        <div class="meta-value"><span class="meta-badge" style="background-color:rgba(125,60,152,0.1); color:var(--acme-purple-light);">${elementData.protocol || 'REST'}</span></div>
                    </div>
                    <div class="meta-property">
                        <div class="meta-label">From System</div>
                        <div class="meta-value" style="font-family:var(--font-mono); font-size:13px; cursor:pointer; color:var(--acme-purple-light);" onclick="selectNodeById('${elementData.from}')">${elementData.from}</div>
                    </div>
                    <div class="meta-property">
                        <div class="meta-label">To System</div>
                        <div class="meta-value" style="font-family:var(--font-mono); font-size:13px; cursor:pointer; color:var(--acme-purple-light);" onclick="selectNodeById('${elementData.to}')">${elementData.to}</div>
                    </div>
                    <div class="meta-property">
                        <div class="meta-label">Status</div>
                        <div class="meta-value"><span class="meta-badge badge-${elementData.status}">${elementData.status}</span></div>
                    </div>
                `;
            } else {
                html += `
                    <div class="meta-property">
                        <div class="meta-label">Type</div>
                        <div class="meta-value" style="font-weight:700; color:var(--acme-purple-light);">${elementData.type.toUpperCase()}</div>
                    </div>
                    <div class="meta-property">
                        <div class="meta-label">Component Name</div>
                        <div class="meta-value" style="font-size:16px; font-weight:700;">${elementData.name}</div>
                    </div>
                    <div class="meta-property">
                        <div class="meta-label">Component ID</div>
                        <div class="meta-value" style="font-family:var(--font-mono); font-size:12px; color:var(--text-muted);">${elementData.id}</div>
                    </div>
                    <div class="meta-property">
                        <div class="meta-label">Security Group / Zone</div>
                        <div class="meta-value" style="font-family:var(--font-mono); font-size:12px;">${parentOverrides[elementData.id] || elementData.group || 'None'}</div>
                    </div>
                    <div class="meta-property">
                        <div class="meta-label">Lifecycle Status</div>
                        <div class="meta-value"><span class="meta-badge badge-${elementData.lifecycle_status}">${elementData.lifecycle_status}</span></div>
                    </div>
                `;
            }
            html += '</div>';
            container.innerHTML = html;
        }

        function selectNodeById(nodeId) {
            const node = data.components.find(c => c.id === nodeId);
            if (node) {
                showDetails(node, false);
                highlightSVGElement(nodeId, false);
                const pos = nodePositions[nodeId];
                if (pos) {
                    const container = document.getElementById('cy');
                    zoom = 1.0;
                    panX = container.clientWidth / 2 - pos.x;
                    panY = container.clientHeight / 2 - pos.y;
                    applyTransform();
                }
            }
        }

        function clearDetails() {
            document.getElementById('inspector-content').innerHTML = `
                <div class="empty-inspector">
                    <div class="empty-icon">🛈</div>
                    <p>Click on any component or connection in the diagram to inspect its metadata.</p>
                </div>
            `;
        }

        function handleSearch() {
            const query = document.getElementById('search-box').value.trim().toLowerCase();
            if (query === '') {
                clearHighlights();
                return;
            }
            const matchedNode = data.components.find(c => c.name.toLowerCase().includes(query) || c.id.toLowerCase().includes(query));
            if (matchedNode) {
                selectNodeById(matchedNode.id);
            } else {
                const matchedConn = data.connections.find(c => (c.protocol && c.protocol.toLowerCase().includes(query)) || c.from.toLowerCase().includes(query) || c.to.toLowerCase().includes(query));
                if (matchedConn) {
                    const index = data.connections.indexOf(matchedConn);
                    showDetails(matchedConn, true);
                    highlightSVGElement(index, true);
                }
            }
        }

        function applyFilters() {
            const chkUnchanged = document.getElementById('chk-unchanged').checked;
            const chkUpdated = document.getElementById('chk-updated').checked;
            const chkNew = document.getElementById('chk-new').checked;
            const svg = document.getElementById('svg-diagram-element');
            if (!svg) return;
            
            data.components.forEach(c => {
                const el = svg.getElementById(c.id);
                if (!el) return;
                const status = c.lifecycle_status;
                let show = true;
                if (status === 'unchanged' && !chkUnchanged) show = false;
                else if (status === 'updated' && !chkUpdated) show = false;
                else if (status === 'new' && !chkNew) show = false;
                el.style.display = show ? '' : 'none';
            });
            
            data.connections.forEach((conn, index) => {
                const el = svg.getElementById(`e-${index}`);
                if (!el) return;
                const srcEl = svg.getElementById(conn.from);
                const tgtEl = svg.getElementById(conn.to);
                if (srcEl && tgtEl && (srcEl.style.display === 'none' || tgtEl.style.display === 'none')) {
                    el.style.display = 'none';
                } else {
                    el.style.display = '';
                }
            });
        }

        function applyTransform() {
            const viewport = document.querySelector('g.viewport');
            if (viewport) {
                viewport.setAttribute('transform', `translate(${panX}, ${panY}) scale(${zoom})`);
            }
        }

        function resetCamera() {
            const container = document.getElementById('cy');
            zoom = Math.min(container.clientWidth / 1760, container.clientHeight / 1280) * 0.95;
            panX = (container.clientWidth - 1760 * zoom) / 2;
            panY = (container.clientHeight - 1280 * zoom) / 2;
            applyTransform();
        }

        function exportSVG() {
            const svg = document.getElementById('svg-diagram-element').cloneNode(true);
            const viewport = svg.querySelector('g.viewport');
            viewport.removeAttribute('transform');
            const svgString = new XMLSerializer().serializeToString(svg);
            const blob = new Blob([svgString], {type: 'image/svg+xml;charset=utf-8'});
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'acme_integration_flow.svg';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        function exportPNG() {
            const svg = document.getElementById('svg-diagram-element');
            const svgString = new XMLSerializer().serializeToString(svg);
            const svgBlob = new Blob([svgString], {type: 'image/svg+xml;charset=utf-8'});
            const URL = window.URL || window.webkitURL || window;
            const blobURL = URL.createObjectURL(svgBlob);
            const image = new Image();
            image.onload = () => {
                const canvas = document.createElement('canvas');
                canvas.width = 1760 * 2;
                canvas.height = 1280 * 2;
                const context = canvas.getContext('2d');
                context.fillStyle = document.body.getAttribute('data-theme') === 'dark' ? '#0f111a' : '#f4f6f9';
                context.fillRect(0, 0, canvas.width, canvas.height);
                context.scale(2, 2);
                context.drawImage(image, 0, 0);
                
                const png = canvas.toDataURL('image/png');
                const link = document.createElement('a');
                link.href = png;
                link.download = 'acme_integration_flow.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            };
            image.src = blobURL;
        }

        window.addEventListener('DOMContentLoaded', () => {
            data = loadDiagramData();
            document.getElementById('dashboard-title').textContent = data.title || "Acme Integration Architecture";
            renderDiagram();
            resetCamera();

            const container = document.getElementById('cy');
            container.addEventListener('click', function(e) {
                const nodeGroup = e.target.closest('.node-group');
                const edgeGroup = e.target.closest('.edge-group');
                if (nodeGroup) {
                    const cId = nodeGroup.id;
                    const comp = data.components.find(c => c.id === cId);
                    showDetails(comp, false);
                    highlightSVGElement(cId, false);
                } else if (edgeGroup) {
                    const index = parseInt(edgeGroup.id.replace('e-', ''));
                    const conn = data.connections[index];
                    showDetails(conn, true);
                    highlightSVGElement(index, true);
                } else if (e.target === container || e.target.tagName === 'svg' || e.target.closest('.group-container')) {
                    clearDetails();
                    clearHighlights();
                }
            });

            container.addEventListener('mousedown', function(e) {
                const targetTag = e.target.tagName;
                if (targetTag === 'svg' || e.target.closest('.group-container') || e.target.classList.contains('canvas-container') || e.target.id === 'cy') {
                    isPanning = true;
                    startX = e.clientX - panX;
                    startY = e.clientY - panY;
                    container.style.cursor = 'grabbing';
                }
            });

            window.addEventListener('mousemove', function(e) {
                if (isPanning) {
                    panX = e.clientX - startX;
                    panY = e.clientY - startY;
                    applyTransform();
                }
            });

            window.addEventListener('mouseup', function() {
                isPanning = false;
                container.style.cursor = 'default';
            });

            container.addEventListener('wheel', function(e) {
                e.preventDefault();
                const zoomFactor = 1.1;
                const rect = container.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;
                const prevZoom = zoom;
                if (e.deltaY < 0) {
                    zoom *= zoomFactor;
                } else {
                    zoom /= zoomFactor;
                }
                zoom = Math.max(0.1, Math.min(zoom, 10));
                panX = mouseX - (mouseX - panX) * (zoom / prevZoom);
                panY = mouseY - (mouseY - panY) * (zoom / prevZoom);
                applyTransform();
            }, { passive: false });
        });

        function runLayout() {
            resetCamera();
            clearDetails();
            clearHighlights();
        }

        function getSampleData() {
            return {
                title: "Sample Enterprise Flow Diagram",
                groups: [
                    { id: "techx_aws", name: "TechX AWS" }
                ],
                components: [
                    { id: "acme_connect", name: "Acme Connect", group: "techx_aws", type: "channel", lifecycle_status: "unchanged" }
                ],
                connections: []
            };
        }
"""

# 2. Write update logic
# Locate the App Logic script tag block in template.html and replace it
new_template_content = re.sub(pattern, f'\\1\n{js_code}\n\\2', template_content, flags=re.DOTALL)

with open(template_path, 'w') as f:
    f.write(new_template_content)

print("Updated template.html successfully.")

# 3. Compile viewer.html from updated template
json_str = json.dumps(data, indent=2)
viewer_content = new_template_content.replace(
    '/* DIAGRAM_DATA_JSON_PLACEHOLDER */',
    json_str
)

with open(viewer_path, 'w') as f:
    f.write(viewer_content)

print("Updated nleads_viewer.html successfully.")

