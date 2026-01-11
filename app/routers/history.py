from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel

from app.db.database import get_session
from app.db.models import WorkoutSession, WorkoutRoutine, User
from app.core.security import get_current_user # <--- Auth


from app.db.models import SessionSet, Exercise # Ensure these are imported
from app.schemas.session import SessionDetailRead, SessionSetDetail # Import new schemas

from app.schemas.session import SessionUpdate, SessionRead
from app.db.models import SessionSet

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



@router.get("/{session_id}", response_model=SessionDetailRead)
def get_session_details(
    session_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # 1. Get the Session
    workout_session = session.get(WorkoutSession, session_id)
    if not workout_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Security: Ensure it belongs to the user
    if workout_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 2. Get the Routine Name
    routine = session.get(WorkoutRoutine, workout_session.routine_id)
    routine_name = routine.name if routine else "Unknown Routine"

    # 3. Get the Sets (Joined with Exercise Name)
    # We query SessionSet and join Exercise to get the name
    sets_results = session.exec(
        select(SessionSet, Exercise.name, Exercise.id) # Select ID too
        .join(Exercise, SessionSet.exercise_id == Exercise.id)
        .where(SessionSet.session_id == session_id)
        .order_by(SessionSet.exercise_id, SessionSet.set_number) 
    ).all()

    sets_data = []
    for s, ex_name, ex_id in sets_results: # Unpack ID
        sets_data.append(SessionSetDetail(
            exercise_id=ex_id, # Pass it
            exercise_name=ex_name,
            set_number=s.set_number,
            reps=s.reps,
            weight=s.weight,
            is_completed=s.is_completed
        ))

    # Calculate Duration
    duration = 0
    if workout_session.end_time and workout_session.start_time:
        diff = workout_session.end_time - workout_session.start_time
        duration = int(diff.total_seconds() / 60)

    return SessionDetailRead(
        id=workout_session.id,
        routine_name=routine_name,
        start_time=workout_session.start_time,
        end_time=workout_session.end_time or workout_session.start_time,
        duration_minutes=duration,
        sets=sets_data
    )






# 2. Add PUT (Edit Session)
@router.put("/{session_id}", response_model=SessionRead)
def update_session(
    session_id: uuid.UUID,
    update_data: SessionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    workout_session = session.get(WorkoutSession, session_id)
    if not workout_session or workout_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found or authorized")

    # Transaction: Replace Sets
    try:
        # Delete old
        existing = session.exec(select(SessionSet).where(SessionSet.session_id == session_id)).all()
        for x in existing: session.delete(x)
        
        # Add new
        for s in update_data.sets:
            new_set = SessionSet(
                session_id=session_id,
                exercise_id=s.exercise_id,
                set_number=s.set_number,
                reps=s.reps,
                weight=s.weight,
                is_completed=s.is_completed
            )
            session.add(new_set)
            
        session.commit()
        return SessionRead(id=workout_session.id, status=workout_session.status)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

# @router.put("/{session_id}", response_model=SessionRead)
# def update_session(
#     session_id: uuid.UUID,
#     update_data: SessionUpdate,
#     session: Session = Depends(get_session),
#     current_user: User = Depends(get_current_user)
# ):
#     # 1. Get the Session
#     workout_session = session.get(WorkoutSession, session_id)
#     if not workout_session:
#         raise HTTPException(status_code=404, detail="Session not found")
        
#     if workout_session.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized")

#     # 2. Transaction: Delete Old Sets -> Add New Sets
#     # This ensures we don't have orphaned sets or logic errors with re-ordering
#     try:
#         # Delete existing sets for this session
#         existing_sets = session.exec(
#             select(SessionSet).where(SessionSet.session_id == session_id)
#         ).all()
#         for s in existing_sets:
#             session.delete(s)
            
#         # Add new sets
#         for s in update_data.sets:
#             new_set = SessionSet(
#                 session_id=session_id,
#                 exercise_id=s.exercise_id,
#                 set_number=s.set_number,
#                 reps=s.reps,
#                 weight=s.weight,
#                 is_completed=s.is_completed
#             )
#             session.add(new_set)
            
#         session.commit()
#         session.refresh(workout_session)
        
#         return SessionRead(id=workout_session.id, status=workout_session.status)
        
#     except Exception as e:
#         session.rollback()
#         raise HTTPException(status_code=500, detail=str(e))