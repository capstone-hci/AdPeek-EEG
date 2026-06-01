import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.database.models import Session as SessionModel, Ad
from app.services.analytics.insights import compute_attention_percent

router = APIRouter()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    try:
        sessions = db.query(SessionModel).filter(
            SessionModel.eeg_data.isnot(None),
        ).all()

        total_participants = len(sessions)
        total_ads = db.query(Ad).count()

        attention_list = [
            s.eeg_data.get("attention", 0) for s in sessions if s.eeg_data
        ]
        avg_attention_index = (
            round(float(np.mean(attention_list)), 4) if attention_list else 0.0
        )
        attention_percent = (
            compute_attention_percent(avg_attention_index) if attention_list else 0
        )

        return {
            "total_participants": total_participants,
            "total_ads": total_ads,
            # 프론트가 avg_attention에 %를 붙이는 경우 → 0~100 표시값
            "avg_attention": attention_percent,
            "attention_percent": attention_percent,
            "avg_attention_index": avg_attention_index,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))