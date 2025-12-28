from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import uuid
from pydantic import BaseModel

from app.db.database import get_session
from app.db.models import WorkoutRoutine, RoutineExercise, Exercise
from app.schemas.workout import RoutineStart, ExercisePreview, SetTarget, WorkoutRoutineRead # Import the new Read model

from app.db.models import WorkoutSession, SessionSet
from app.schemas.session import SessionCreate, SessionRead

router = APIRouter(prefix="/workouts", tags=["workouts"])

@router.get("/routines", response_model=List[WorkoutRoutineRead])
def get_routines(session: Session = Depends(get_session)):
    routines = session.exec(select(WorkoutRoutine)).all()
    
    response = []
    for r in routines:
        # Find the latest completed session for this routine
        last_session = session.exec(
            select(WorkoutSession)
            .where(WorkoutSession.routine_id == r.id)
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
def start_workout_session(routine_id: uuid.UUID, session: Session = Depends(get_session)):
    """
    Logic:
    1. Fetch the routine configuration.
    2. Check history (TODO: Future step).
    3. Return the targets for today.
    """
    routine = session.get(WorkoutRoutine, routine_id)
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")
        
    # Get exercises sorted by order
    statement = select(RoutineExercise).where(RoutineExercise.routine_id == routine_id).order_by(RoutineExercise.order_index)
    routine_exercises = session.exec(statement).all()
    
    response_exercises = []
    
    for rx in routine_exercises:
        # Fetch the actual name (optimization: join query is better, but this is easier to read)
        exercise_def = session.get(Exercise, rx.exercise_id)
        
        # Build the sets
        # Logic: In V1, we just repeat the target_sets. 
        # In V2, we will calculate based on history.
        sets_list = []
        for i in range(1, rx.target_sets + 1):
            sets_list.append(SetTarget(
                set_number=i,
                target_reps=rx.target_reps,
                target_weight=rx.target_weight
            ))
            
        response_exercises.append(ExercisePreview(
            exercise_id=rx.exercise_id,
            name=exercise_def.name,
            sets=sets_list,
            increment_value=rx.increment_value
        ))
        
    return RoutineStart(
        routine_id=routine.id,
        name=routine.name,
        exercises=response_exercises
    )

@router.post("/finish", response_model=SessionRead)
def finish_workout(session_data: SessionCreate, db: Session = Depends(get_session)):
    """
    Saves a completed workout session and all its sets.
    """
    # 1. Create the Session Record
    workout_session = WorkoutSession(
        routine_id=session_data.routine_id,
        start_time=session_data.start_time,
        end_time=session_data.end_time,
        status="completed"
    )
    db.add(workout_session)
    db.commit()
    db.refresh(workout_session)
    
    # 2. Create the Set Records
    for s in session_data.sets:
        # Only save completed sets? Or all sets? 
        # Usually we save all, but mark uncompleted ones as such.
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