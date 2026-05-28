import sys
sys.path.append("/Users/kongkittisan/Documents/workspaces/diagram-agent/scratch")
from generate_svg import (
    data, node_positions, comp_by_id, get_node_dims,
    is_vertical_segment_blocked, is_horizontal_segment_blocked,
    find_clean_vertical_corridor, is_vertical_blocked, is_vertical_blocked_near_target
)

src_id = "nleads_engine"
tgt_id = "sftp_server"

src_pos = node_positions[src_id]
tgt_pos = node_positions[tgt_id]

src_w, src_h = get_node_dims(src_id, "core_engine")
tgt_w, tgt_h = get_node_dims(tgt_id, "server")

sx, sy = src_pos['x'], src_pos['y']
tx, ty = tgt_pos['x'], tgt_pos['y']

sx_port, sy_port = sx - src_w/2, sy
tx_port, ty_port = tx + tgt_w/2, ty

# exit from bottom, enter top
sx_port, sy_port = sx, sy + src_h/2
tx_port, ty_port = tx, ty - tgt_h/2

print(f"sx_port={sx_port}, sy_port={sy_port}, tx_port={tx_port}, ty_port={ty_port}")

# Test blockage specifically at x=150
x = 150
y_min = 780
y_max = 1057
exclude_ids = [src_id, tgt_id]

margin_x = 10
margin_y = 5
y_start, y_end = min(y_min, y_max), max(y_min, y_max)
print(f"Checking x={x} from {y_start} to {y_end}:")
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
        overlap = max(y_start, comp_y_min) <= min(y_end, comp_y_max)
        print(f"  node {c_id}: x_range=[{comp_x_min}, {comp_x_max}], y_range=[{comp_y_min}, {comp_y_max}], overlap={overlap}")



# Done

