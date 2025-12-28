from pydantic import BaseModel
from typing import List
import uuid

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