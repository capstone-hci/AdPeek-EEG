import sys
import os
import uuid
import random
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.database.models import Session as SessionModel, Survey, AdResult

# 그리드 셀 중심 좌표
CELL_COORDS = {
    1: (0.17, 0.17), 2: (0.50, 0.17), 3: (0.83, 0.17),
    4: (0.17, 0.50), 5: (0.50, 0.50), 6: (0.83, 0.50),
    7: (0.17, 0.83), 8: (0.50, 0.83), 9: (0.83, 0.83),
}

# 씬 데이터 (product/text 강조)
SCENES = [
    {"scene": 1,  "start": 0.00,  "end": 1.67,  "grid": {"person": [5, 8], "background": [1,2,3,4,6,7,9], "text": [], "product": []}},
    {"scene": 2,  "start": 1.67,  "end": 4.07,  "grid": {"person": [2,5,8], "background": [1,3,4,7], "text": [6,9], "product": []}},
    {"scene": 3,  "start": 4.07,  "end": 5.97,  "grid": {"person": [1,2,4,5,7,8], "background": [3,6], "text": [9], "product": []}},
    {"scene": 4,  "start": 5.97,  "end": 8.04,  "grid": {"person": [2,5,7,8], "background": [1,3,4,6], "text": [8,9], "product": []}},
    {"scene": 5,  "start": 8.04,  "end": 8.88,  "grid": {"person": [1,4,7], "background": [2,3], "text": [8,9], "product": [5,6]}},
    {"scene": 6,  "start": 8.88,  "end": 10.81, "grid": {"person": [4,7], "background": [1,2], "text": [8,9], "product": [3,5,6]}},
    {"scene": 7,  "start": 10.81, "end": 11.58, "grid": {"person": [2,5,8], "background": [1,3,4,6,7], "text": [9], "product": [8]}},
    {"scene": 8,  "start": 11.58, "end": 12.58, "grid": {"person": [1,2,4,7], "background": [3], "text": [8,9], "product": [5,6]}},
    {"scene": 9,  "start": 12.58, "end": 14.28, "grid": {"person": [2], "background": [1,3,4], "text": [7,8,9], "product": [5,6]}},
    {"scene": 10, "start": 14.28, "end": 17.08, "grid": {"person": [6], "background": [1,2,3,4,5], "text": [7,8,9], "product": []}},
    {"scene": 11, "start": 17.08, "end": 17.85, "grid": {"person": [2,5,8], "background": [1,3,4,6,7,9], "text": [], "product": []}},
    {"scene": 12, "start": 17.85, "end": 20.72, "grid": {"person": [2,5,8], "background": [1,3,4,6,7,9], "text": [], "product": []}},
    {"scene": 13, "start": 20.72, "end": 23.32, "grid": {"person": [5], "background": [1,2,3,4,6,7,8,9], "text": [], "product": []}},
    {"scene": 14, "start": 25.79, "end": 30.02, "grid": {"person": [], "background": [1,2,3,4,6,7,8,9], "text": [5], "product": []}},
]


def get_scene_at(elapsed_sec: float):
    for scene in SCENES:
        if scene["start"] <= elapsed_sec < scene["end"]:
            return scene
    return None


def is_product_or_text_scene(scene: dict) -> bool:
    if not scene:
        return False
    return bool(scene["grid"]["product"] or scene["grid"]["text"])


def get_focus_cell(scene: dict) -> int:
    """제품/텍스트 씬이면 해당 셀, 아니면 배경"""
    if scene["grid"]["product"]:
        return random.choice(scene["grid"]["product"])
    if scene["grid"]["text"]:
        return random.choice(scene["grid"]["text"])
    if scene["grid"]["person"]:
        return random.choice(scene["grid"]["person"])
    return random.choice(scene["grid"]["background"])


def add_noise(val: float, noise: float = 0.03) -> float:
    return round(max(0.0, min(1.0, val + random.uniform(-noise, noise))), 3)


