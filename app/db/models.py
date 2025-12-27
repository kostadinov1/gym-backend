from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
import uuid

# --- EXERCISES ---
class ExerciseBase(SQLModel):
    name: str = Field(index=True)
    default_increment: float = 2.5  # e.g., Add 2.5kg next time
    unit: str = "kg"

class Exercise(ExerciseBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    # Relationship to sets omitted for brevity initially

# --- WORKOUT SESSIONS ---
class WorkoutSessionBase(SQLModel):
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    note: Optional[str] = None

class WorkoutSession(WorkoutSessionBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Relationships
    sets: List["WorkoutSet"] = Relationship(back_populates="session")

# --- SETS (The detailed log) ---
class WorkoutSetBase(SQLModel):
    set_order: int # 1, 2, 3, 4
    reps: int
    weight: float
    rpe: Optional[int] = None # Rate of Perceived Exertion (1-10)
    
class WorkoutSet(WorkoutSetBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Foreign Keys
    session_id: uuid.UUID = Field(foreign_key="workoutsession.id")
    exercise_id: uuid.UUID = Field(foreign_key="exercise.id")
    
    # Relationships
    session: WorkoutSession = Relationship(back_populates="sets")