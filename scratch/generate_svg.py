import os

output_svg = "/Users/kongkittisan/Documents/workspaces/diagram-agent/generated_diagrams/nleads_real_diagram.svg"

# Hardcoded data parsed from nleads_metadata.yaml
data = {
  "title": "NLEADS - Real-time Integration Architecture",
  "groups": [
    { "id": "techx_aws", "name": "TechX AWS (Bank)", "style": "yellow dashed border, light background" },
    { "id": "acme_aws", "name": "Acme AWS", "style": "yellow dashed border, light background" },
    { "id": "acme_azure", "name": "Acme Azure", "style": "blue solid border, light background" },
    { "id": "acme_staff", "name": "Acme Staff (Internal Access)", "style": "black solid border, light grey background" },
    { "id": "on_premise_upper", "name": "On-Premise", "style": "grey solid border, light grey background" },
    { "id": "on_premise_lower", "name": "On-Premise", "style": "grey solid border, light grey background" },
    { "id": "partner_3rd_party", "name": "Partner / 3rd Party", "style": "purple solid border, light background" },
    { "id": "saas_cloud", "name": "SaaS Cloud", "style": "purple solid border, light background" },
    { "id": "acme_huawei", "name": "Acme Huawei", "style": "green solid border, light background" },
    { "id": "mainframe_1", "name": "Mainframe", "style": "thin black border, white background", "parent": "on_premise_upper" },
    { "id": "mainframe_2", "name": "Mainframe", "style": "thin black border, white background", "parent": "on_premise_upper" },
    { "id": "service_grid", "name": "Service Grid", "style": "no border, clean layout", "parent": "on_premise_upper" },
    { "id": "depts_mcs", "name": "Depts / MCS", "style": "thin black border, white background", "parent": "on_premise_upper" },
    { "id": "verification_grid", "name": "Verification Grid", "style": "thin grey border, white background", "parent": "on_premise_upper" }
  ],
  "components": [
    { "id": "acme_connect", "name": "Acme Connect", "group": "techx_aws", "lifecycle_status": "unchanged", "type": "channel" },
    { "id": "acme_one", "name": "Acme ONE", "group": "acme_aws", "lifecycle_status": "unchanged", "type": "channel" },
    { "id": "ast_tool", "name": "Auto Sales Tools (AST)", "group": "acme_azure", "lifecycle_status": "unchanged", "type": "channel" },
    { "id": "call_center", "name": "Call Center", "group": "acme_staff", "lifecycle_status": "unchanged", "type": "channel" },
    { "id": "eapi_onprem_1", "name": "EAPI", "group": "on_premise_upper", "lifecycle_status": "updated", "type": "gateway" },
    { "id": "eapi_onprem_2", "name": "EAPI", "group": "on_premise_upper", "lifecycle_status": "updated", "type": "gateway" },
    { "id": "mq_broker_1", "name": "MQ", "group": "on_premise_upper", "lifecycle_status": "unchanged", "type": "gateway" },
    { "id": "mq_broker_2", "name": "MQ", "group": "on_premise_upper", "lifecycle_status": "unchanged", "type": "gateway" },
    { "id": "als", "name": "ALS", "group": "mainframe_1", "lifecycle_status": "unchanged", "type": "mainframe" },
    { "id": "mg_cheque", "name": "MG CHEQUE", "group": "mainframe_1", "lifecycle_status": "unchanged", "type": "mainframe" },
    { "id": "gn", "name": "GN", "group": "mainframe_1", "lifecycle_status": "unchanged", "type": "mainframe" },
    { "id": "rm", "name": "RM", "group": "mainframe_2", "lifecycle_status": "unchanged", "type": "mainframe" },
    { "id": "im_st", "name": "IM/ST", "group": "mainframe_2", "lifecycle_status": "unchanged", "type": "mainframe" },
    { "id": "faat", "name": "FAAT", "group": "mainframe_2", "lifecycle_status": "unchanged", "type": "mainframe" },
    { "id": "estm", "name": "ESTM", "group": "service_grid", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "lhs", "name": "LHS", "group": "service_grid", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "ncb", "name": "NCB", "group": "service_grid", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "ncbos", "name": "NCBOS", "group": "service_grid", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "nss", "name": "NSS", "group": "service_grid", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "sfwh", "name": "SFWH (Safewatch)", "group": "service_grid", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "ref_data", "name": "Reference Data", "group": "service_grid", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "svaf", "name": "SVAF", "group": "service_grid", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "watch_list", "name": "Watch List", "group": "service_grid", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "actm", "name": "ACTM", "group": "service_grid", "lifecycle_status": "new", "type": "server" },
    { "id": "enlite", "name": "ENLITE", "group": "service_grid", "lifecycle_status": "new", "type": "server" },
    { "id": "sftp_server", "name": "SFTP Server", "group": "on_premise_lower", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "dmip_nleads", "name": "DMIP-NLEADS", "group": "on_premise_lower", "lifecycle_status": "updated", "type": "server" },
    { "id": "ecm_autoloan", "name": "ECM-AUTOLOAN + NLEADS", "group": "on_premise_lower", "lifecycle_status": "updated", "type": "server" },
    { "id": "smtp_custard", "name": "SMTP Server CUSTARD", "group": "on_premise_lower", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "smtp_zimba", "name": "SMTP Server ZIMBA", "group": "on_premise_lower", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "ecm_unsecured", "name": "ECM-UNSECURED", "group": "depts_mcs", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "ecm_lead", "name": "ECM-LEAD", "group": "depts_mcs", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "fos", "name": "FOS", "group": "depts_mcs", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "nleads_engine", "name": "NLEADS", "group": "acme_azure", "lifecycle_status": "new", "type": "core_engine" },
    { "id": "eapi_azure", "name": "EAPI", "group": "acme_azure", "lifecycle_status": "updated", "type": "gateway" },
    { "id": "confluent_kafka", "name": "Confluent Kafka", "group": "acme_azure", "lifecycle_status": "updated", "type": "gateway" },
    { "id": "e_kafka", "name": "E-Kafka", "group": "acme_azure", "lifecycle_status": "updated", "type": "gateway" },
    { "id": "ade", "name": "ADE", "group": "verification_grid", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "emv", "name": "EMV", "group": "verification_grid", "lifecycle_status": "unchanged", "type": "server" },
    { "id": "nmsx", "name": "NMSX (Replace Detica)", "group": "verification_grid", "lifecycle_status": "new", "type": "server" },
    { "id": "partner_eco", "name": "Partner Eco", "group": "techx_aws", "lifecycle_status": "unchanged", "type": "external_partner" },
    { "id": "mitsubishi", "name": "Mitsubishi", "group": "partner_3rd_party", "lifecycle_status": "unchanged", "type": "external_partner" },
    { "id": "deves", "name": "Deves", "group": "partner_3rd_party", "lifecycle_status": "unchanged", "type": "external_partner" },
    { "id": "omakase", "name": "Omakase Car", "group": "partner_3rd_party", "lifecycle_status": "unchanged", "type": "external_partner" },
    { "id": "dlt", "name": "DLT", "group": "partner_3rd_party", "lifecycle_status": "unchanged", "type": "external_partner" },
    { "id": "icore", "name": "iCore", "group": "acme_huawei", "lifecycle_status": "unchanged", "type": "external_partner" },
    { "id": "payroll", "name": "BIPO Acme Payroll", "group": "saas_cloud", "lifecycle_status": "unchanged", "type": "external_partner" }
  ],
  "connections": [
    { "from": "acme_connect", "to": "eapi_onprem_1", "protocol": "REST", "status": "existing" },
    { "from": "acme_one", "to": "eapi_onprem_2", "protocol": "REST", "status": "existing" },
    { "from": "eapi_onprem_1", "to": "nleads_engine", "protocol": "REST", "status": "existing" },
    { "from": "eapi_onprem_2", "to": "nleads_engine", "protocol": "REST", "status": "existing" },
    { "from": "ast_tool", "to": "eapi_azure", "protocol": "REST", "status": "existing" },
    { "from": "ast_tool", "to": "nleads_engine", "protocol": "REST", "status": "existing" },
    { "from": "call_center", "to": "eapi_azure", "protocol": "REST", "status": "existing" },
    { "from": "eapi_onprem_1", "to": "mq_broker_1", "protocol": "XML", "status": "existing" },
    { "from": "mq_broker_1", "to": "acme_connect", "protocol": "MQ/XML", "status": "existing" },
    { "from": "nleads_engine", "to": "mq_broker_1", "protocol": "XML", "status": "existing" },
    { "from": "mq_broker_1", "to": "als", "protocol": "MQ", "status": "existing" },
    { "from": "nleads_engine", "to": "mq_broker_2", "protocol": "XML", "status": "existing" },
    { "from": "mq_broker_2", "to": "rm", "protocol": "MQ", "status": "existing" },
    { "from": "nleads_engine", "to": "confluent_kafka", "protocol": "Publish", "status": "new" },
    { "from": "nleads_engine", "to": "e_kafka", "protocol": "Publish", "status": "new" },
    { "from": "confluent_kafka", "to": "ecm_autoloan", "protocol": "Subscribe", "status": "new" },
    { "from": "e_kafka", "to": "ecm_autoloan", "protocol": "Subscribe", "status": "new" },
    { "from": "nleads_engine", "to": "sftp_server", "protocol": "SFTP", "status": "existing" },
    { "from": "nleads_engine", "to": "smtp_custard", "protocol": "SMTP", "status": "existing" },
    { "from": "nleads_engine", "to": "smtp_zimba", "protocol": "SMTP", "status": "existing" },
    { "from": "nleads_engine", "to": "dmip_nleads", "protocol": "REST", "status": "existing" },
    { "from": "nleads_engine", "to": "ecm_unsecured", "protocol": "SOAP", "status": "new" },
    { "from": "nleads_engine", "to": "ecm_lead", "protocol": "SOAP", "status": "new" },
    { "from": "nleads_engine", "to": "fos", "protocol": "SOAP", "status": "new" },
    { "from": "nleads_engine", "to": "eapi_azure", "protocol": "REST", "status": "existing" },
    { "from": "eapi_azure", "to": "ade", "protocol": "REST", "status": "existing" },
    { "from": "eapi_azure", "to": "emv", "protocol": "REST", "status": "existing" },
    { "from": "eapi_azure", "to": "nmsx", "protocol": "REST", "status": "existing" },
    { "from": "nleads_engine", "to": "partner_eco", "protocol": "REST", "status": "existing" },
    { "from": "nleads_engine", "to": "mitsubishi", "protocol": "REST", "status": "existing" },
    { "from": "nleads_engine", "to": "deves", "protocol": "REST", "status": "existing" },
    { "from": "nleads_engine", "to": "omakase", "protocol": "REST", "status": "existing" },
    { "from": "nleads_engine", "to": "dlt", "protocol": "REST", "status": "existing" },
    { "from": "nleads_engine", "to": "icore", "protocol": "XML", "status": "existing" },
    { "from": "nleads_engine", "to": "payroll", "protocol": "REST", "status": "existing" }
  ]
}

