from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.db.database import get_session
from app.db.models import Exercise
# Importing from your new schemas folder
from app.schemas.exercise import ExerciseCreate, ExerciseRead

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