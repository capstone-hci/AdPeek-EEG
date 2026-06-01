import numpy as np
from sqlalchemy.orm import Session
from app.database.models import Session as SessionModel, AdResult, Ad, Survey
from app.services.analytics.aoi import compute_aoi
from app.services.analytics.insights import (
    compute_eeg_peaks,
    compute_gaze_insights,
    compute_survey_insights,
    compute_attention_percent,
)
import uuid


def aggregate_ad_results(db: Session, ad_id: str) -> dict:
    sessions = db.query(SessionModel).filter(
        SessionModel.ad_id == ad_id,
        SessionModel.eeg_data.isnot(None),
    ).all()

    if not sessions:
        return None

    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    scene_data = []
    if ad and ad.scene_data:
        scene_data = ad.scene_data.get("video_analysis", {}).get("scenes", [])

    surveys = db.query(Survey).filter(Survey.ad_id == ad_id).all()

    participant_count = len(sessions)
    attention_list = []
    arousal_list = []
    heatmap_points = []
    all_frames = []

    for session in sessions:
        if session.eeg_data:
            attention_list.append(session.eeg_data.get("attention", 0))
            arousal_list.append(session.eeg_data.get("arousal", 0))

        if session.synced_frames:
            for frame in session.synced_frames:
                heatmap_points.append({
                    "x": frame["gaze"]["x_norm"],
                    "y": frame["gaze"]["y_norm"],
                })
            all_frames.extend(session.synced_frames)

    avg_attention = round(float(np.mean(attention_list)), 4) if attention_list else None
    avg_arousal = round(float(np.mean(arousal_list)), 4) if arousal_list else None
    avg_gaze_duration = 30.0  # 광고 영상 길이 고정

    # 씬별 집계
    scene_results = []
    for scene in scene_data:
        scene_frames = [
            f for f in all_frames
            if scene["start"] <= f["elapsed_ms"] / 1000 < scene["end"]
        ]

        scene_attention = [f["eeg"]["attention"] for f in scene_frames if "eeg" in f]
        scene_arousal = [f["eeg"]["arousal"] for f in scene_frames if "eeg" in f]
        scene_heatmap = [
            {"x": f["gaze"]["x_norm"], "y": f["gaze"]["y_norm"]}
            for f in scene_frames if "gaze" in f
        ]

        scene_results.append({
            "scene": scene["scene"],
            "start": scene["start"],
            "end": scene["end"],
            "avg_attention": round(float(np.mean(scene_attention)), 4) if scene_attention else None,
            "avg_arousal": round(float(np.mean(scene_arousal)), 4) if scene_arousal else None,
            "heatmap_data": scene_heatmap,
        })

    # AOI 분석
    aoi_rows = compute_aoi(all_frames, scene_data, participant_count)

    # EEG 피크
    eeg_peaks = compute_eeg_peaks(all_frames)

    # gaze insights
    gaze_insights = compute_gaze_insights(all_frames, aoi_rows)

    # survey 집계
    survey_insights = compute_survey_insights(surveys)

    # attention percent
    attention_percent = compute_attention_percent(avg_attention) if avg_attention else 0

    # insights
    insights = {
        "attentionPercent": attention_percent,
        "recallRate": int(survey_insights["recallRate"].replace("%", "")) if survey_insights["recallRate"] else None,
        "gaze": gaze_insights,
        "eeg": eeg_peaks,
        "survey": survey_insights,
    }

    result = {
        "ad_id": ad_id,
        "participant_count": participant_count,
        "avg_attention": avg_attention,
        "avg_arousal": avg_arousal,
        "avg_gaze_duration": avg_gaze_duration,
        "heatmap_data": heatmap_points,
        "scenes": scene_results,
        "insights": insights,
    }

    existing = db.query(AdResult).filter(AdResult.ad_id == ad_id).first()
    if existing:
        for key, value in result.items():
            setattr(existing, key, value)
    else:
        db.add(AdResult(id=str(uuid.uuid4()), **result))

    db.commit()

    return result