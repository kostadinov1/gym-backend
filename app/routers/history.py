from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.db.database import get_session
from app.db.models import WorkoutSession, WorkoutRoutine
from app.schemas.session import SessionRead

# We need a custom schema for the list view (lighter than full details)
from pydantic import BaseModel
import uuid

class SessionSummary(BaseModel):
    id: uuid.UUID
    routine_name: str
    date: datetime
    status: str

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/", response_model=List[SessionSummary])
def get_history(
    start_date: datetime,
    end_date: datetime,
    session: Session = Depends(get_session)
):
    # Select sessions joined with routine names
    statement = (
        select(WorkoutSession, WorkoutRoutine.name)
        .join(WorkoutRoutine)
        .where(WorkoutSession.start_time >= start_date)
        .where(WorkoutSession.start_time <= end_date)
        .order_by(WorkoutSession.start_time.desc())
    )
    
    results = session.exec(statement).all()
    
    # Transform to schema
    history = []
    for workout, routine_name in results:
        history.append(SessionSummary(
            id=workout.id,
            routine_name=routine_name,
            date=workout.start_time,
            status=workout.status
        ))
        
    return history