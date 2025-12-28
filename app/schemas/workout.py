from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# --- Existing Classes ---
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

# --- NEW CLASS (Add this) ---
class WorkoutRoutineRead(BaseModel):
    id: uuid.UUID
    name: str
    day_of_week: Optional[int] = None
    last_completed_at: Optional[datetime] = None