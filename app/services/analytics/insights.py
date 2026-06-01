import numpy as np
from typing import Optional


def compute_eeg_peaks(frames: list) -> dict:
    if not frames:
        return {"attentionPeakRange": None, "arousalPeakRange": None}

    attention_values = [f["eeg"]["attention"] for f in frames]
    arousal_values = [f["eeg"]["arousal"] for f in frames]
    timestamps = [f["elapsed_ms"] / 1000 for f in frames]

    def get_peak_range(values: list, timestamps: list) -> Optional[str]:
        if not values:
            return None
        peak_idx = int(np.argmax(values))
        start = max(0, peak_idx - 15)
        end = min(len(timestamps) - 1, peak_idx + 15)
        return f"{round(timestamps[start], 1)}–{round(timestamps[end], 1)}s"

    return {
        "attentionPeakRange": get_peak_range(attention_values, timestamps),
        "arousalPeakRange": get_peak_range(arousal_values, timestamps),
    }


def compute_gaze_insights(frames: list, aoi_rows: list) -> dict:
    if not frames:
        return {
            "maxGazeRange": None,
            "maxDwellTime": None,
            "aoiRows": [],
        }

    attention_values = [f["eeg"]["attention"] for f in frames]
    timestamps = [f["elapsed_ms"] / 1000 for f in frames]
    peak_idx = int(max(range(len(attention_values)), key=lambda i: attention_values[i]))
    start = max(0, peak_idx - 15)
    end = min(len(timestamps) - 1, peak_idx + 15)

    max_dwell = 0.0
    for row in aoi_rows:
        val = float(row["dwell"].replace("초", ""))
        if val > max_dwell:
            max_dwell = val

    return {
        "maxGazeRange": f"{round(timestamps[start], 1)}–{round(timestamps[end], 1)}s",
        "maxDwellTime": f"{round(max_dwell, 1)}초",
        "aoiRows": aoi_rows,
    }


def compute_survey_insights(surveys: list) -> dict:
    if not surveys:
        return {
            "recallRate": None,
            "purchaseIntent": None,
            "positiveEmotion": None,
        }

    total = len(surveys)
    recall_count = sum(1 for s in surveys if s.recall == "yes")
    positive_count = sum(1 for s in surveys if s.emotion == "positive")
    avg_brand_score = round(sum(s.brand_score for s in surveys) / total, 1)

    return {
        "recallRate": f"{round(recall_count / total * 100)}%",
        "purchaseIntent": f"{avg_brand_score}/5",
        "positiveEmotion": f"{round(positive_count / total * 100)}%",
    }


def compute_attention_percent(avg_attention: float) -> int:
    normalized = min(avg_attention / 10.0, 1.0)
    return round(normalized * 100)