comp_by_id = {c['id']: c for c in data.get('components', [])}

# 1. Preset coordinates with spacing margins
node_positions = {
    # --- ROW 1 (Channels & Clients) ---
    "acme_connect": {"x": 150, "y": 140},
    "partner_eco": {"x": 370, "y": 140},
    "acme_one": {"x": 590, "y": 140},
    "ast_tool": {"x": 920, "y": 140},
    "call_center": {"x": 1470, "y": 140},

    # --- ROW 2 (Gateways & On-Premise Upper) ---
    "eapi_onprem_1": {"x": 480, "y": 330},
    "eapi_onprem_2": {"x": 700, "y": 330},
    "mq_broker_1": {"x": 480, "y": 470},
    "nleads_engine": {"x": 920, "y": 470}, # Center Engine
    "mq_broker_2": {"x": 1360, "y": 470},
    "eapi_azure": {"x": 1360, "y": 330}, # Right EAPI

    # Mainframe 1 (Left Stack) - Perfectly aligned at x=150
    "als": {"x": 150, "y": 340},
    "mg_cheque": {"x": 150, "y": 430},
    "gn": {"x": 150, "y": 520},

    # Mainframe 2 (Right Stack) - Perfectly aligned at x=1580
    "rm": {"x": 1580, "y": 340},
    "im_st": {"x": 1580, "y": 430},
    "faat": {"x": 1580, "y": 520},

    # Service Grid (Bottom Left)
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

    # Depts / MCS (Bottom Right) - Aligned at x=1580
    "ecm_unsecured": {"x": 1580, "y": 720},
    "ecm_lead": {"x": 1580, "y": 810},
    "fos": {"x": 1580, "y": 900},

    # Verification Grid (Middle Right) - Aligned at x=1360
    "ade": {"x": 1360, "y": 580},
    "emv": {"x": 1360, "y": 670},
    "nmsx": {"x": 1360, "y": 760},

    # Middle Kafkas - Aligned at x=1140
    "confluent_kafka": {"x": 1140, "y": 630},
    "e_kafka": {"x": 1140, "y": 720},

    # --- ROW 3 (On-Premise Lower) ---
    "sftp_server": {"x": 150, "y": 1080},
    "smtp_custard": {"x": 370, "y": 1080},
    "smtp_zimba": {"x": 590, "y": 1080},
    "dmip_nleads": {"x": 810, "y": 1080},
    "ecm_autoloan": {"x": 810, "y": 1170},

    # Partners
    "mitsubishi": {"x": 1030, "y": 1080},
    "deves": {"x": 1250, "y": 1080},
    "omakase": {"x": 1140, "y": 1170},
    "dlt": {"x": 1360, "y": 1170},

    # SaaS Cloud
    "payroll": {"x": 1470, "y": 1080},

    # Acme Huawei - Perfectly aligned with right mainframe column at x=1580
    "icore": {"x": 1580, "y": 1080}
}

