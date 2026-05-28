from __future__ import annotations

from .schema import ComponentType

# Per-type target dimensions, font size and weight. Width/height are *minimum*
# targets — they grow if a wrapped label still doesn't fit.
NODE_PROFILE: dict[ComponentType, dict] = {
    ComponentType.core_engine:     {"w": 230, "h": 105, "font": 16, "weight": "700"},
    ComponentType.actor:           {"w": 120, "h": 110, "font": 13, "weight": "400"},
    ComponentType.datastore:       {"w": 160, "h": 90,  "font": 14, "weight": "400"},
    ComponentType.queue:           {"w": 190, "h": 75,  "font": 14, "weight": "400"},
    ComponentType.mainframe:       {"w": 180, "h": 75,  "font": 14, "weight": "400"},
    ComponentType.gateway:         {"w": 175, "h": 75,  "font": 14, "weight": "400"},
    ComponentType.external_partner:{"w": 180, "h": 75,  "font": 14, "weight": "400"},
    ComponentType.channel:         {"w": 180, "h": 75,  "font": 14, "weight": "400"},
    ComponentType.server:          {"w": 180, "h": 75,  "font": 14, "weight": "400"},
}
DEFAULT_PROFILE = {"w": 180, "h": 75, "font": 14, "weight": "400"}

PADDING_X = 16
PADDING_Y = 14
LINE_HEIGHT_MULT = 1.25
CHAR_WIDTH_MULT = 0.58   # average char width as fraction of font size (Inter/system-ui ish)
MAX_LINES = 3

EDGE_LABEL_FONT = 12
GROUP_LABEL_FONT = 14
TITLE_FONT = 22


def get_profile(type_: ComponentType) -> dict:
    return NODE_PROFILE.get(type_, DEFAULT_PROFILE)


def wrap_text(text: str, max_chars: int, max_lines: int = MAX_LINES) -> list[str]:
    """Greedy word-wrap. Returns up to max_lines; overflow gets glued onto the last line."""
    words = text.split()
    if not words:
        return [text]
    lines: list[str] = []
    current = words[0]
    for w in words[1:]:
        candidate = current + " " + w
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = w
    lines.append(current)
    if len(lines) > max_lines:
        head = lines[: max_lines - 1]
        tail = " ".join(lines[max_lines - 1 :])
        lines = head + [tail]
    return lines


def compute_node_layout(
    text: str, type_: ComponentType
) -> tuple[int, int, list[str], int, str]:
    """Return (width, height, lines, font_px, font_weight) for a component.

    The same function is used by both the transformer (to size the ELK node)
    and the renderer (to draw the same wrapped lines).
    """
    p = get_profile(type_)
    font = int(p["font"])
    char_w = font * CHAR_WIDTH_MULT
    line_h = font * LINE_HEIGHT_MULT

    target_w = int(p["w"])
    target_h = int(p["h"])

    # Available text width inside the target node, in characters.
    usable = max(20, target_w - PADDING_X * 2)
    max_chars = max(6, int(usable / char_w))
    lines = wrap_text(text, max_chars, MAX_LINES)
    longest = max(len(l) for l in lines)

    needed_w = int(longest * char_w) + PADDING_X * 2
    width = max(target_w, needed_w)

    text_h = int(len(lines) * line_h)
    height = max(target_h, text_h + PADDING_Y * 2)

    return width, height, lines, font, str(p["weight"])


def estimate_text_size(text: str, font_px: int) -> tuple[int, int]:
    """For ELK label hints on edges/groups — single-line estimate."""
    w = max(36, int(len(text) * font_px * CHAR_WIDTH_MULT) + 12)
    h = int(font_px * LINE_HEIGHT_MULT)
    return w, h
