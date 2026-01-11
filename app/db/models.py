from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
import uuid
from pydantic import EmailStr 

# --- 0. USERS (New) ---
class User(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)



# --- 1. CORE EXERCISE LIBRARY ---
    
class ExerciseBase(SQLModel):
    name: str = Field(index=True)
    default_increment: float = Field(default=0.0) # Change default to 0.0 or remove requirement
    unit: str = "kg"

  

class Exercise(ExerciseBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    is_custom: bool = True
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id") 

    
    # Relationships
    routine_exercises: List["RoutineExercise"] = Relationship(back_populates="exercise")
    session_sets: List["SessionSet"] = Relationship(back_populates="exercise")

# --- 2. THE PLAN (Macro Cycle) ---
class WorkoutPlan(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: Optional[str] = None
    user_id: uuid.UUID = Field(foreign_key="user.id") # Plans MUST have an owner

    
    # These 3 lines are CRITICAL for the new seed to work
    duration_weeks: int = 4
    start_date: datetime 
    end_date: datetime 
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    routines: List["WorkoutRoutine"] = Relationship(back_populates="plan")

# --- 3. THE ROUTINE (The Daily Template) ---
class WorkoutRoutine(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    plan_id: uuid.UUID = Field(foreign_key="workoutplan.id")
    name: str # e.g., "Pull Day A"
    
    # Scheduling Logic
    # 0=Monday, 6=Sunday. If null, it's floating.
    day_of_week: Optional[int] = None 
        # NEW FIELD
    routine_type: str = Field(default="workout") # Values: 'workout', 'rest'
    
    plan: WorkoutPlan = Relationship(back_populates="routines")
    exercises: List["RoutineExercise"] = Relationship(back_populates="routine")
    sessions: List["WorkoutSession"] = Relationship(back_populates="routine")

# --- 4. EXERCISE CONFIGURATION (The specific targets) ---
class RoutineExercise(SQLModel, table=True):
    """
    Links an Exercise to a Routine with specific goals.
    Allows 'Deadlift' to be heavy on Mon and light on Fri.
    """
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    routine_id: uuid.UUID = Field(foreign_key="workoutroutine.id")
    exercise_id: uuid.UUID = Field(foreign_key="exercise.id")
    
    order_index: int # 1, 2, 3...
    
    # Targets for Week 1
    target_sets: int
    target_reps: int
    target_weight: float # Starting weight
    rest_seconds: int = 90
    
    # Custom Increment for this specific routine
    increment_value: float 
    
    routine: WorkoutRoutine = Relationship(back_populates="exercises")
    exercise: Exercise = Relationship(back_populates="routine_exercises")

# --- 5. LOGGING: SESSIONS ---
class WorkoutSession(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    routine_id: uuid.UUID = Field(foreign_key="workoutroutine.id")
    
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = "in_progress" # in_progress, completed, skipped
    
    routine: WorkoutRoutine = Relationship(back_populates="sessions")
    sets: List["SessionSet"] = Relationship(back_populates="session")
    user_id: uuid.UUID = Field(foreign_key="user.id") # Sessions MUST have an owner

# --- 6. LOGGING: SETS ---
class SessionSet(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="workoutsession.id")
    exercise_id: uuid.UUID = Field(foreign_key="exercise.id")
    
    set_number: int
    reps: int
    weight: float
    is_completed: bool = False
    
    session: WorkoutSession = Relationship(back_populates="sets")
    exercise: Exercise = Relationship(back_populates="session_sets")