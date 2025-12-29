from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlmodel import Session, select
from typing import List, Optional
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


class UserStats(BaseModel):
    total_workouts: int
    workouts_this_month: int
    last_workout_date: Optional[datetime] = None

@router.get("/stats", response_model=UserStats)
def get_stats(session: Session = Depends(get_session)):
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)

    # 1. Total Count
    total = session.exec(select(func.count(WorkoutSession.id)).where(WorkoutSession.status == "completed")).one()
    
    # 2. This Month
    month_count = session.exec(
        select(func.count(WorkoutSession.id))
        .where(WorkoutSession.status == "completed")
        .where(WorkoutSession.start_time >= start_of_month)
    ).one()
    
    # 3. Last Workout
    last_workout = session.exec(
        select(WorkoutSession)
        .where(WorkoutSession.status == "completed")
        .order_by(WorkoutSession.end_time.desc())
        .limit(1)
    ).first()

    return UserStats(
        total_workouts=total,
        workouts_this_month=month_count,
        last_workout_date=last_workout.end_time if last_workout else None
    )