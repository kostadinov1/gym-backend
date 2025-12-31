from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel

from app.db.database import get_session
from app.db.models import WorkoutSession, WorkoutRoutine, User
from app.core.security import get_current_user # <--- Auth

class SessionSummary(BaseModel):
    id: uuid.UUID
    routine_name: str
    date: datetime
    status: str

class UserStats(BaseModel):
    total_workouts: int
    workouts_this_month: int
    last_workout_date: Optional[datetime] = None

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/", response_model=List[SessionSummary])
def get_history(
    start_date: datetime,
    end_date: datetime,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # <--- Auth
):
    statement = (
        select(WorkoutSession, WorkoutRoutine.name)
        .join(WorkoutRoutine)
        .where(WorkoutSession.user_id == current_user.id) # <--- Filter
        .where(WorkoutSession.start_time >= start_date)
        .where(WorkoutSession.start_time <= end_date)
        .order_by(WorkoutSession.start_time.desc())
    )
    
    results = session.exec(statement).all()
    
    history = []
    for workout, routine_name in results:
        history.append(SessionSummary(
            id=workout.id,
            routine_name=routine_name,
            date=workout.start_time,
            status=workout.status
        ))
    return history

@router.get("/stats", response_model=UserStats)
def get_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # <--- Auth
):
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)

    # Base query for THIS user
    base_query = select(func.count(WorkoutSession.id)).where(WorkoutSession.user_id == current_user.id).where(WorkoutSession.status == "completed")

    total = session.exec(base_query).one()
    
    month_count = session.exec(
        base_query.where(WorkoutSession.start_time >= start_of_month)
    ).one()
    
    last_workout = session.exec(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == current_user.id)
        .where(WorkoutSession.status == "completed")
        .order_by(WorkoutSession.end_time.desc())
        .limit(1)
    ).first()

    return UserStats(
        total_workouts=total,
        workouts_this_month=month_count,
        last_workout_date=last_workout.end_time if last_workout else None
    )