# Node parent overrides to align them inside On-Premise container visually
parent_overrides = {
    "nleads_engine": "on_premise_upper",
    "eapi_azure": "on_premise_upper",
    "confluent_kafka": "on_premise_upper",
    "e_kafka": "on_premise_upper"
}

# Dimensions configuration
def get_node_dims(node_id, node_type):
    if node_id == "nleads_engine":
        return 145, 65
    elif node_type == "mainframe":
        return 130, 42
    else:
        return 125, 46

# Dynamic Calculation of Group Boundaries
groups_children = {}
for comp in data.get('components', []):
    c_id = comp['id']
    group_id = parent_overrides.get(c_id, comp.get('group'))
    if group_id:
        if group_id not in groups_children:
            groups_children[group_id] = []
        groups_children[group_id].append(c_id)

group_bounds = {}
group_definitions = {g['id']: g for g in data.get('groups', [])}

for g_id, children in groups_children.items():
    xs, ys = [], []
    for c_id in children:
        pos = node_positions.get(c_id)
        if pos:
            w, h = get_node_dims(c_id, next((c['type'] for c in data['components'] if c['id'] == c_id), 'server'))
            xs.extend([pos['x'] - w/2, pos['x'] + w/2])
            ys.extend([pos['y'] - h/2, pos['y'] + h/2])
    if xs and ys:
        pad_x, pad_y = 35, 45
        group_bounds[g_id] = {
            "x": min(xs) - pad_x,
            "y": min(ys) - pad_y,
            "w": (max(xs) - min(xs)) + (2 * pad_x),
            "h": (max(ys) - min(ys)) + (2 * pad_y)
        }

