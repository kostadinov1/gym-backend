from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import uuid

from app.db.database import get_session
from app.db.models import WorkoutRoutine, RoutineExercise, Exercise, WorkoutSession, SessionSet, User, WorkoutPlan
from app.schemas.workout import RoutineStart, ExercisePreview, SetTarget, WorkoutRoutineRead
from app.schemas.session import SessionCreate, SessionRead
from app.core.security import get_current_user # <--- Auth

router = APIRouter(prefix="/workouts", tags=["workouts"])

@router.get("/routines", response_model=List[WorkoutRoutineRead])
def get_routines(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # <--- Auth
):
    # Join Routine -> Plan -> User to filter
    statement = (
        select(WorkoutRoutine)
        .join(WorkoutPlan)
        .where(WorkoutPlan.user_id == current_user.id)
        .where(WorkoutPlan.is_active == True)
    )
    routines = session.exec(statement).all()
    
    response = []
    for r in routines:
        last_session = session.exec(
            select(WorkoutSession)
            .where(WorkoutSession.routine_id == r.id)
            .where(WorkoutSession.user_id == current_user.id) # <--- Filter History
            .where(WorkoutSession.status == "completed")
            .order_by(WorkoutSession.end_time.desc())
            .limit(1)
        ).first()
        
        response.append(WorkoutRoutineRead(
            id=r.id,
            name=r.name,
            day_of_week=r.day_of_week,
            last_completed_at=last_session.end_time if last_session else None
        ))
        
    return response

@router.get("/start/{routine_id}", response_model=RoutineStart)
def start_workout_session(
    routine_id: uuid.UUID, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership via Plan
    routine = session.exec(
        select(WorkoutRoutine)
        .join(WorkoutPlan)
        .where(WorkoutRoutine.id == routine_id)
        .where(WorkoutPlan.user_id == current_user.id)
    ).first()
    
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")
        
    routine_exercises = session.exec(
        select(RoutineExercise)
        .where(RoutineExercise.routine_id == routine_id)
        .order_by(RoutineExercise.order_index)
    ).all()
    
    response_exercises = []
    for rx in routine_exercises:
        exercise_def = session.get(Exercise, rx.exercise_id)
        
        sets_list = []
        for i in range(1, rx.target_sets + 1):
            sets_list.append(SetTarget(
                set_number=i,
                target_reps=rx.target_reps,
                target_weight=rx.target_weight
            ))
            
        response_exercises.append(ExercisePreview(
            exercise_id=rx.exercise_id,
            name=exercise_def.name if exercise_def else "Unknown",
            sets=sets_list,
            increment_value=rx.increment_value
        ))
        
    return RoutineStart(
        routine_id=routine.id,
        name=routine.name,
        exercises=response_exercises
    )

@router.post("/finish", response_model=SessionRead)
def finish_workout(
    session_data: SessionCreate, 
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # <--- Auth
):
    workout_session = WorkoutSession(
        routine_id=session_data.routine_id,
        start_time=session_data.start_time,
        end_time=session_data.end_time,
        status="completed",
        user_id=current_user.id # <--- Assign Owner
    )
    db.add(workout_session)
    db.commit()
    db.refresh(workout_session)
    
    for s in session_data.sets:
        db_set = SessionSet(
            session_id=workout_session.id,
            exercise_id=s.exercise_id,
            set_number=s.set_number,
            reps=s.reps,
            weight=s.weight,
            is_completed=s.is_completed
        )
        db.add(db_set)
    
    db.commit()
    
    return SessionRead(id=workout_session.id, status="completed")