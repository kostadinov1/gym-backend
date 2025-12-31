from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, or_
from typing import List
import uuid

from app.db.database import get_session
from app.db.models import Exercise, User
from app.schemas.exercise import ExerciseCreate, ExerciseRead, ExerciseUpdate
from app.core.security import get_current_user # Import the Gatekeeper

router = APIRouter(prefix="/exercises", tags=["exercises"])

@router.post("/", response_model=ExerciseRead)
def create_exercise(
    exercise: ExerciseCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # <--- Require Login
):
    # Create with user_id
    db_exercise = Exercise.model_validate(exercise)
    db_exercise.user_id = current_user.id # <--- Assign Owner
    db_exercise.is_custom = True
    
    session.add(db_exercise)
    session.commit()
    session.refresh(db_exercise)
    return db_exercise

@router.get("/", response_model=List[ExerciseRead])
def read_exercises(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Logic: Show System Exercises OR My Custom Exercises
    statement = select(Exercise).where(
        or_(
            Exercise.user_id == None,       # System
            Exercise.user_id == current_user.id # Mine
        )
    )
    return session.exec(statement).all()

@router.delete("/{exercise_id}")
def delete_exercise(
    exercise_id: uuid.UUID, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    exercise = session.get(Exercise, exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
        
    # Strict check: Must belong to user
    if exercise.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this exercise")
        
    session.delete(exercise)
    session.commit()
    return {"ok": True}

@router.patch("/{exercise_id}", response_model=ExerciseRead)
def update_exercise(
    exercise_id: uuid.UUID, 
    exercise_update: ExerciseUpdate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    db_exercise = session.get(Exercise, exercise_id)
    if not db_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    if db_exercise.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to edit this exercise")

    exercise_data = exercise_update.model_dump(exclude_unset=True)
    for key, value in exercise_data.items():
        setattr(db_exercise, key, value)
        
    session.add(db_exercise)
    session.commit()
    session.refresh(db_exercise)
    return db_exercise