for g_id, g in group_definitions.items():
    parent_id = g.get('parent')
    if parent_id and g_id in group_bounds:
        p_bounds = group_bounds.setdefault(parent_id, {"x": 9999, "y": 9999, "w": 0, "h": 0})
        c_bounds = group_bounds[g_id]
        
        min_x = min(p_bounds["x"], c_bounds["x"]) if p_bounds["x"] != 9999 else c_bounds["x"]
        min_y = min(p_bounds["y"], c_bounds["y"]) if p_bounds["y"] != 9999 else c_bounds["y"]
        
        p_max_x = p_bounds["x"] + p_bounds["w"] if p_bounds["w"] > 0 else -9999
        c_max_x = c_bounds["x"] + c_bounds["w"]
        max_x = max(p_max_x, c_max_x)
        
        p_max_y = p_bounds["y"] + p_bounds["h"] if p_bounds["h"] > 0 else -9999
        c_max_y = c_bounds["y"] + c_bounds["h"]
        max_y = max(p_max_y, c_max_y)
        
        p_bounds["x"] = min_x - 10
        p_bounds["y"] = min_y - 10
        p_bounds["w"] = (max_x - min_x) + 20
        p_bounds["h"] = (max_y - min_y) + 20

# Helper to check if a vertical line segment is blocked by any node
def is_vertical_segment_blocked(x, y_min, y_max, exclude_ids=None):
    margin_x = 10
    margin_y = 5
    y_start, y_end = min(y_min, y_max), max(y_min, y_max)
    for c_id, pos in node_positions.items():
        if exclude_ids and c_id in exclude_ids:
            continue
        comp = comp_by_id.get(c_id)
        if not comp:
            continue
        w, h = get_node_dims(c_id, comp['type'])
        comp_x_min = pos['x'] - w/2 - margin_x
        comp_x_max = pos['x'] + w/2 + margin_x
        comp_y_min = pos['y'] - h/2 - margin_y
        comp_y_max = pos['y'] + h/2 + margin_y
        
        if comp_x_min <= x <= comp_x_max:
            if max(y_start, comp_y_min) <= min(y_end, comp_y_max):
                return True
    return False

# Helper to check if a horizontal line segment is blocked by any node
def is_horizontal_segment_blocked(y, x_min, x_max, exclude_ids=None):
    margin_x = 5
    margin_y = 10
    x_start, x_end = min(x_min, x_max), max(x_min, x_max)
    for c_id, pos in node_positions.items():
        if exclude_ids and c_id in exclude_ids:
            continue
        comp = comp_by_id.get(c_id)
        if not comp:
            continue
        w, h = get_node_dims(c_id, comp['type'])
        comp_x_min = pos['x'] - w/2 - margin_x
        comp_x_max = pos['x'] + w/2 + margin_x
        comp_y_min = pos['y'] - h/2 - margin_y
        comp_y_max = pos['y'] + h/2 + margin_y
        
        if comp_y_min <= y <= comp_y_max:
            if max(x_start, comp_x_min) <= min(x_end, comp_x_max):
                return True
    return False

# Helper to find a clean vertical corridor
def find_clean_vertical_corridor(sx_port, sy_port, tx_port, ty_port, src_id, tgt_id):
    candidates = [
        (sx_port + tx_port) / 2,
        260, 450, 535, 645, 755, 880, 920, 1005, 1255, 1430, 1525
    ]
    
    best_x = None
    min_dist = 999999
    
    for x in candidates:
        if is_vertical_segment_blocked(x, sy_port, ty_port, exclude_ids=[src_id, tgt_id]):
            continue
        if is_horizontal_segment_blocked(sy_port, sx_port, x, exclude_ids=[src_id, tgt_id]):
            continue
        if is_horizontal_segment_blocked(ty_port, x, tx_port, exclude_ids=[src_id, tgt_id]):
            continue
            
        midpoint = (sx_port + tx_port) / 2
        dist = abs(x - midpoint)
        
        x_min, x_max = min(sx_port, tx_port), max(sx_port, tx_port)
        if not (x_min - 5 <= x <= x_max + 5):
            dist += 300
            
        if dist < min_dist:
            min_dist = dist
            best_x = x
            
    if best_x is not None:
        return best_x
    return (sx_port + tx_port) / 2

