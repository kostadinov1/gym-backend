from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import uuid
from pydantic import BaseModel

from app.db.database import get_session
from app.db.models import WorkoutRoutine, RoutineExercise, Exercise

router = APIRouter(prefix="/workouts", tags=["workouts"])

# --- Response Models ---
class SetTarget(BaseModel):
    set_number: int
    target_reps: int
    target_weight: float

class ExercisePreview(BaseModel):
    exercise_id: uuid.UUID
    name: str
    sets: List[SetTarget]
    increment_value: float

class RoutineStart(BaseModel):
    routine_id: uuid.UUID
    name: str
    exercises: List[ExercisePreview]

# --- Endpoints ---

@router.get("/routines", response_model=List[WorkoutRoutine])
def get_routines(session: Session = Depends(get_session)):
    # Returns all available routines (e.g., Pull A, Pull B)
    return session.exec(select(WorkoutRoutine)).all()

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