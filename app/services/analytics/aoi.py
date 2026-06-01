from typing import Optional


def get_grid_cell(x_norm: float, y_norm: float) -> int:
    """
    정규화 좌표 → 3x3 그리드 셀 번호 (1~9)
    1 2 3
    4 5 6
    7 8 9
    """
    col = min(int(x_norm * 3), 2)  # 0, 1, 2
    row = min(int(y_norm * 3), 2)  # 0, 1, 2
    return row * 3 + col + 1


def get_area_type(cell: int, grid: dict) -> Optional[str]:
    """
    그리드 셀 번호 → 영역 타입 (person/product/text/background)
    우선순위: product > person > text > background
    """
    if cell in grid.get("product", []):
        return "product"
    if cell in grid.get("person", []):
        return "person"
    if cell in grid.get("text", []):
        return "text"
    if cell in grid.get("background", []):
        return "background"
    return None


def compute_aoi(frames: list, scenes: list, participant_count: int = 1) -> dict:
    area_frames = {"product": 0, "person": 0, "text": 0, "background": 0}

    for frame in frames:
        elapsed_sec = frame["elapsed_ms"] / 1000
        x = frame["gaze"]["x_norm"]
        y = frame["gaze"]["y_norm"]

        current_scene = None
        for scene in scenes:
            if scene["start"] <= elapsed_sec < scene["end"]:
                current_scene = scene
                break

        if not current_scene:
            continue

        cell = get_grid_cell(x, y)
        area = get_area_type(cell, current_scene["grid"])

        if area:
            area_frames[area] += 1

    aoi_rows = []
    for area, count in sorted(area_frames.items(), key=lambda x: -x[1]):
        if count == 0:
            continue
        dwell_sec = round((count / 30) / participant_count, 1)  # 참여자 수로 나눔
        aoi_rows.append({
            "area": _area_label(area),
            "dwell": f"{dwell_sec}초",
            "count": count // participant_count,
        })

    return aoi_rows


def _area_label(area: str) -> str:
    return {
        "product": "제품 영역",
        "person": "인물 영역",
        "text": "텍스트/CTA",
        "background": "배경 영역",
    }.get(area, area)