# Helper to find a clean horizontal corridor
def find_clean_horizontal_corridor(sx_port, sy_port, tx_port, ty_port, src_id, tgt_id):
    candidates = [
        (sy_port + ty_port) / 2,
        235, 610, 990
    ]
    
    best_y = None
    min_dist = 999999
    
    for y in candidates:
        if is_horizontal_segment_blocked(y, sx_port, tx_port, exclude_ids=[src_id, tgt_id]):
            continue
        if is_vertical_segment_blocked(sx_port, sy_port, y, exclude_ids=[src_id, tgt_id]):
            continue
        if is_vertical_segment_blocked(tx_port, y, ty_port, exclude_ids=[src_id, tgt_id]):
            continue
            
        midpoint = (sy_port + ty_port) / 2
        dist = abs(y - midpoint)
        
        y_min, y_max = min(sy_port, ty_port), max(sy_port, ty_port)
        if not (y_min - 5 <= y <= y_max + 5):
            dist += 300
            
        if dist < min_dist:
            min_dist = dist
            best_y = y
            
    if best_y is not None:
        return best_y
    return (sy_port + ty_port) / 2

def is_vertical_blocked(src_id, tgt_pos):
    src_pos = node_positions[src_id]
    y_min, y_max = min(src_pos['y'], tgt_pos['y']), max(src_pos['y'], tgt_pos['y'])
    for c_id, pos in node_positions.items():
        if c_id == src_id:
            continue
        if abs(pos['x'] - src_pos['x']) < 15 and y_min < pos['y'] < y_max:
            return True
    return False

def is_vertical_blocked_near_target(tgt_id, src_pos):
    tgt_pos = node_positions[tgt_id]
    y_min, y_max = min(src_pos['y'], tgt_pos['y']), max(src_pos['y'], tgt_pos['y'])
    for c_id, pos in node_positions.items():
        if c_id == tgt_id:
            continue
        if abs(pos['x'] - tgt_pos['x']) < 15 and y_min < pos['y'] < y_max:
            return True
    return False

# First Pass: Count connection directions to determine Port Indices
# node_ports maps each node to lists of connection indices on each of its 4 faces
node_ports = {
    c_id: {
        "Left": [],
        "Right": [],
        "Top": [],
        "Bottom": []
    }
    for c_id in node_positions
}

connection_faces = [] # Cache determined faces for second pass: (exit_face, entry_face)

for index, conn in enumerate(data.get('connections', [])):
    src_id, tgt_id = conn['from'], conn['to']
    src_pos = node_positions.get(src_id)
    tgt_pos = node_positions.get(tgt_id)
    
    if not src_pos or not tgt_pos:
        connection_faces.append((None, None))
        continue

    # Face Heuristic selection
    # 1. Same column bypass to prevent drawing through intermediate nodes
    if abs(src_pos['x'] - tgt_pos['x']) < 15 and abs(src_pos['y'] - tgt_pos['y']) > 150:
        if tgt_pos['y'] > src_pos['y']:
            exit_face, entry_face = "Bottom", ("Left" if tgt_pos['x'] > 1500 else "Right")
        else:
            exit_face, entry_face = "Top", ("Left" if tgt_pos['x'] > 1500 else "Right")
            
    # 2. Descending connections to bottom row nodes (y >= 1000) from NLEADS exit from bottom
    # But exclude nodes on the right column (x >= 1400) so they route via Right -> Left
    elif src_id == "nleads_engine" and tgt_pos['y'] >= 1000 and tgt_pos['x'] < 1400:
        exit_face, entry_face = "Bottom", "Top"

    # 3. Blocked vertical path heuristics
    elif is_vertical_blocked(src_id, tgt_pos) or is_vertical_blocked_near_target(tgt_id, src_pos):
        dx = tgt_pos['x'] - src_pos['x']
        exit_face = "Right" if dx > 0 else "Left"
        entry_face = "Left" if dx > 0 else "Right"
        
        
    # 4. Default general heuristic
    else:
        dx = tgt_pos['x'] - src_pos['x']
        dy = tgt_pos['y'] - src_pos['y']
        
        if abs(dx) >= abs(dy):
            if dx > 0:
                exit_face, entry_face = "Right", "Left"
            else:
                exit_face, entry_face = "Left", "Right"
        else:
            if dy > 0:
                exit_face, entry_face = "Bottom", "Top"
            else:
                exit_face, entry_face = "Top", "Bottom"
                
    node_ports[src_id][exit_face].append(index)
    node_ports[tgt_id][entry_face].append(index)
    connection_faces.append((exit_face, entry_face))

# Sort connection indices on each face to minimize crossing lines
for c_id in node_ports:
    for face in ["Left", "Right", "Top", "Bottom"]:
        conn_indices = node_ports[c_id][face]
        if not conn_indices:
            continue
        
        # Sort ports by target/source X for Top/Bottom (horizontal) and Y for Left/Right (vertical)
        def get_sort_key(idx):
            conn = data['connections'][idx]
            other_id = conn['to'] if conn['from'] == c_id else conn['from']
            other_pos = node_positions.get(other_id, {"x": 0, "y": 0})
            return other_pos["x"] if face in ["Top", "Bottom"] else other_pos["y"]
            
        conn_indices.sort(key=get_sort_key)