def generate_gaze_frames(participant_id: int) -> list:
    """30Hz × 30초 = 900프레임 생성"""
    frames = []
    total_frames = 900  # 30s × 30Hz

    base_attention = random.uniform(3.0, 4.5)
    base_arousal = random.uniform(5.0, 7.0)

    for i in range(total_frames):
        elapsed_ms = i * 33
        elapsed_sec = elapsed_ms / 1000

        scene = get_scene_at(elapsed_sec)
        if not scene:
            continue

        # 제품/텍스트 씬에서 집중도/각성도 상승
        is_focus = is_product_or_text_scene(scene)
        if is_focus:
            attention = base_attention + random.uniform(2.5, 4.5) + math.sin(i * 0.1) * 0.5
            arousal = base_arousal + random.uniform(3.0, 6.0) + math.cos(i * 0.1) * 0.8
        else:
            attention = base_attention + random.uniform(-0.5, 1.0)
            arousal = base_arousal + random.uniform(-1.0, 1.5)

        # gaze 좌표 — 제품/텍스트에 집중
        cell = get_focus_cell(scene)
        cx, cy = CELL_COORDS[cell]
        x_norm = add_noise(cx, 0.08)
        y_norm = add_noise(cy, 0.08)

        frames.append({
            "timestamp": round(elapsed_sec, 3),
            "elapsed_ms": elapsed_ms,
            "gaze": {"x_norm": x_norm, "y_norm": y_norm},
            "eeg": {
                "attention": round(attention, 4),
                "arousal": round(arousal, 4),
            }
        })

    return frames


def generate_eeg_summary(frames: list) -> dict:
    attentions = [f["eeg"]["attention"] for f in frames]
    arousals = [f["eeg"]["arousal"] for f in frames]
    return {
        "attention": round(sum(attentions) / len(attentions), 4),
        "arousal": round(sum(arousals) / len(arousals), 4),
        "bands": {
            "alpha": round(random.uniform(20.0, 35.0), 4),
            "beta": round(random.uniform(120.0, 180.0), 4),
            "theta": round(random.uniform(4.0, 8.0), 4),
        }
    }


# 설문 데이터 (15명 기준 — recall 약 67%, positive 약 60%)
SURVEY_DATA = [
    ("yes", 5, "positive"),
    ("yes", 4, "positive"),
    ("yes", 5, "positive"),
    ("yes", 4, "neutral"),
    ("yes", 3, "positive"),
    ("yes", 4, "positive"),
    ("yes", 5, "positive"),
    ("yes", 4, "positive"),
    ("unsure", 3, "neutral"),
    ("unsure", 3, "neutral"),
    ("no", 2, "negative"),
    ("yes", 4, "positive"),
    ("yes", 5, "positive"),
    ("unsure", 3, "neutral"),
    ("no", 2, "negative"),
]


def seed():
    db = SessionLocal()
    try:
        # 기존 데이터 삭제
        db.query(SessionModel).filter(SessionModel.ad_id == "ad_001").delete()
        db.query(Survey).filter(Survey.ad_id == "ad_001").delete()
        db.query(AdResult).filter(AdResult.ad_id == "ad_001").delete()
        db.commit()
        print("기존 데이터 삭제 완료")

        for i in range(15):
            frames = generate_gaze_frames(i)
            eeg_data = generate_eeg_summary(frames)

            session = SessionModel(
                id=str(uuid.uuid4()),
                ad_id="ad_001",
                start_time=1714900000.0 + i * 300,
                gaze_data=[{
                    "x_norm": f["gaze"]["x_norm"],
                    "y_norm": f["gaze"]["y_norm"],
                    "timestamp": f["timestamp"],
                    "elapsed_ms": f["elapsed_ms"],
                } for f in frames],
                eeg_data=eeg_data,
                synced_frames=frames,
            )
            db.add(session)

            recall, score, emotion = SURVEY_DATA[i]
            survey = Survey(
                id=str(uuid.uuid4()),
                ad_id="ad_001",
                session_id=session.id,
                recall=recall,
                brand_score=score,
                emotion=emotion,
            )
            db.add(survey)
            db.commit()
            print(f"참여자 {i+1} 삽입 완료")

        print("\n✅ 더미 데이터 15명 삽입 완료")

    except Exception as e:
        db.rollback()
        print(f"❌ 오류: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()