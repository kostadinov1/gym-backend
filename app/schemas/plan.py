from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# --- PLAN SCHEMAS ---
class PlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: datetime 
    duration_weeks: int 

class PlanRead(PlanCreate):
    id: uuid.UUID
    is_active: bool
    end_date: datetime

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

# --- ROUTINE SCHEMAS ---
class RoutineCreate(BaseModel):
    name: str
    day_of_week: Optional[int] = None 
    routine_type: str = "workout" # <--- ADD THIS (Default to workout)

class RoutineRead(RoutineCreate):
    id: uuid.UUID
    plan_id: uuid.UUID

# --- EXERCISE TARGET SCHEMAS ---
class RoutineExerciseCreate(BaseModel):
    exercise_id: uuid.UUID
    order_index: int
    target_sets: int
    target_reps: int
    target_weight: float
    rest_seconds: int = 90
    increment_value: float

# NEW: This is the specific schema that includes the NAME
class RoutineExerciseRead(RoutineExerciseCreate):
    id: uuid.UUID
    name: str