# 4. Generate SVG XML
svg_width, svg_height = 1760, 1280
svg_content = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%" style="background-color: #f4f6f9;">',
    '  <defs>',
    '    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
    '      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#4a5568" />',
    '    </marker>',
    '    <marker id="arrow-new" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
    '      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#7D3C98" />',
    '    </marker>',
    '  </defs>',
    '  <style>',
    '    .title { font-family: "Inter", sans-serif; font-size: 22px; font-weight: bold; fill: #4A2E80; }',
    '    .legend-text { font-family: "Inter", sans-serif; font-size: 11px; fill: #4a5568; }',
    '    .zone-title { font-family: "Inter", sans-serif; font-size: 12px; font-weight: bold; fill: #4A2E80; text-transform: uppercase; letter-spacing: 0.5px; }',
    '    .node-text { font-family: "Inter", sans-serif; font-size: 11px; font-weight: bold; fill: #2d3748; text-anchor: middle; }',
    '    .conn-text { font-family: "Inter", sans-serif; font-size: 8px; fill: #4a5568; text-anchor: middle; font-weight: bold; }',
    '  </style>',
    '  <!-- Title -->',
    '  <text x="40" y="45" class="title">NLEADS - Real-time Integration Architecture</text>',
    ''
]

# Render Legend
svg_content.append('  <!-- Legend -->')
svg_content.append('  <g transform="translate(1280, 25)">')
svg_content.append('    <rect x="0" y="0" width="430" height="30" fill="#ffffff" stroke="#e2e8f0" rx="4" ry="4"/>')
svg_content.append('    <rect x="10" y="8" width="12" height="12" fill="#ffffff" stroke="#333333" stroke-width="1.5" rx="2" ry="2"/>')
svg_content.append('    <text x="27" y="17" class="legend-text">Unchanged</text>')
svg_content.append('    <rect x="120" y="8" width="12" height="12" fill="#ffeaa7" stroke="#0984e3" stroke-width="1.5" rx="2" ry="2"/>')
svg_content.append('    <text x="137" y="17" class="legend-text">Updated / Modified</text>')
svg_content.append('    <rect x="270" y="8" width="12" height="12" fill="#ffffff" stroke="#7d3c98" stroke-width="1.5" rx="2" ry="2"/>')
svg_content.append('    <text x="287" y="17" class="legend-text">New System/Flow</text>')
svg_content.append('  </g>')

# Render Groups (Containers)
for g_id, g in group_definitions.items():
    bounds = group_bounds.get(g_id)
    if bounds:
        dash = 'stroke-dasharray="4,4"' if 'dashed' in g.get('style', '') else ''
        stroke_color = "#f1c40f" if "yellow" in g.get('style', '') else (
            "#9b59b6" if "purple" in g.get('style', '') else (
                "#2ecc71" if "green" in g.get('style', '') else (
                    "#3498db" if "blue" in g.get('style', '') else (
                        "#333333" if "black" in g.get('style', '') else "#95a5a6"
                    )
                )
            )
        )
        fill_color = "rgba(254, 253, 232, 0.15)" if "yellow" in g.get('style', '') else (
            "rgba(250, 244, 252, 0.15)" if "purple" in g.get('style', '') else (
                "rgba(244, 253, 248, 0.15)" if "green" in g.get('style', '') else (
                    "rgba(244, 249, 253, 0.12)" if "blue" in g.get('style', '') else (
                        "rgba(248, 249, 249, 0.4)" if "black" in g.get('style', '') else "rgba(149, 165, 166, 0.05)"
                    )
                )
            )
        )
        if g_id in ["mainframe_1", "mainframe_2", "depts_mcs", "verification_grid"]:
            fill_color = "#ffffff"
            stroke_color = "#a0aec0"
        elif g_id == "service_grid":
            fill_color = "rgba(250, 250, 250, 0.8)"
            stroke_color = "#cbd5e0"
            dash = 'stroke-dasharray="3,3"'

        svg_content.append(f'  <rect x="{bounds["x"]}" y="{bounds["y"]}" width="{bounds["w"]}" height="{bounds["h"]}" fill="{fill_color}" stroke="{stroke_color}" stroke-width="1.5" {dash} rx="6" ry="6"/>')
        svg_content.append(f'  <text x="{bounds["x"] + 15}" y="{bounds["y"] + 20}" class="zone-title">{g["name"]}</text>')

