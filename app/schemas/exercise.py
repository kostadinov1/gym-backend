from sqlmodel import SQLModel
from typing import Optional
import uuid

class ExerciseCreate(SQLModel):
    name: str
    default_increment: float = 2.5
    unit: str = "kg"

class ExerciseRead(ExerciseCreate):
    id: uuid.UUID
    is_custom: bool = True

class ExerciseUpdate(SQLModel):
    name: Optional[str] = None
    default_increment: Optional[float] = None
    unit: Optional[str] = None