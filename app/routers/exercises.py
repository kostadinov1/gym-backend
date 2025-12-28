import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.db.database import get_session
from app.db.models import Exercise
# Importing from your new schemas folder
from app.schemas.exercise import ExerciseCreate, ExerciseRead
from fastapi import HTTPException
from app.schemas.exercise import ExerciseUpdate # Import the new schema


router = APIRouter(prefix="/exercises", tags=["exercises"])

@router.post("/", response_model=ExerciseRead)
def create_exercise(exercise: ExerciseCreate, session: Session = Depends(get_session)):
    db_exercise = Exercise.model_validate(exercise)
    session.add(db_exercise)
    session.commit()
    session.refresh(db_exercise)
    return db_exercise

@router.get("/", response_model=List[ExerciseRead])
def read_exercises(session: Session = Depends(get_session)):
    exercises = session.exec(select(Exercise)).all()
    return exercises


@router.delete("/{exercise_id}")
def delete_exercise(exercise_id: uuid.UUID, session: Session = Depends(get_session)):
    exercise = session.get(Exercise, exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
        
    # Protection: Don't allow deleting System exercises
    if not exercise.is_custom:
        raise HTTPException(status_code=400, detail="Cannot delete system exercises")
        
    session.delete(exercise)
    session.commit()
    return {"ok": True}



@router.patch("/{exercise_id}", response_model=ExerciseRead)
def update_exercise(
    exercise_id: uuid.UUID, 
    exercise_update: ExerciseUpdate, 
    session: Session = Depends(get_session)
):
    db_exercise = session.get(Exercise, exercise_id)
    if not db_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # Validation: Only allow editing custom exercises (to protect system defaults)
    if not db_exercise.is_custom:
         raise HTTPException(status_code=400, detail="Cannot edit system exercises")

    # Update only provided fields
    exercise_data = exercise_update.model_dump(exclude_unset=True)
    for key, value in exercise_data.items():
        setattr(db_exercise, key, value)
        
    session.add(db_exercise)
    session.commit()
    session.refresh(db_exercise)
    return db_exercise