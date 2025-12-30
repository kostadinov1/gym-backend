from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import uuid

# --- PLAN SCHEMAS ---
class PlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: datetime 
    duration_weeks: int # 1 to 52

class PlanRead(PlanCreate):
    id: uuid.UUID
    is_active: bool
    end_date: datetime

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

# --- ROUTINE SCHEMAS (For creation within a plan) ---
class RoutineCreate(BaseModel):
    name: str
    day_of_week: Optional[int] = None # 0=Mon, 6=Sun

class RoutineRead(RoutineCreate):
    id: uuid.UUID
    plan_id: uuid.UUID

# --- ROUTINE EXERCISE SCHEMAS ---
class RoutineExerciseCreate(BaseModel):
    exercise_id: uuid.UUID
    order_index: int
    target_sets: int
    target_reps: int
    target_weight: float
    rest_seconds: int = 90
    increment_value: float