# Render Components
svg_content.append('  <!-- Component Nodes -->')
comp_by_id = {c['id']: c for c in data.get('components', [])}
for c_id, pos in node_positions.items():
    comp = comp_by_id.get(c_id)
    if not comp:
        continue
    w, h = get_node_dims(c_id, comp['type'])
    x_left = pos['x'] - w/2
    y_top = pos['y'] - h/2
    
    stroke = "#333333"
    fill = "#ffffff"
    stroke_width = "1.5"
    rx, ry = 4, 4
    
    if c_id == "nleads_engine":
        fill = "#e8f4fc"
        stroke = "#7d3c98"
        stroke_width = "2.5"
    elif c_id in ["confluent_kafka", "e_kafka"]:
        stroke = "#7d3c98"
        stroke_width = "2"
    elif comp['lifecycle_status'] == 'updated' or comp['type'] == 'gateway':
        fill = "#ffeaa7"
        stroke = "#0984e3" if comp['lifecycle_status'] == 'updated' else "#333333"
        stroke_width = "2" if comp['lifecycle_status'] == 'updated' else "1.5"
    elif comp['lifecycle_status'] == 'new':
        stroke = "#7d3c98"
        stroke_width = "2"
        
    if comp['type'] == 'mainframe':
        svg_content.append(f'  <g id="{c_id}">')
        svg_content.append(f'    <rect x="{x_left}" y="{y_top + 6}" width="{w}" height="{h - 6}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" rx="2" ry="2"/>')
        svg_content.append(f'    <ellipse cx="{pos["x"]}" cy="{y_top + 6}" rx="{w/2}" ry="6" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>')
        svg_content.append(f'    <path d="M {x_left} {pos["y"] + h/2 - 6} A {w/2} 6 0 0 0 {x_left + w} {pos["y"] + h/2 - 6}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}"/>')
    else:
        svg_content.append(f'  <g id="{c_id}">')
        svg_content.append(f'    <rect x="{x_left}" y="{y_top}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" rx="{rx}" ry="{ry}"/>')
    
    name_parts = comp['name'].split(' ')
    if len(name_parts) > 1 and len(comp['name']) > 12:
        y_offset = -4 if len(name_parts) == 2 else -8
        for i, part in enumerate(name_parts[:3]):
            svg_content.append(f'    <text x="{pos["x"]}" y="{pos["y"] + y_offset + (i * 12) + 4}" class="node-text">{part}</text>')
    else:
        svg_content.append(f'    <text x="{pos["x"]}" y="{pos["y"] + 4}" class="node-text">{comp["name"]}</text>')
    svg_content.append('  </g>')

# Second Pass: Render Connections with Multi-Port Offset Calculation
svg_content.append('  <!-- Connection Edges -->')

# Pre-calculate ports, directions, and corridors
prepared_connections = []
for index, conn in enumerate(data.get('connections', [])):
    src_id, tgt_id = conn['from'], conn['to']
    src_pos = node_positions.get(src_id)
    tgt_pos = node_positions.get(tgt_id)
    
    if not src_pos or not tgt_pos:
        prepared_connections.append(None)
        continue
        
    exit_face, entry_face = connection_faces[index]
    if not exit_face:
        prepared_connections.append(None)
        continue
        
    src_comp = comp_by_id.get(src_id)
    tgt_comp = comp_by_id.get(tgt_id)
    
    src_w, src_h = get_node_dims(src_id, src_comp['type'])
    tgt_w, tgt_h = get_node_dims(tgt_id, tgt_comp['type'])
    
    sx, sy = src_pos['x'], src_pos['y']
    tx, ty = tgt_pos['x'], tgt_pos['y']
    
    # 1. Compute Exit Port Coordinate on Source Node Edge
    out_list = node_ports[src_id][exit_face]
    i = out_list.index(index)
    K = len(out_list)
    
    if src_id == "nleads_engine" and exit_face == "Bottom":
        fanning_w = 95
        offset_src = (fanning_w / (K + 1)) * (i + 1) - fanning_w / 2 + 12
    else:
        L_src = src_h if exit_face in ["Left", "Right"] else src_w
        offset_src = (L_src / (K + 1)) * (i + 1) - L_src / 2

    
    if exit_face == "Right":
        sx_port, sy_port = sx + src_w/2, sy + offset_src
    elif exit_face == "Left":
        sx_port, sy_port = sx - src_w/2, sy + offset_src
    elif exit_face == "Bottom":
        sx_port, sy_port = sx + offset_src, sy + src_h/2
    else: # Top
        sx_port, sy_port = sx + offset_src, sy - src_h/2

    # 2. Compute Entry Port Coordinate on Target Node Edge
    in_list = node_ports[tgt_id][entry_face]
    j = in_list.index(index)
    M = len(in_list)
    L_tgt = tgt_h if entry_face in ["Left", "Right"] else tgt_w
    offset_tgt = (L_tgt / (M + 1)) * (j + 1) - L_tgt / 2
    
    if entry_face == "Right":
        tx_port, ty_port = tx + tgt_w/2, ty + offset_tgt
    elif entry_face == "Left":
        tx_port, ty_port = tx - tgt_w/2, ty + offset_tgt
    elif entry_face == "Bottom":
        tx_port, ty_port = tx + offset_tgt, ty + tgt_h/2
    else: # Top
        tx_port, ty_port = tx + offset_tgt, ty - tgt_h/2

    # Determine general direction
    direction = "Vertical" if exit_face in ["Top", "Bottom"] and entry_face in ["Top", "Bottom"] else "Horizontal"
    
    # Find clean corridor
    if direction == "Horizontal":
        mid_x = find_clean_vertical_corridor(sx_port, sy_port, tx_port, ty_port, src_id, tgt_id)
        mid_y = None
    else:
        mid_x = None
        mid_y = find_clean_horizontal_corridor(sx_port, sy_port, tx_port, ty_port, src_id, tgt_id)
        
    prepared_connections.append({
        "index": index,
        "conn": conn,
        "sx_port": sx_port,
        "sy_port": sy_port,
        "tx_port": tx_port,
        "ty_port": ty_port,
        "direction": direction,
        "mid_x": mid_x,
        "mid_y": mid_y,
        "src_id": src_id,
        "tgt_id": tgt_id,
        "offset_val": 0
    })

# Group connections by corridors to assign sorted stagger offsets
v_corridors_groups = {}
h_corridors_groups = {}

for prep in prepared_connections:
    if not prep:
        continue
    if prep["direction"] == "Horizontal":
        corr_key = int(round(prep["mid_x"] / 10.0) * 10)
        if corr_key not in v_corridors_groups:
            v_corridors_groups[corr_key] = []
        v_corridors_groups[corr_key].append(prep)
    else:
        corr_key = int(round(prep["mid_y"] / 10.0) * 10)
        if corr_key not in h_corridors_groups:
            h_corridors_groups[corr_key] = []
        h_corridors_groups[corr_key].append(prep)

# Sort each vertical corridor group by (sy_port + ty_port) / 2 to prevent crossings (FIFO/Nesting rule)
for corr_key, preps in v_corridors_groups.items():
    preps.sort(key=lambda p: (p["sy_port"] + p["ty_port"]) / 2)
    N = len(preps)
    for idx, prep in enumerate(preps):
        prep["offset_val"] = idx * 12 - (N - 1) * 6

# Sort each horizontal corridor group by (sx_port + tx_port) / 2 to prevent crossings (FIFO/Nesting rule)
for corr_key, preps in h_corridors_groups.items():
    preps.sort(key=lambda p: (p["sx_port"] + p["tx_port"]) / 2)
    N = len(preps)
    for idx, prep in enumerate(preps):
        prep["offset_val"] = idx * 12 - (N - 1) * 6

# Draw orthogonal connections with dynamic track separation
for prep in prepared_connections:
    if not prep:
        continue
    index = prep["index"]
    conn = prep["conn"]
    sx_port = prep["sx_port"]
    sy_port = prep["sy_port"]
    tx_port = prep["tx_port"]
    ty_port = prep["ty_port"]
    direction = prep["direction"]
    offset_val = prep["offset_val"]
    src_id = prep["src_id"]
    tgt_id = prep["tgt_id"]
    
    is_new = conn.get('status') == 'new'
    edge_color = "#7d3c98" if is_new else "#4a5568"
    marker = "url(#arrow-new)" if is_new else "url(#arrow)"
    
    path_d = ""
    label_x, label_y = 0, 0
    
    if direction == "Horizontal":
        # Check if straight line is possible and unblocked
        if abs(sy_port - ty_port) < 15 and not is_horizontal_segment_blocked(sy_port, sx_port, tx_port, exclude_ids=[src_id, tgt_id]):
            path_d = f"M {sx_port} {sy_port} L {tx_port} {ty_port}"
            label_x = (sx_port + tx_port) / 2
            label_y = sy_port - 6
        else:
            mid_x = prep["mid_x"]
            staggered_mid_x = mid_x + offset_val
            path_d = f"M {sx_port} {sy_port} L {staggered_mid_x} {sy_port} L {staggered_mid_x} {ty_port} L {tx_port} {ty_port}"
            label_x = staggered_mid_x
            label_y = (sy_port + ty_port) / 2
            
    else: # Vertical flow
        # Check if straight line is possible and unblocked
        if abs(sx_port - tx_port) < 15 and not is_vertical_segment_blocked(sx_port, sy_port, ty_port, exclude_ids=[src_id, tgt_id]):
            path_d = f"M {sx_port} {sy_port} L {tx_port} {ty_port}"
            label_x = sx_port + 6
            label_y = (sy_port + ty_port) / 2
        else:
            mid_y = prep["mid_y"]
            staggered_mid_y = mid_y + offset_val
            path_d = f"M {sx_port} {sy_port} L {sx_port} {staggered_mid_y} L {tx_port} {staggered_mid_y} L {tx_port} {ty_port}"
            label_x = (sx_port + tx_port) / 2
            label_y = staggered_mid_y - 6

    # Render Path and Label
    svg_content.append(f'  <path d="{path_d}" fill="none" stroke="{edge_color}" stroke-width="1.6" marker-end="{marker}"/>')
    
    if conn.get('protocol'):
        proto = conn['protocol']
        label_w = len(proto) * 6 + 10
        svg_content.append(f'  <g transform="translate({label_x}, {label_y})">')
        svg_content.append(f'    <rect x="{-label_w/2}" y="-7" width="{label_w}" height="13" fill="#ffffff" stroke="#e2e8f0" stroke-width="0.7" rx="2" ry="2"/>')
        svg_content.append(f'    <text x="0" y="2" class="conn-text" fill="{edge_color}">{proto}</text>')
        svg_content.append('  </g>')

svg_content.append('</svg>')

# Save final clean SVG
with open(output_svg, 'w') as f:
    f.write("\n".join(svg_content))

print(f"Generated clean SVG at {output_svg}")
